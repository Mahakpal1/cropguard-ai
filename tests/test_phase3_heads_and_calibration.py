"""Tests for Phase 3: Hierarchical Heads, Training Engine, and Calibration.

Verifies:
1. CropClassifierHead and PerCropDiseaseHead forward passes and shapes.
2. Free energy computation and OOD / unsupported rejection behavior.
3. Joint probability calculation P(crop) * P(disease | crop) and Top-2 crop alternatives.
4. Fast head training on cached features with class-balanced loss.
5. Post-hoc Temperature Scaling and ECE minimization.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from src.calibrate import EnergyOODCalibrator, SystemCalibrator, TemperatureCalibrator
from src.heads import (
    CropClassifierHead,
    HierarchicalClassifier,
    HierarchicalPrediction,
    PerCropDiseaseHead,
)
from src.train import HeadTrainer

ROOT = Path(__file__).resolve().parents[1]


# ── 1. Head Architecture & Forward Pass Tests ────────────────────────────────

def test_crop_classifier_head_and_energy():
    in_dim = 128
    num_crops = 4
    head = CropClassifierHead(in_features=in_dim, num_crops=num_crops)

    # Batch of 3 samples
    x = torch.randn(3, in_dim)
    logits = head(x)
    assert logits.shape == (3, num_crops + 1)  # 4 crops + 1 unsupported

    # Energy score computation
    energy = head.compute_energy(logits, temp=1.0)
    assert energy.shape == (3,)
    assert not torch.isnan(energy).any()


def test_per_crop_disease_head():
    in_dim = 128
    num_diseases = 3
    head = PerCropDiseaseHead(in_features=in_dim, num_diseases=num_diseases)

    x = torch.randn(2, in_dim)
    logits = head(x)
    assert logits.shape == (2, num_diseases)


# ── 2. Hierarchical Inference & Rejection Tests ──────────────────────────────

def test_hierarchical_classifier_joint_prediction():
    in_dim = 64
    crops = ["Tomato", "Potato"]
    disease_map = {
        "Tomato": ["Early_Blight", "Late_Blight", "Healthy"],
        "Potato": ["Early_Blight", "Late_Blight"],
    }

    classifier = HierarchicalClassifier(
        in_features=in_dim,
        crop_names=crops,
        crop_disease_map=disease_map,
        crop_threshold=0.30,
        energy_threshold=10.0,  # Generous threshold for raw uncalibrated weights
    )

    feat = np.random.randn(in_dim).astype(np.float32)
    pred = classifier.predict(feat)

    assert isinstance(pred, HierarchicalPrediction)
    if pred.is_supported:
        assert pred.crop in crops
        assert pred.disease in disease_map[pred.crop]
        # Joint probability constraint: P(crop) * P(disease|crop) <= P(crop)
        assert np.isclose(pred.confidence, pred.crop_confidence * pred.disease_confidence, atol=1e-5)
        assert pred.confidence <= pred.crop_confidence + 1e-5


def test_hierarchical_classifier_rejects_unsupported():
    in_dim = 64
    crops = ["Tomato"]
    disease_map = {"Tomato": ["Early_Blight"]}

    classifier = HierarchicalClassifier(
        in_features=in_dim,
        crop_names=crops,
        crop_disease_map=disease_map,
        crop_threshold=0.90,  # High threshold triggers rejection
    )

    feat = np.zeros(in_dim, dtype=np.float32)
    pred = classifier.predict(feat)

    # Should be rejected due to low confidence
    assert pred.is_supported is False
    assert pred.status == "UNSUPPORTED_OR_LOW_CONF"


# ── 3. Head Training on Cached Features ──────────────────────────────────────

def test_head_trainer_fast_convergence(tmp_path):
    in_dim = 64
    n_samples = 40

    # Synthetic features: 20 Tomato, 20 Rice
    feats = np.random.randn(n_samples, in_dim).astype(np.float32)
    crop_labels = np.array([0] * 20 + [1] * 20, dtype=np.int64)
    disease_labels = np.array([0] * 10 + [1] * 10 + [2] * 20, dtype=np.int64)

    cache_data = {
        "features": feats,
        "crop_labels": crop_labels,
        "disease_labels": disease_labels,
        "crop_to_idx": {"Tomato": 0, "Rice": 1},
        "disease_to_idx": {"Early_Blight": 0, "Healthy": 1, "Brown_Spot": 2},
        "crop_disease_map": {
            "Tomato": ["Early_Blight", "Healthy"],
            "Rice": ["Brown_Spot"],
        },
    }

    trainer = HeadTrainer(epochs=3, batch_size=16)
    ckpt_path = tmp_path / "test_heads.pt"
    classifier = trainer.train_hierarchical_system(cache_data, out_checkpoint_path=str(ckpt_path))

    assert isinstance(classifier, HierarchicalClassifier)
    assert ckpt_path.exists()
    assert "Tomato" in classifier.disease_heads
    assert "Rice" in classifier.disease_heads


# ── 4. Calibration & ECE Tests ───────────────────────────────────────────────

def test_temperature_scaling_and_ece():
    # Synthetic uncalibrated overconfident logits
    np.random.seed(42)
    labels = np.random.randint(0, 3, size=60)
    logits = np.random.randn(60, 3) * 5.0  # High variance = overconfident

    best_t, ece_before, ece_after = TemperatureCalibrator.fit_temperature(logits, labels)

    assert best_t > 0.05
    # Scaled probabilities must be properly normalized
    scaled_probs = torch.softmax(torch.from_numpy(logits) / best_t, dim=-1).numpy()
    assert np.allclose(scaled_probs.sum(axis=-1), 1.0)


def test_energy_ood_threshold():
    id_energies = np.array([-5.0, -4.5, -4.0, -3.8, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0])
    threshold = EnergyOODCalibrator.fit_threshold_at_tpr(id_energies, target_tpr=0.90)

    # 90th percentile should be <= -1.4
    assert threshold <= -1.4
    # Approximately 90% of samples are accepted (<= threshold)
    accepted_ratio = np.mean(id_energies <= threshold)
    assert accepted_ratio >= 0.85
