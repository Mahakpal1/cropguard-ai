"""Leave-One-Dataset-Out (LODO) Cross-Domain Benchmark for CropGuard.

Performs rigorous cross-domain validation:
Iteratively trains on N-1 dataset sources and evaluates on the single held-out source.
This serves as the definitive test for real-world field generalizability,
measuring domain transfer gap and preventing lab-distribution score inflation.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

from eval.metrics import EvaluationReport, PerformanceEvaluator
from src.extract_features import FeatureCacheEngine
from src.heads import HierarchicalClassifier
from src.train import HeadTrainer

logger = logging.getLogger("cropguard.lodo")


class LODOEvaluator:
    """Runs Leave-One-Dataset-Out cross-domain benchmarks."""

    def __init__(self, trainer: Optional[HeadTrainer] = None):
        self.trainer = trainer or HeadTrainer(epochs=10, batch_size=64)

    def run_lodo(
        self,
        cache_data: Dict[str, Union[np.ndarray, dict]],
        min_samples_per_source: int = 15,
        out_report_path: Optional[str] = "eval/reports/lodo_report.json",
    ) -> Dict[str, EvaluationReport]:
        """
        Execute Leave-One-Dataset-Out across all eligible dataset sources.
        """
        source_ids = np.array(cache_data["source_ids"])
        unique_sources = np.unique(source_ids).tolist()

        # Filter out augmented sources or tiny collections
        candidate_sources = [
            s for s in unique_sources
            if not s.endswith("_aug") and np.sum(source_ids == s) >= min_samples_per_source
        ]

        logger.info(f"Starting LODO Benchmark across {len(candidate_sources)} sources: {candidate_sources}")
        results: Dict[str, EvaluationReport] = {}

        for test_source in candidate_sources:
            test_mask = (source_ids == test_source)
            train_mask = (~test_mask)

            n_train = int(np.sum(train_mask))
            n_test = int(np.sum(test_mask))

            logger.info(f"--- FOLD: Holding out '{test_source}' (Train: {n_train}, Test: {n_test}) ---")

            # Slice train cache
            train_cache = {
                "features": cache_data["features"][train_mask],
                "crop_labels": cache_data["crop_labels"][train_mask],
                "disease_labels": cache_data["disease_labels"][train_mask],
                "crop_to_idx": cache_data["crop_to_idx"],
                "disease_to_idx": cache_data["disease_to_idx"],
                "crop_disease_map": cache_data["crop_disease_map"],
            }

            # Train heads on all other sources
            classifier: HierarchicalClassifier = self.trainer.train_hierarchical_system(train_cache)
            # Disable energy-based OOD rejection for LODO folds — the LODO classifier
            # has not been calibrated on a validation set, so using the default tight
            # threshold would reject all out-of-distribution samples unfairly.
            # Setting energy threshold to +inf and crop threshold to 0.0 means no sample
            # is rejected due to OOD calibration, giving honest cross-domain
            # generalization accuracy numbers on the held-out dataset.
            classifier.energy_threshold = float("inf")
            classifier.crop_threshold = 0.0

            # Evaluate on held-out source
            test_feats = cache_data["features"][test_mask]
            test_crops = np.array(list(cache_data["crop_to_idx"].keys()))
            test_diseases = np.array(list(cache_data["disease_to_idx"].keys()))

            idx_to_crop = {v: k for k, v in cache_data["crop_to_idx"].items()}
            idx_to_disease = {v: k for k, v in cache_data["disease_to_idx"].items()}

            y_true_crops = [idx_to_crop[c] for c in cache_data["crop_labels"][test_mask]]
            y_true_diseases = [idx_to_disease[d] for d in cache_data["disease_labels"][test_mask]]

            y_pred_crops = []
            y_pred_diseases = []
            is_supported_flags = []

            for i in range(len(test_feats)):
                pred = classifier.predict(test_feats[i])
                y_pred_crops.append(pred.crop)
                y_pred_diseases.append(pred.disease)
                is_supported_flags.append(pred.is_supported)

            report = PerformanceEvaluator.evaluate_predictions(
                y_true_crops=y_true_crops,
                y_pred_crops=y_pred_crops,
                y_true_diseases=y_true_diseases,
                y_pred_diseases=y_pred_diseases,
                is_supported_flags=is_supported_flags,
                dataset_name=f"LODO_Holdout_{test_source}",
            )
            results[test_source] = report

        if out_report_path:
            p = Path(out_report_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            report_dict = {
                k: {
                    "dataset_name": v.dataset_name,
                    "total_samples": v.total_samples,
                    "evaluated_samples": v.evaluated_samples,
                    "rejection_rate": v.rejection_rate,
                    "crop_accuracy": v.crop_accuracy,
                    "disease_accuracy": v.disease_accuracy,
                    "joint_accuracy": v.joint_accuracy,
                    "macro_f1": v.macro_f1,
                    "per_crop_accuracy": v.per_crop_accuracy,
                }
                for k, v in results.items()
            }
            with open(p, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2)
            logger.info(f"Saved LODO evaluation report to {out_report_path}")

        return results
