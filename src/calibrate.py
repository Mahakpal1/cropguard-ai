"""Temperature Scaling and Calibration Engine for CropGuard.

Calibrates confidence probabilities using post-hoc Temperature Scaling (Guo et al.)
evaluated preferentially on real-world field validation splits.
Calibrates energy score thresholds for honest out-of-distribution (OOD) rejection.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from scipy.optimize import minimize

from src.heads import HierarchicalClassifier

logger = logging.getLogger("cropguard.calibrate")


class TemperatureCalibrator:
    """Optimizes temperature T > 0 on validation logits using L-BFGS to minimize NLL."""

    @staticmethod
    def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
        """
        Compute Expected Calibration Error (ECE).
        ECE = sum_m (|acc(B_m) - conf(B_m)| * |B_m| / N)
        """
        confidences = np.max(probs, axis=-1)
        predictions = np.argmax(probs, axis=-1)
        accuracies = (predictions == labels).astype(float)

        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n_samples = len(labels)

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            prop_in_bin = np.mean(in_bin)

            if prop_in_bin > 0:
                accuracy_in_bin = np.mean(accuracies[in_bin])
                avg_confidence_in_bin = np.mean(confidences[in_bin])
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

        return float(ece)

    @classmethod
    def fit_temperature(
        cls,
        logits: np.ndarray,
        labels: np.ndarray,
    ) -> Tuple[float, float, float]:
        """
        Fit temperature parameter T to minimize Negative Log Likelihood.
        Returns:
            (best_T, ece_before, ece_after)
        """
        z = torch.from_numpy(logits).float()
        y = torch.from_numpy(labels).long()

        raw_probs = torch.softmax(z, dim=-1).numpy()
        ece_before = cls.compute_ece(raw_probs, labels)

        def nll_objective(t_arr):
            t_val = float(t_arr[0])
            scaled = z / t_val
            loss = nn.CrossEntropyLoss()(scaled, y).item()
            return loss

        res = minimize(
            nll_objective,
            x0=[1.0],
            bounds=[(0.05, 10.0)],
            method="L-BFGS-B",
        )
        best_t = float(res.x[0])

        scaled_probs = torch.softmax(z / best_t, dim=-1).numpy()
        ece_after = cls.compute_ece(scaled_probs, labels)

        logger.info(f"Fitted Temperature: {best_t:.3f} | ECE Before: {ece_before:.2%} | ECE After: {ece_after:.2%}")
        return best_t, ece_before, ece_after


class EnergyOODCalibrator:
    """Calibrates energy threshold E(x) = -T * logsumexp(logits / T) for OOD / unfamiliar input rejection."""

    @staticmethod
    def fit_threshold_at_tpr(
        id_energies: np.ndarray,
        target_tpr: float = 0.95,
    ) -> float:
        """
        Compute energy threshold such that target_tpr (e.g. 95%) of in-distribution samples are accepted.
        Since lower energy = more familiar / in-distribution, threshold is the target_tpr percentile of ID energies.
        """
        threshold = float(np.percentile(id_energies, target_tpr * 100.0))
        logger.info(f"Calibrated Energy Threshold at TPR {target_tpr:.0%}: {threshold:.3f}")
        return threshold


class SystemCalibrator:
    """Orchestrates calibration across the full HierarchicalClassifier."""

    @staticmethod
    def calibrate(
        classifier: HierarchicalClassifier,
        val_cache_data: Dict[str, Union[np.ndarray, dict]],
        target_tpr: float = 0.95,
    ) -> HierarchicalClassifier:
        """
        Calibrate crop head, disease heads, and energy threshold using validation data.
        Prefers field validation samples (is_lab == False) when available.
        """
        classifier.eval()
        device = next(classifier.parameters()).device
        feats = val_cache_data["features"]
        crop_labels = val_cache_data["crop_labels"]
        disease_labels = val_cache_data["disease_labels"]
        is_lab = val_cache_data.get("is_lab", np.zeros(len(feats), dtype=bool))

        # 1. Prioritize field samples if sufficient
        field_mask = (~is_lab)
        if field_mask.sum() >= 20:
            eval_feats = feats[field_mask]
            eval_crop_labels = crop_labels[field_mask]
            eval_disease_labels = disease_labels[field_mask]
        else:
            eval_feats = feats
            eval_crop_labels = crop_labels
            eval_disease_labels = disease_labels

        # 2. Calibrate Crop Head Temperature
        with torch.no_grad():
            x_t = torch.from_numpy(eval_feats).float().to(device)
            raw_crop_logits = classifier.crop_head.net(x_t).cpu().numpy()

        best_t_crop, ece_b, ece_a = TemperatureCalibrator.fit_temperature(
            raw_crop_logits, eval_crop_labels
        )
        classifier.crop_head.temperature.data.fill_(best_t_crop)

        # 3. Calibrate Energy Threshold on Crop Head
        with torch.no_grad():
            crop_logits_scaled = classifier.crop_head(x_t)
            energies = classifier.crop_head.compute_energy(crop_logits_scaled).cpu().numpy()

        energy_thresh = EnergyOODCalibrator.fit_threshold_at_tpr(energies, target_tpr=target_tpr)
        classifier.energy_threshold = energy_thresh

        # 4. Calibrate Per-Crop Disease Heads
        crop_to_idx = val_cache_data["crop_to_idx"]
        disease_to_idx = val_cache_data["disease_to_idx"]
        crop_disease_map = val_cache_data["crop_disease_map"]
        disease_labels = val_cache_data["disease_labels"]

        for crop_name, head in classifier.disease_heads.items():
            if crop_name not in crop_to_idx:
                continue
            c_idx = crop_to_idx[crop_name]
            mask = (eval_crop_labels == c_idx)
            sub_feats = eval_feats[mask]
            if len(sub_feats) < 10 or head.num_diseases <= 1:
                continue

            crop_diseases = crop_disease_map.get(crop_name, [])
            dis_to_local = {d: i for i, d in enumerate(crop_diseases)}
            sub_dis_global = eval_disease_labels[mask]
            sub_dis_local = np.array([
                dis_to_local.get(
                    [k for k, v in disease_to_idx.items() if v == g][0], 0
                )
                for g in sub_dis_global
            ], dtype=np.int64)

            with torch.no_grad():
                sub_x = torch.from_numpy(sub_feats).float().to(device)
                raw_dis_logits = head.net(sub_x).cpu().numpy()

            best_t_dis, _, _ = TemperatureCalibrator.fit_temperature(raw_dis_logits, sub_dis_local)
            head.temperature.data.fill_(best_t_dis)

        return classifier
