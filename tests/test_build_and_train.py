"""Tests for CropGuard End-to-End Build and Training Engine (src/build_and_train.py).

Verifies:
1. PipelineBuilder initialization and taxonomy loading.
2. Dataset scanning, pHash deduplication grouping, and honest leaf-group splitting.
3. Feature caching, hierarchical head training, temperature scaling, and energy calibration.
4. Export of deployable bundle (hierarchical_heads.pt, model_config.json, classes_hierarchy.json).
5. Loading checkpoint into CropGuardInferenceEngine and executing end-to-end diagnosis.
6. Backend Classifier loading DINOv2 hierarchical checkpoint with simulated=False.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from src.build_and_train import PipelineBuilder
from src.extract_features import FeatureCacheEngine
from src.heads import HierarchicalClassifier
from src.infer import CropGuardInferenceEngine


@pytest.fixture
def temp_workspace(tmp_path):
    """Setup temporary dirs for data, cache, and output models."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    output_dir = tmp_path / "output_model"
    output_dir.mkdir()

    # Create dummy images in two class folders
    c1 = data_dir / "Tomato_healthy"
    c1.mkdir()
    c2 = data_dir / "Tomato_Early_blight"
    c2.mkdir()
    c3 = data_dir / "Potato___Early_blight"
    c3.mkdir()

    for i in range(4):
        # Greenish image
        img = Image.new("RGB", (64, 64), (30 + i * 5, 140, 30))
        img.save(c1 / f"leaf_{i}.jpg")
        # Brown-spotted image
        img2 = Image.new("RGB", (64, 64), (120 + i * 5, 80, 20))
        img2.save(c2 / f"leaf_{i}.jpg")
        # Potato leaf
        img3 = Image.new("RGB", (64, 64), (40 + i * 5, 120, 40))
        img3.save(c3 / f"leaf_{i}.jpg")

    return {
        "data_dir": data_dir,
        "cache_dir": cache_dir,
        "output_dir": output_dir,
        "taxonomy": os.path.join(PROJ_ROOT, "data", "taxonomy.csv"),
    }


def test_builder_initialization(temp_workspace):
    builder = PipelineBuilder(
        taxonomy_path=temp_workspace["taxonomy"],
        model_name="dinov2_vits14",
        cache_dir=str(temp_workspace["cache_dir"]),
        output_dir=str(temp_workspace["output_dir"]),
        device="cpu",
    )
    assert builder.registry is not None
    assert len(builder.registry.crops) > 0
    assert builder.extractor.feature_dim == 384


def test_scan_and_honest_split(temp_workspace):
    builder = PipelineBuilder(
        taxonomy_path=temp_workspace["taxonomy"],
        model_name="dinov2_vits14",
        cache_dir=str(temp_workspace["cache_dir"]),
        output_dir=str(temp_workspace["output_dir"]),
        device="cpu",
    )

    train_df, val_df, test_df = builder.scan_and_prepare_dataset(
        data_roots=[temp_workspace["data_dir"]],
        max_samples_per_class=4,
        cap_lab_ratio=None,
    )

    total_samples = len(train_df) + len(val_df) + len(test_df)
    assert total_samples == 12, f"Expected 12 images, found {total_samples}"

    # Verify honest grouping: leaf_group_ids in train must not intersect with test
    train_groups = set(train_df["leaf_group_id"].unique())
    test_groups = set(test_df["leaf_group_id"].unique())
    assert len(train_groups.intersection(test_groups)) == 0, "Leakage detected: leaf group in both train and test!"


def test_train_and_calibrate_with_synthetic_cache(temp_workspace):
    """Test train_and_calibrate on synthetic cache dicts (fast unit test without full ViT feature extraction)."""
    builder = PipelineBuilder(
        taxonomy_path=temp_workspace["taxonomy"],
        model_name="dinov2_vits14",
        cache_dir=str(temp_workspace["cache_dir"]),
        output_dir=str(temp_workspace["output_dir"]),
        device="cpu",
    )

    feat_dim = 384
    n_train = 30
    n_val = 15

    # 2 crops: Tomato (classes: Healthy, Early_Blight), Potato (class: Early_Blight)
    crop_names = ["Tomato", "Potato"]
    crop_disease_map = {
        "Tomato": ["Early_Blight", "Healthy"],
        "Potato": ["Early_Blight"],
    }
    crop_to_idx = {"Tomato": 0, "Potato": 1}
    disease_to_idx = {"Early_Blight": 0, "Healthy": 1}

    np.random.seed(42)
    train_feats = np.random.randn(n_train, feat_dim).astype(np.float32)
    train_crops = np.random.choice([0, 1], size=n_train)
    train_dis = np.random.choice([0, 1], size=n_train)

    val_feats = np.random.randn(n_val, feat_dim).astype(np.float32)
    val_crops = np.random.choice([0, 1], size=n_val)
    val_dis = np.random.choice([0, 1], size=n_val)

    train_cache_file = temp_workspace["cache_dir"] / "test_train.npz"
    val_cache_file = temp_workspace["cache_dir"] / "test_val.npz"

    np.savez_compressed(
        train_cache_file,
        features=train_feats,
        crop_labels=train_crops,
        disease_labels=train_dis,
        canonical_keys=["Tomato___Healthy"] * n_train,
        is_lab=np.ones(n_train, dtype=bool),
        source_ids=["pv"] * n_train,
        leaf_group_ids=["grp"] * n_train,
        crop_to_idx_json=json.dumps(crop_to_idx),
        disease_to_idx_json=json.dumps(disease_to_idx),
        crop_disease_map_json=json.dumps(crop_disease_map),
        crop_names_json=json.dumps(crop_names),
        feature_dim=feat_dim,
    )

    np.savez_compressed(
        val_cache_file,
        features=val_feats,
        crop_labels=val_crops,
        disease_labels=val_dis,
        canonical_keys=["Tomato___Healthy"] * n_val,
        is_lab=np.ones(n_val, dtype=bool),
        source_ids=["pv"] * n_val,
        leaf_group_ids=["grp"] * n_val,
        crop_to_idx_json=json.dumps(crop_to_idx),
        disease_to_idx_json=json.dumps(disease_to_idx),
        crop_disease_map_json=json.dumps(crop_disease_map),
        crop_names_json=json.dumps(crop_names),
        feature_dim=feat_dim,
    )

    classifier, ckpt_path = builder.train_and_calibrate(
        train_cache_path=train_cache_file,
        val_cache_path=val_cache_file,
        epochs=3,
        lr=1e-3,
        batch_size=16,
    )

    assert ckpt_path.exists(), "hierarchical_heads.pt checkpoint was not created"
    assert (temp_workspace["output_dir"] / "model_config.json").exists()
    assert (temp_workspace["output_dir"] / "classes_hierarchy.json").exists()

    # Load and check checkpoint content
    ckpt = torch.load(ckpt_path, map_location="cpu")
    assert "model_state" in ckpt
    assert "energy_threshold" in ckpt
    assert "temperature_crop" in ckpt
    assert len(ckpt["crop_names"]) == 2


def _create_mock_checkpoint(output_dir: Path):
    ckpt_path = output_dir / "hierarchical_heads.pt"
    if ckpt_path.exists():
        return ckpt_path
    clf = HierarchicalClassifier(
        in_features=384,
        crop_names=["Tomato", "Potato"],
        crop_disease_map={"Tomato": ["Healthy", "Early_Blight"], "Potato": ["Early_Blight"]},
        energy_threshold=-2.0,
    )
    torch.save({
        "model_state": clf.state_dict(),
        "in_features": 384,
        "crop_names": ["Tomato", "Potato"],
        "crop_disease_map": {"Tomato": ["Healthy", "Early_Blight"], "Potato": ["Early_Blight"]},
        "crop_to_idx": {"Tomato": 0, "Potato": 1},
        "disease_to_idx": {"Early_Blight": 0, "Healthy": 1},
        "energy_threshold": -2.0,
        "temperature_crop": 1.0,
        "temperatures_disease": {"Tomato": 1.0, "Potato": 1.0},
    }, ckpt_path)
    cfg = {
        "name": "cropguard_dinov2_hierarchical",
        "model_type": "dinov2_hierarchical",
        "backbone": "dinov2_vits14",
        "energy_threshold": -2.0,
        "confidence_threshold": 0.60,
    }
    with open(output_dir / "model_config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return ckpt_path


def test_inference_engine_from_checkpoint(temp_workspace):
    """Verify CropGuardInferenceEngine loads the exported checkpoint and diagnoses an image."""
    ckpt_path = _create_mock_checkpoint(temp_workspace["output_dir"])

    engine = CropGuardInferenceEngine.from_checkpoint(
        ckpt_path,
        model_name="dinov2_vits14",
        device="cpu",
    )
    assert engine.classifier is not None
    assert len(engine.classifier.crop_names) == 2

    # Run diagnosis on a green image
    img = Image.new("RGB", (100, 100), (34, 139, 34))
    diag = engine.diagnose(img, explain=False)
    assert diag.crop in ("Tomato", "Potato", "Non-Crop / Background", "Unsupported Crop", "Unsupported / Unknown")
    assert 0.0 <= diag.confidence <= 1.0


def test_backend_classifier_loads_dinov2_model(temp_workspace):
    """Verify backend Classifier loads the DINOv2 bundle without falling back to simulated."""
    from backend.app.services.classifier import Classifier

    _create_mock_checkpoint(temp_workspace["output_dir"])

    classes = [
        {"id": "Tomato_healthy", "crop": {"en": "Tomato", "hi": "टमाटर"}, "disease": {"en": "Healthy", "hi": "स्वस्थ"}},
        {"id": "Tomato_Early_blight", "crop": {"en": "Tomato", "hi": "टमाटर"}, "disease": {"en": "Early Blight", "hi": "अगेती झुलसा"}},
    ]

    clf = Classifier(model_dir=temp_workspace["output_dir"], classes=classes)
    assert clf.simulated is False, "Expected live DINOv2 model, but classifier reported simulated=True"
    assert clf.dinov2_engine is not None

    # Run prediction through classifier
    img = Image.new("RGB", (64, 64), (30, 130, 30))
    res = clf.predict(pil_img=img)
    assert "class_id" in res
    assert "confidence" in res
    assert "crop_confidence" in res
    assert "disease_confidence" in res
