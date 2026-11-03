"""Tests for Phase 2: DINOv2 Feature Extractor, Background Randomization & Feature Caching.

Verifies:
1. Procedural background generation and alpha-feathered compositing.
2. Photometric augmentations (jitter, blur, JPEG compression, cutout).
3. Frozen DINOv2 feature extraction, output dimensions, and L2 normalization.
4. End-to-end feature caching to compressed .npz archive and reload integrity.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from src.augment import BackgroundRandomizer, PhotometricFieldAugmenter
from src.extract_features import DINOv2FeatureExtractor, FeatureCacheEngine

ROOT = Path(__file__).resolve().parents[1]


# ── 1. Augmentation & Background Randomization Tests ─────────────────────────

def test_background_randomizer_composites_leaf():
    randomizer = BackgroundRandomizer()
    h, w = 120, 120

    # Synthetic leaf patch
    leaf_bgr = np.zeros((h, w, 3), dtype=np.uint8)
    leaf_bgr[30:90, 30:90] = [34, 139, 34]  # Green leaf

    leaf_mask = np.zeros((h, w), dtype=np.uint8)
    leaf_mask[30:90, 30:90] = 255

    blended = randomizer.composite(leaf_bgr, leaf_mask, feather_radius=3)

    assert blended.shape == (h, w, 3)
    assert blended.dtype == np.uint8
    # Background outside leaf should no longer be black (0,0,0)
    assert np.mean(blended[5:15, 5:15]) > 10.0


def test_photometric_field_augmenter():
    augmenter = PhotometricFieldAugmenter()
    raw = Image.fromarray(np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8))

    aug = augmenter.augment(raw, p_randomize_bg=0.0)
    assert isinstance(aug, Image.Image)
    assert aug.size == (100, 100)

    # Test JPEG compression helper
    compressed = augmenter.apply_jpeg_compression(raw, quality_range=(40, 50))
    assert compressed.size == (100, 100)

    # Test partial cutout
    arr = np.array(raw)
    cut = augmenter.apply_partial_cutout(arr, num_patches=1, patch_ratio=0.2)
    assert cut.shape == arr.shape


# ── 2. DINOv2 Feature Extractor Tests ────────────────────────────────────────

def test_dinov2_extractor_single_and_batch():
    # Use ViT-S/14 (384-d) for speed
    extractor = DINOv2FeatureExtractor(model_name="dinov2_vits14")
    assert extractor.feature_dim == 384

    # Single image extraction
    dummy_pil = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    feat = extractor.extract_image(dummy_pil)

    assert feat.shape == (384,)
    assert feat.dtype == np.float32
    # Verify L2 normalization
    norm = np.linalg.norm(feat)
    assert np.isclose(norm, 1.0, atol=1e-3), f"Expected unit norm, got {norm}"

    # Batch extraction
    batch = [dummy_pil, dummy_pil]
    batch_feats = extractor.extract_batch(batch, batch_size=2)
    assert batch_feats.shape == (2, 384)


# ── 3. Feature Caching Engine Tests ──────────────────────────────────────────

def test_feature_cache_save_and_load(tmp_path):
    # Create two temporary test images
    img1_path = tmp_path / "leaf1.jpg"
    img2_path = tmp_path / "leaf2.jpg"

    img_data = np.random.randint(30, 200, (100, 100, 3), dtype=np.uint8)
    Image.fromarray(img_data).save(img1_path)
    Image.fromarray(img_data).save(img2_path)

    df = pd.DataFrame([
        {
            "image_path": str(img1_path),
            "canonical_crop": "Tomato",
            "canonical_disease": "Early_Blight",
            "canonical_key": "Tomato___Early_Blight",
            "is_lab": True,
            "source": "plantvillage",
            "leaf_group_id": "grp_001",
        },
        {
            "image_path": str(img2_path),
            "canonical_crop": "Rice",
            "canonical_disease": "Brown_Spot",
            "canonical_key": "Rice___Brown_Spot",
            "is_lab": False,
            "source": "rice_dslr",
            "leaf_group_id": "grp_002",
        },
    ])

    extractor = DINOv2FeatureExtractor(model_name="dinov2_vits14")
    engine = FeatureCacheEngine(extractor=extractor)

    out_npz = tmp_path / "test_features.npz"
    summary = engine.process_and_cache(df, str(out_npz), apply_augmentation=False, batch_size=2)

    assert summary["cached_samples"] == 2
    assert summary["feature_dim"] == 384
    assert out_npz.exists()

    # Load cache back and verify unpacked dictionaries
    loaded = FeatureCacheEngine.load_cache(str(out_npz))
    assert loaded["features"].shape == (2, 384)
    assert len(loaded["crop_labels"]) == 2
    assert "Tomato" in loaded["crop_to_idx"]
    assert "Rice" in loaded["crop_to_idx"]
    assert "Tomato" in loaded["crop_disease_map"]
    assert "Early_Blight" in loaded["crop_disease_map"]["Tomato"]
