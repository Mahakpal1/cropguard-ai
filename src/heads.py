"""Hierarchical Classification Heads for CropGuard.

Implements:
1. CropClassifierHead: Predicts P(crop) over supported crops + "unsupported/not-a-leaf".
2. PerCropDiseaseHead: Predicts P(disease | crop) for a specific crop (including "healthy").
3. HierarchicalClassifier: Orchestrates joint inference:
   P(diagnosis) = P(crop) * P(disease | crop), with energy-based OOD rejection and top-2 routing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class HierarchicalPrediction:
    """Structured output of the two-stage hierarchical model."""
    crop: str
    disease: str
    canonical_key: str
    confidence: float                  # Joint probability P(crop) * P(disease | crop)
    crop_confidence: float             # Marginal probability P(crop)
    disease_confidence: float          # Conditional probability P(disease | crop)
    energy_score: float                # Free energy for OOD / unfamiliar input detection
    is_supported: bool                 # False if unsupported crop / not-a-leaf / rejected
    status: str                        # 'CONFIDENT', 'UNCERTAIN_CROP', 'UNSUPPORTED_OR_LOW_CONF'
    top2_crop: Optional[str] = None    # Second most likely crop if confidence is close
    top2_disease: Optional[str] = None
    top2_confidence: Optional[float] = None


class CropClassifierHead(nn.Module):
    """Predicts crop identity and detects unsupported/non-leaf inputs."""

    def __init__(self, in_features: int = 384, num_crops: int = 15, hidden_dim: int = 256, dropout: float = 0.2):
        super().__init__()
        self.in_features = in_features
        self.num_crops = num_crops
        # Crops index 0 to num_crops-1 are supported crops, last index (num_crops) is "unsupported"
        self.num_classes = num_crops + 1

        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, self.num_classes),
        )
        self.temperature = nn.Parameter(torch.ones(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns scaled logits."""
        logits = self.net(x)
        t = torch.clamp(self.temperature, min=0.1, max=10.0)
        return logits / t

    def compute_energy(self, logits: torch.Tensor, temp: float = 1.0) -> torch.Tensor:
        """
        Free energy E(x) = -T * logsumexp(logits / T).
        Higher energy indicates unfamiliar / out-of-distribution input.
        """
        return -temp * torch.logsumexp(logits / temp, dim=-1)


class PerCropDiseaseHead(nn.Module):
    """Predicts disease condition conditioned on a known crop."""

    def __init__(self, in_features: int = 384, num_diseases: int = 5, hidden_dim: int = 128, dropout: float = 0.15):
        super().__init__()
        self.in_features = in_features
        self.num_diseases = num_diseases

        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_diseases),
        )
        self.temperature = nn.Parameter(torch.ones(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.net(x)
        t = torch.clamp(self.temperature, min=0.1, max=10.0)
        return logits / t


class HierarchicalClassifier(nn.Module):
    """
    Two-stage hierarchical classifier:
    Photo Features -> [Crop Head] -> P(crop)
                   -> [Disease Head for detected crop] -> P(disease | crop)
    Joint = P(crop) * P(disease | crop).
    """

    def __init__(
        self,
        in_features: int = 384,
        crop_names: Optional[List[str]] = None,
        crop_disease_map: Optional[Dict[str, List[str]]] = None,
        crop_threshold: float = 0.45,
        energy_threshold: float = -2.5,
    ):
        super().__init__()
        self.in_features = in_features
        self.crop_names = crop_names or []
        self.crop_threshold = crop_threshold
        self.energy_threshold = energy_threshold

        # Crop Head
        self.crop_head = CropClassifierHead(
            in_features=in_features,
            num_crops=len(self.crop_names),
        )

        # Per-crop Disease Heads
        self.disease_heads = nn.ModuleDict()
        self.crop_disease_map = crop_disease_map or {}
        for crop, diseases in self.crop_disease_map.items():
            self.disease_heads[crop] = PerCropDiseaseHead(
                in_features=in_features,
                num_diseases=len(diseases),
            )

    @torch.no_grad()
    def predict(
        self,
        feature_vector: Union[np.ndarray, torch.Tensor],
        top_k_crops: int = 2,
    ) -> HierarchicalPrediction:
        """
        Execute calibrated hierarchical inference.
        """
        self.eval()
        device = next(self.parameters()).device
        if isinstance(feature_vector, np.ndarray):
            x = torch.from_numpy(feature_vector).float().to(device)
            if x.ndim == 1:
                x = x.unsqueeze(0)
        else:
            x = feature_vector.float().to(device)
            if x.ndim == 1:
                x = x.unsqueeze(0)

        # 1. Evaluate Crop Head
        crop_logits = self.crop_head(x)
        crop_probs = F.softmax(crop_logits, dim=-1).squeeze(0).cpu().numpy()
        energy = float(self.crop_head.compute_energy(crop_logits).item())

        num_crops = len(self.crop_names)
        unsupported_idx = num_crops
        p_unsupported = float(crop_probs[unsupported_idx])

        # Crop probabilities over supported crops
        supported_crop_probs = crop_probs[:num_crops]
        top_crop_indices = np.argsort(supported_crop_probs)[::-1]
        top1_crop_idx = int(top_crop_indices[0])
        top1_crop_prob = float(supported_crop_probs[top1_crop_idx])
        top1_crop_name = self.crop_names[top1_crop_idx]

        # Check OOD or unsupported
        is_rejected = (
            p_unsupported > 0.50
            or top1_crop_prob < self.crop_threshold
            or energy > self.energy_threshold
        )

        if is_rejected:
            return HierarchicalPrediction(
                crop="Unsupported / Unknown",
                disease="Not Supported",
                canonical_key="__unsupported_____not_supported__",
                confidence=float(top1_crop_prob),
                crop_confidence=float(top1_crop_prob),
                disease_confidence=0.0,
                energy_score=energy,
                is_supported=False,
                status="UNSUPPORTED_OR_LOW_CONF",
            )

        # 2. Evaluate Disease Head for Top-1 Crop
        if top1_crop_name not in self.disease_heads:
            return HierarchicalPrediction(
                crop=top1_crop_name,
                disease="Unknown",
                canonical_key=f"{top1_crop_name}___Unknown",
                confidence=float(top1_crop_prob),
                crop_confidence=float(top1_crop_prob),
                disease_confidence=0.0,
                energy_score=energy,
                is_supported=False,
                status="UNSUPPORTED_OR_LOW_CONF",
            )
        disease_head = self.disease_heads[top1_crop_name]

        dis_logits = disease_head(x)
        dis_probs = F.softmax(dis_logits, dim=-1).squeeze(0).cpu().numpy()
        top1_dis_idx = int(np.argmax(dis_probs))
        top1_dis_prob = float(dis_probs[top1_dis_idx])
        disease_list = self.crop_disease_map[top1_crop_name]
        top1_disease_name = disease_list[top1_dis_idx]

        # Joint Probability = P(crop) * P(disease | crop)
        joint_confidence = float(top1_crop_prob * top1_dis_prob)
        canonical_key = f"{top1_crop_name}___{top1_disease_name}"

        # 3. Compute Top-2 Alternative Crop/Disease if relevant
        top2_crop_name = None
        top2_disease_name = None
        top2_joint = None
        status = "CONFIDENT"

        if len(top_crop_indices) > 1:
            top2_crop_idx = int(top_crop_indices[1])
            top2_crop_prob = float(supported_crop_probs[top2_crop_idx])
            top2_crop_name = self.crop_names[top2_crop_idx]

            # If margin between crop 1 and crop 2 is narrow (< 0.20), flag uncertain crop
            if (top1_crop_prob - top2_crop_prob) < 0.20:
                status = "UNCERTAIN_CROP"

            if top2_crop_name in self.disease_heads:
                head2 = self.disease_heads[top2_crop_name]
                dis2_logits = head2(x)
                dis2_probs = F.softmax(dis2_logits, dim=-1).squeeze(0).cpu().numpy()
                idx2 = int(np.argmax(dis2_probs))
                top2_disease_name = self.crop_disease_map[top2_crop_name][idx2]
                top2_joint = float(top2_crop_prob * dis2_probs[idx2])

        return HierarchicalPrediction(
            crop=top1_crop_name,
            disease=top1_disease_name,
            canonical_key=canonical_key,
            confidence=joint_confidence,
            crop_confidence=top1_crop_prob,
            disease_confidence=top1_dis_prob,
            energy_score=energy,
            is_supported=True,
            status=status,
            top2_crop=top2_crop_name,
            top2_disease=top2_disease_name,
            top2_confidence=top2_joint,
        )
