"""Phase 2 feature tests.

Covers:
- Default KB is now knowledge_base/broad (38 entries)
- Calibrated gates: energy_threshold present in active model_config after calibration
- CropID: crop.available is True when ml/models/crop_id/config.json exists
- Training augmentation: RandomShadow module is importable and produces valid output
- Broad KB is fully served via /api/v1/knowledge/<class_id>
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BROAD_KB = ROOT / "knowledge_base" / "broad"
MODEL_CFG = ROOT / "ml" / "models" / "model_config.json"
CROP_ID_DIR = ROOT / "ml" / "models" / "crop_id"


# ── 2.1 Default KB is broad ─────────────────────────────────────────────────

def test_default_kb_is_broad():
    """Settings() should resolve kb_dir to knowledge_base/broad by default (no env override)."""
    import os
    env_before = os.environ.pop("KB_DIR", None)
    try:
        # Re-import to get a fresh default (Settings uses lambda so it re-evaluates each time)
        from backend.app.config import Settings
        s = Settings()
        assert "broad" in str(s.kb_dir), f"Expected broad in default kb_dir, got {s.kb_dir}"
    finally:
        if env_before is not None:
            os.environ["KB_DIR"] = env_before


def test_broad_kb_has_38_entries():
    """The broad KB directory has at least 38 JSON entries (one per cropguard38 class)."""
    entries = list(BROAD_KB.glob("*.json"))
    assert len(entries) >= 38, f"Expected >= 38 JSON files in knowledge_base/broad, got {len(entries)}"


def test_advisory_loads_38_entries_from_broad():
    """Advisory loads all 38 broad KB entries when pointing at knowledge_base/broad."""
    from backend.app.services.advisory import Advisory
    adv = Advisory(BROAD_KB)
    assert len(adv.entries) >= 38, f"Advisory loaded {len(adv.entries)} entries, expected >= 38"


def test_broad_kb_advice_tier_is_draft():
    """A class that has a broad KB entry returns advice_tier 'draft' (not 'none')."""
    from backend.app.services.advisory import Advisory
    adv = Advisory(BROAD_KB)
    tier = adv.tier("Apple___Cedar_apple_rust")
    assert tier == "draft", f"Expected 'draft', got '{tier}'"


# ── 2.2 CropID availability ──────────────────────────────────────────────────

def test_crop_id_available_when_config_exists():
    """CropID.available is True if and only if crop_id/config.json exists."""
    from backend.app.services.crop_id import CropID
    model_dir = ROOT / "ml" / "models"
    crop = CropID(model_dir)
    config_present = (CROP_ID_DIR / "config.json").exists()
    assert crop.available == config_present, (
        f"CropID.available={crop.available} but config_present={config_present}"
    )


@pytest.mark.skipif(not (CROP_ID_DIR / "config.json").exists(), reason="BioCLIP export not yet run")
def test_crop_id_config_has_required_keys():
    """BioCLIP export produces a config.json with all required keys."""
    cfg = json.load(open(CROP_ID_DIR / "config.json", encoding="utf-8"))
    for key in ("onnx", "embeddings", "crops", "mean", "std", "logit_scale", "threshold"):
        assert key in cfg, f"Missing key '{key}' in crop_id/config.json"
    assert len(cfg["crops"]) >= 10, "Expected at least 10 crops in crop_id/config.json"


@pytest.mark.skipif(not (CROP_ID_DIR / "config.json").exists(), reason="BioCLIP export not yet run")
def test_crop_id_onnx_and_embeddings_exist():
    """After BioCLIP export, both ONNX encoder and embeddings .npy file exist."""
    cfg = json.load(open(CROP_ID_DIR / "config.json", encoding="utf-8"))
    assert (CROP_ID_DIR / cfg["onnx"]).exists(), "crop_encoder.onnx not found"
    assert (CROP_ID_DIR / cfg["embeddings"]).exists(), "crop_embeddings.npy not found"


# ── 2.3 Calibrated gates ────────────────────────────────────────────────────

@pytest.mark.skipif(not MODEL_CFG.exists(), reason="model_config.json not found (no real model installed)")
def test_active_model_config_has_energy_threshold():
    """After gate calibration, model_config.json must contain an energy_threshold."""
    cfg = json.load(open(MODEL_CFG, encoding="utf-8"))
    assert "energy_threshold" in cfg, (
        "energy_threshold not in model_config.json — run: "
        "python ml/calibrate_gates.py --id-dir data/disease_dataset/valid --write"
    )
    val = cfg["energy_threshold"]
    assert isinstance(val, (int, float)) and val < 0, (
        f"energy_threshold should be a negative float (log-sum-exp score), got {val}"
    )


@pytest.mark.skipif(not MODEL_CFG.exists(), reason="model_config.json not found")
def test_active_model_has_valid_confidence_threshold():
    """Confidence threshold should be in (0.3, 0.99)."""
    cfg = json.load(open(MODEL_CFG, encoding="utf-8"))
    thr = cfg.get("confidence_threshold", 0.6)
    assert 0.3 <= thr <= 0.99, f"confidence_threshold {thr} is out of expected range [0.3, 0.99]"


# ── 2.6 Training augmentations ───────────────────────────────────────────────

def test_random_shadow_importable_and_works():
    """RandomShadow transform is importable from train_local and produces valid PIL output."""
    import sys
    ml_dir = ROOT / "ml"
    if str(ml_dir) not in sys.path:
        sys.path.insert(0, str(ml_dir))
    from train_local import RandomShadow
    from PIL import Image
    import numpy as np
    shadow = RandomShadow(p=1.0)          # always apply
    img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8) + 100)
    out = shadow(img)
    assert isinstance(out, Image.Image), "RandomShadow must return a PIL Image"
    assert out.size == img.size, "RandomShadow must not change image dimensions"


def test_make_transforms_returns_two_pipelines():
    """make_transforms(224) returns (train_tf, eval_tf), both callable on a PIL image."""
    import sys
    ml_dir = ROOT / "ml"
    if str(ml_dir) not in sys.path:
        sys.path.insert(0, str(ml_dir))
    from train_local import make_transforms
    import numpy as np
    from PIL import Image
    import torch
    tf_train, tf_eval = make_transforms(224)
    img = Image.fromarray(np.random.randint(0, 255, (300, 200, 3), dtype=np.uint8))
    t = tf_train(img)
    assert isinstance(t, torch.Tensor) and t.shape == (3, 224, 224), f"train tf output shape {t.shape}"
    e = tf_eval(img)
    assert isinstance(e, torch.Tensor) and e.shape == (3, 224, 224), f"eval tf output shape {e.shape}"
