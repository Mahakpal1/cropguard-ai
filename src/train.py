"""Laptop-Friendly Training Engine for CropGuard Hierarchical Heads.

Trains CropClassifierHead and PerCropDiseaseHead on pre-extracted cached .npz features.
Runs in seconds on GPU and minutes on CPU using class-balanced CrossEntropyLoss
and AdamW with Cosine Annealing.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.extract_features import FeatureCacheEngine
from src.heads import CropClassifierHead, HierarchicalClassifier, PerCropDiseaseHead

logger = logging.getLogger("cropguard.train")


class HeadTrainer:
    """Trains hierarchical heads on cached features."""

    def __init__(
        self,
        device: Optional[str] = None,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        batch_size: int = 64,
        epochs: int = 25,
    ):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.epochs = epochs

    @staticmethod
    def compute_class_weights(labels: np.ndarray, num_classes: int) -> torch.Tensor:
        """Compute inverse-frequency class weights to balance rare and dominant classes."""
        counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
        total = float(np.sum(counts))
        counts = np.maximum(counts, 1.0)
        weights = total / (num_classes * counts)
        # Normalize weights
        weights = weights / np.mean(weights)
        return torch.from_numpy(weights).float()

    def train_crop_head(
        self,
        features: np.ndarray,
        crop_labels: np.ndarray,
        num_crops: int,
    ) -> CropClassifierHead:
        """Train the CropClassifierHead (classes: 0..num_crops-1, plus index num_crops for unsupported)."""
        head = CropClassifierHead(
            in_features=features.shape[1],
            num_crops=num_crops,
        ).to(self.device)

        weights = self.compute_class_weights(crop_labels, num_crops + 1).to(self.device)
        criterion = nn.CrossEntropyLoss(weight=weights)
        optimizer = torch.optim.AdamW(head.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)

        x_t = torch.from_numpy(features).float()
        y_t = torch.from_numpy(crop_labels).long()
        ds = TensorDataset(x_t, y_t)
        loader = DataLoader(ds, batch_size=self.batch_size, shuffle=True)

        head.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            correct = 0
            total = 0
            for bx, by in loader:
                bx, by = bx.to(self.device), by.to(self.device)
                optimizer.zero_grad()
                logits = head(bx)
                loss = criterion(logits, by)
                loss.backward()
                optimizer.step()

                total_loss += loss.item() * len(by)
                preds = logits.argmax(dim=-1)
                correct += (preds == by).sum().item()
                total += len(by)

            scheduler.step()
            acc = correct / total if total > 0 else 0
            logger.debug(f"[CropHead Epoch {epoch+1}/{self.epochs}] Loss: {total_loss/total:.4f}, Acc: {acc:.2%}")

        return head

    def train_disease_head(
        self,
        features: np.ndarray,
        disease_labels: np.ndarray,
        num_diseases: int,
    ) -> PerCropDiseaseHead:
        """Train disease classifier for a single specific crop."""
        head = PerCropDiseaseHead(
            in_features=features.shape[1],
            num_diseases=num_diseases,
        ).to(self.device)

        if len(features) == 0 or num_diseases <= 1:
            return head

        weights = self.compute_class_weights(disease_labels, num_diseases).to(self.device)
        criterion = nn.CrossEntropyLoss(weight=weights)
        optimizer = torch.optim.AdamW(head.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)

        x_t = torch.from_numpy(features).float()
        y_t = torch.from_numpy(disease_labels).long()
        ds = TensorDataset(x_t, y_t)
        loader = DataLoader(ds, batch_size=min(self.batch_size, len(ds)), shuffle=True)

        head.train()
        for epoch in range(self.epochs):
            for bx, by in loader:
                bx, by = bx.to(self.device), by.to(self.device)
                optimizer.zero_grad()
                logits = head(bx)
                loss = criterion(logits, by)
                loss.backward()
                optimizer.step()
            scheduler.step()

        return head

    def train_hierarchical_system(
        self,
        cache_data: Dict[str, Union[np.ndarray, dict]],
        out_checkpoint_path: Optional[str] = None,
    ) -> HierarchicalClassifier:
        """
        Orchestrate complete training over cached features:
        1. CropClassifierHead over all features
        2. PerCropDiseaseHead for each distinct crop
        """
        feats = cache_data["features"]
        crop_labels = cache_data["crop_labels"]
        disease_labels = cache_data["disease_labels"]
        crop_to_idx = cache_data["crop_to_idx"]
        disease_to_idx = cache_data["disease_to_idx"]
        crop_disease_map = cache_data["crop_disease_map"]

        idx_to_crop = {v: k for k, v in crop_to_idx.items()}
        crops_list = [idx_to_crop[i] for i in range(len(crop_to_idx))]

        logger.info(f"Training Crop Head across {len(crops_list)} crops ({len(feats)} samples)...")
        crop_head = self.train_crop_head(feats, crop_labels, num_crops=len(crops_list))

        disease_heads = nn.ModuleDict()
        for crop_name in crops_list:
            crop_idx = crop_to_idx[crop_name]
            mask = (crop_labels == crop_idx)
            sub_feats = feats[mask]

            crop_diseases = crop_disease_map.get(crop_name, [])
            if len(sub_feats) == 0 or len(crop_diseases) == 0:
                disease_heads[crop_name] = PerCropDiseaseHead(
                    in_features=feats.shape[1],
                    num_diseases=max(1, len(crop_diseases)),
                )
                continue

            # Remap global disease indices to local [0..M_c-1] indices
            sub_dis_global = disease_labels[mask]
            dis_to_local = {d: i for i, d in enumerate(crop_diseases)}
            sub_dis_local = np.array([
                dis_to_local.get(
                    [k for k, v in disease_to_idx.items() if v == g][0], 0
                )
                for g in sub_dis_global
            ], dtype=np.int64)

            logger.info(f"Training Disease Head for {crop_name} ({len(crop_diseases)} classes, {len(sub_feats)} samples)...")
            d_head = self.train_disease_head(sub_feats, sub_dis_local, num_diseases=len(crop_diseases))
            disease_heads[crop_name] = d_head

        # Assemble full hierarchical system
        classifier = HierarchicalClassifier(
            in_features=feats.shape[1],
            crop_names=crops_list,
            crop_disease_map=crop_disease_map,
        )
        classifier.crop_head = crop_head
        classifier.disease_heads = disease_heads

        if out_checkpoint_path:
            p = Path(out_checkpoint_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "model_state": classifier.state_dict(),
                "in_features": feats.shape[1],
                "crop_names": crops_list,
                "crop_disease_map": crop_disease_map,
                "crop_to_idx": crop_to_idx,
                "disease_to_idx": disease_to_idx,
                "energy_threshold": classifier.energy_threshold,
            }, p)
            logger.info(f"Saved trained hierarchical model to {out_checkpoint_path}")

        return classifier
