"""Tests for Layer 4: Laptop-Feasible Training Plan.

Validates:
1. Feature extraction caching with and without augmentation (clean vs augmented slicing).
2. Laptop-feasible CPU head training in seconds.
3. Field-only validation calibration for temperature scaling and energy reject threshold.
4. Native LoRA module: step-0 equivalence, parameter freezing, weight merging, and decision rule.
"""
from __future__ import annotations

import time
import numpy as np
import pytest
import torch
import torch.nn as nn

from src.calibrate import SystemCalibrator, TemperatureCalibrator, EnergyOODCalibrator
from src.extract_features import FeatureCacheEngine
from src.heads import HierarchicalClassifier
from src.lora import LoRALinear, apply_lora_to_dinov2, merge_lora_weights, LoRABenchmarkEngine
from src.train import HeadTrainer


# ---------------------------------------------------------------------------
# 1. Feature Caching Slices (With & Without Augmentation)
# ---------------------------------------------------------------------------
def test_feature_cache_clean_and_augmented_slicing():
    """Verify FeatureCacheEngine correctly partitions and filters clean vs augmented features."""
    n_clean = 40
    n_aug = 30
    total = n_clean + n_aug

    clean_sources = [f"plantvillage_{i}" for i in range(n_clean)]
    aug_sources = [f"plantvillage_{i}_aug" for i in range(n_aug)]
    all_sources = np.array(clean_sources + aug_sources, dtype=object)

    mock_cache = {
        "features": np.random.randn(total, 64).astype(np.float32),
        "crop_labels": np.random.randint(0, 3, size=total),
        "disease_labels": np.random.randint(0, 5, size=total),
        "canonical_keys": np.array([f"crop{i}___dis{i}" for i in range(total)], dtype=object),
        "is_lab": np.array([True] * n_clean + [False] * n_aug, dtype=bool),
        "source_ids": all_sources,
        "leaf_group_ids": np.array([f"g_{i}" for i in range(total)], dtype=object),
        "crop_to_idx": {"Apple": 0, "Corn": 1, "Tomato": 2},
        "disease_to_idx": {"Healthy": 0, "Rust": 1},
        "crop_disease_map": {"Apple": ["Healthy"], "Corn": ["Rust"], "Tomato": ["Healthy"]},
    }

    clean_slice, aug_slice = FeatureCacheEngine.split_clean_and_augmented(mock_cache)
    assert len(clean_slice["features"]) == n_clean
    assert len(aug_slice["features"]) == n_aug
    assert all(not str(s).endswith("_aug") for s in clean_slice["source_ids"])
    assert all(str(s).endswith("_aug") for s in aug_slice["source_ids"])

    # Test filter_cache
    filtered_clean = FeatureCacheEngine.filter_cache(mock_cache, mode="clean")
    assert len(filtered_clean["features"]) == n_clean

    filtered_aug = FeatureCacheEngine.filter_cache(mock_cache, mode="augmented")
    assert len(filtered_aug["features"]) == n_aug

    filtered_both = FeatureCacheEngine.filter_cache(mock_cache, mode="both")
    assert len(filtered_both["features"]) == total


# ---------------------------------------------------------------------------
# 2. Laptop-Feasible CPU Head Training Speed
# ---------------------------------------------------------------------------
def test_head_training_on_cpu_takes_seconds():
    """Verify that training hierarchical heads on cached features runs in seconds on CPU."""
    n_samples = 200
    feat_dim = 128
    features = np.random.randn(n_samples, feat_dim).astype(np.float32)
    # L2 normalize
    features = features / np.linalg.norm(features, axis=-1, keepdims=True)

    crop_to_idx = {"Apple": 0, "Corn": 1, "Tomato": 2}
    disease_to_idx = {"Healthy": 0, "Scab": 1, "Rust": 2}
    crop_disease_map = {
        "Apple": ["Healthy", "Scab"],
        "Corn": ["Healthy", "Rust"],
        "Tomato": ["Healthy"],
    }

    train_data = {
        "features": features,
        "crop_labels": np.random.randint(0, 3, size=n_samples),
        "disease_labels": np.random.randint(0, 3, size=n_samples),
        "crop_to_idx": crop_to_idx,
        "disease_to_idx": disease_to_idx,
        "crop_disease_map": crop_disease_map,
    }

    trainer = HeadTrainer(device="cpu", epochs=2, batch_size=32, lr=1e-3)
    start_time = time.time()
    classifier = trainer.train_hierarchical_system(train_data)
    elapsed = time.time() - start_time

    assert isinstance(classifier, HierarchicalClassifier)
    # Head training on 200 samples for 2 epochs on CPU must be fast (< 5 seconds)
    assert elapsed < 5.0, f"CPU head training took too long: {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# 3. Field-Only Validation Calibration
# ---------------------------------------------------------------------------
def test_field_only_validation_calibration():
    """Verify temperature scaling and energy reject threshold calibrate strictly on field images."""
    n_lab = 50
    n_field = 30
    total = n_lab + n_field
    feat_dim = 64

    # Lab images have zero noise, field images have realistic variation
    feats = np.random.randn(total, feat_dim).astype(np.float32)
    feats = feats / np.linalg.norm(feats, axis=-1, keepdims=True)

    is_lab = np.array([True] * n_lab + [False] * n_field, dtype=bool)
    crop_labels = np.random.randint(0, 2, size=total)
    disease_labels = np.random.randint(0, 2, size=total)

    crop_names = ["Rice", "Sugarcane"]
    crop_disease_map = {"Rice": ["Blast", "Brown_Spot"], "Sugarcane": ["Healthy", "Red_Rot"]}

    classifier = HierarchicalClassifier(
        in_features=feat_dim,
        crop_names=crop_names,
        crop_disease_map=crop_disease_map,
    )

    val_cache = {
        "features": feats,
        "crop_labels": crop_labels,
        "disease_labels": disease_labels,
        "is_lab": is_lab,
        "crop_to_idx": {"Rice": 0, "Sugarcane": 1},
        "disease_to_idx": {"Blast": 0, "Brown_Spot": 1, "Healthy": 0, "Red_Rot": 1},
        "crop_disease_map": crop_disease_map,
    }

    calibrated_classifier = SystemCalibrator.calibrate(
        classifier,
        val_cache,
        target_tpr=0.95,
        field_only=True,
    )

    meta = calibrated_classifier.calibration_metadata
    assert meta["field_only"] is True
    # Exactly n_field samples were used, all n_lab samples excluded
    assert meta["calibrated_samples"] == n_field
    assert meta["crop_temperature"] > 0.0
    assert meta["energy_threshold"] is not None


# ---------------------------------------------------------------------------
# 4. LoRA Native Implementation: Equivalence & Merging
# ---------------------------------------------------------------------------
def test_lora_linear_initialization_and_equivalence():
    """Verify that LoRALinear at step 0 is mathematically identical to the frozen linear layer."""
    linear = nn.Linear(128, 64)
    x = torch.randn(8, 128)

    orig_out = linear(x).detach()

    lora = LoRALinear(linear, rank=8, alpha=16.0, dropout=0.0)
    # Original weights must be frozen
    assert linear.weight.requires_grad is False
    # LoRA parameters must be trainable
    assert lora.lora_A.requires_grad is True
    assert lora.lora_B.requires_grad is True
    # LoRA B initialized to 0
    assert torch.all(lora.lora_B == 0.0)

    # Output at step 0 must match frozen layer
    lora_out = lora(x).detach()
    diff = torch.max(torch.abs(orig_out - lora_out)).item()
    assert diff < 1e-6, f"LoRA at step 0 diverged from frozen linear: max diff = {diff}"


def test_lora_linear_gradient_and_weight_merging():
    """Verify that gradients only update LoRA adapters and merge() folds weights correctly."""
    linear = nn.Linear(64, 32)
    lora = LoRALinear(linear, rank=4, alpha=8.0, dropout=0.0)

    x = torch.randn(4, 64)
    out = lora(x)
    loss = out.sum()
    loss.backward()

    # Original linear weights have no gradient
    assert linear.weight.grad is None
    # LoRA parameters have gradients
    assert lora.lora_A.grad is not None
    assert lora.lora_B.grad is not None

    # Manually modify B to simulate training update
    with torch.no_grad():
        lora.lora_B.data.fill_(0.01)

    # Output before merge
    out_before = lora(x).detach()

    # Merge weights into original linear
    lora.merge()
    assert lora.merged is True

    # Output after merge (must match without computing delta separately)
    out_after = lora(x).detach()
    diff = torch.max(torch.abs(out_before - out_after)).item()
    assert diff < 1e-6, f"Merged output differed from adapted output: diff={diff}"


def test_apply_lora_to_dinov2_mock_transformer():
    """Verify apply_lora_to_dinov2 correctly instruments transformer attention projections."""
    class MockAttention(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.q_proj = nn.Linear(dim, dim)
            self.k_proj = nn.Linear(dim, dim)
            self.v_proj = nn.Linear(dim, dim)
            self.o_proj = nn.Linear(dim, dim)

    class MockBlock(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.attention = MockAttention(dim)

    class MockEncoder(nn.Module):
        def __init__(self, num_blocks=4, dim=64):
            super().__init__()
            self.layer = nn.ModuleList([MockBlock(dim) for _ in range(num_blocks)])

    class MockViT(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = MockEncoder(num_blocks=4, dim=64)

    vit = MockViT()
    # Apply LoRA to last 2 blocks only
    instrumented_vit, lora_params = apply_lora_to_dinov2(
        vit,
        last_n_blocks=2,
        rank=4,
        alpha=8.0,
        target_modules=("q_proj", "v_proj"),
    )

    # First 2 blocks unchanged (standard Linear)
    assert isinstance(vit.encoder.layer[0].attention.q_proj, nn.Linear)
    assert not isinstance(vit.encoder.layer[0].attention.q_proj, LoRALinear)

    # Last 2 blocks wrapped in LoRALinear
    assert isinstance(vit.encoder.layer[2].attention.q_proj, LoRALinear)
    assert isinstance(vit.encoder.layer[2].attention.v_proj, LoRALinear)
    assert isinstance(vit.encoder.layer[3].attention.q_proj, LoRALinear)
    assert isinstance(vit.encoder.layer[3].attention.v_proj, LoRALinear)

    # Total LoRA params: 2 blocks * 2 projections * (A + B) = 8 parameters
    assert len(lora_params) == 8


# ---------------------------------------------------------------------------
# 5. LoRA Decision Rule: Keep ONLY if LODO Scores Improve
# ---------------------------------------------------------------------------
def test_lora_decision_rule():
    """Verify decision rule strictly rejects LoRA when LODO scores do not improve over frozen baseline."""
    # Case 1: Inconclusive / equal score -> Reject
    frozen_score = 0.9522
    lora_score_inconclusive = 0.9525
    decision_reject = LoRABenchmarkEngine.evaluate_decision_rule(
        frozen_score, lora_score_inconclusive, min_delta=0.005
    )
    assert decision_reject["accepted"] is False
    assert "REJECTED" in decision_reject["verdict"]

    # Case 2: Meaningful cross-domain lift >= +0.5% -> Accept
    lora_score_lift = 0.9600
    decision_accept = LoRABenchmarkEngine.evaluate_decision_rule(
        frozen_score, lora_score_lift, min_delta=0.005
    )
    assert decision_accept["accepted"] is True
    assert decision_accept["verdict"] == "ACCEPTED"
