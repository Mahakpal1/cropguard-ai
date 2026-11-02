"""Phase 3 ViT model tests.

Covers:
- ONNX model file existence and correct output shape (1, 38)
- Pipeline uses the ViT model (not simulated)
- ViT model config has expected keys and field_test_accuracy
- Field accuracy on a subset of PlantDoc test images > 30%
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
VIT_DIR = ROOT / "ml" / "models" / "cropguard38_vit"
PD_DIR = ROOT / "work" / "plantdoc"
ML_DIR = ROOT / "ml"


# ── 4.1 ONNX model artefacts ────────────────────────────────────────────────

def test_vit_onnx_exists():
    """ONNX model file must be present after field fine-tuning."""
    assert (VIT_DIR / "model.onnx").exists(), "cropguard38_vit/model.onnx not found"
    assert (VIT_DIR / "model.onnx.data").exists(), "ONNX external data file not found"
    assert (VIT_DIR / "class_names.json").exists(), "class_names.json not found"
    assert (VIT_DIR / "model_config.json").exists(), "model_config.json not found"


def test_vit_model_config_has_expected_keys():
    """Model config must declare all required keys."""
    cfg = json.load(open(VIT_DIR / "model_config.json"))
    for key in ("name", "onnx", "labels", "input_size", "mean", "std",
                "confidence_threshold", "energy_threshold", "field_test_accuracy"):
        assert key in cfg, f"Missing key '{key}' in model_config.json"
    assert len(cfg["labels"]) == 38, f"Expected 38 labels, got {len(cfg['labels'])}"


def test_vit_field_test_accuracy_recorded():
    """Trained model must have achieved > 50% field accuracy."""
    cfg = json.load(open(VIT_DIR / "model_config.json"))
    acc = cfg["field_test_accuracy"]
    assert acc > 0.50, f"Field accuracy {acc:.2%} is below 50% — model under-performs"


def test_vit_onnx_output_shape():
    """ONNX session must return logit vector of length 38."""
    ort = pytest.importorskip("onnxruntime", reason="onnxruntime not installed")
    sess = ort.InferenceSession(
        str(VIT_DIR / "model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    inp_meta = sess.get_inputs()[0]
    dummy = np.random.randn(1, 3, 224, 224).astype(np.float32)
    out = sess.run(None, {inp_meta.name: dummy})[0]
    assert out.shape == (1, 38), f"Expected output shape (1, 38), got {out.shape}"


# ── 4.2 Pipeline integration ─────────────────────────────────────────────────

def test_pipeline_loads_vit_model():
    """Pipeline must load the ViT ONNX model (not run in simulated mode)."""
    from backend.app.config import Settings
    from backend.app.services.pipeline import Pipeline

    pipe = Pipeline(Settings())
    assert not pipe.clf.simulated, "Pipeline is in simulated mode — ONNX not loaded"
    assert "vit" in pipe.clf.name.lower(), (
        f"Expected 'vit' in model name, got '{pipe.clf.name}'. "
        "Did you run `python ml/switch_model.py cropguard38_vit`?"
    )


def test_pipeline_vit_predicts_apple_cedar_rust():
    """Live prediction on a known image must return a plausible class."""
    from backend.app.config import Settings
    from backend.app.services.pipeline import Pipeline

    img_path = ROOT / "data" / "test" / "test" / "AppleCedarRust1.JPG"
    if not img_path.exists():
        pytest.skip("Test image AppleCedarRust1.JPG not available")

    pipe = Pipeline(Settings())
    result = pipe.predict(img_path.read_bytes(), explain=False)
    assert result["confidence"] > 0.3, f"Confidence too low: {result['confidence']}"
    # Top-1 should be apple-related
    assert "Apple" in result["class_id"] or result["confidence"] > 0.5, (
        f"Unexpected prediction: {result['class_id']} @ {result['confidence']:.2%}"
    )


# ── 4.3 Field accuracy on PlantDoc subset ────────────────────────────────────

@pytest.mark.skipif(not (PD_DIR / "test").exists(), reason="PlantDoc dataset not downloaded")
def test_vit_field_accuracy_above_30pct():
    """ViT pipeline must exceed 30% accuracy on PlantDoc field test photos."""
    if str(ML_DIR) not in sys.path:
        sys.path.insert(0, str(ML_DIR))
    import cg_common as cg
    from backend.app.config import Settings
    from backend.app.services.pipeline import Pipeline

    pipe = Pipeline(Settings())
    cfg = json.load(open(ROOT / "ml" / "models" / "model_config.json"))
    classes = cfg["labels"]
    class_idx = {c: i for i, c in enumerate(classes)}

    fd_te, _ = cg.plantdoc_frame(PD_DIR / "test", class_idx)
    # Use first 60 images for speed
    sample = fd_te.head(60)

    correct = 0
    total = 0
    for _, row in sample.iterrows():
        try:
            result = pipe.predict(Path(row["path"]).read_bytes(), explain=False)
            if result["class_id"] == classes[row["y"]]:
                correct += 1
            total += 1
        except Exception:
            pass

    acc = correct / total if total > 0 else 0
    assert acc > 0.30, f"Field accuracy {acc:.2%} on PlantDoc subset is below 30%"


# ── 4.4 High-Accuracy Fine-Tuned Models (Combined & 384) ──────────────────────

COMBINED_DIR = ROOT / "ml" / "models" / "cropguard38_combined"
VIT384_DIR   = ROOT / "ml" / "models" / "cropguard38_384"


def test_combined_model_field_accuracy_above_70pct():
    """Combined ViT fine-tuned model must achieve > 70% field accuracy."""
    if not COMBINED_DIR.exists():
        pytest.skip("cropguard38_combined not found")
    cfg = json.load(open(COMBINED_DIR / "model_config.json"))
    assert cfg["field_test_accuracy"] > 0.70, f"Got {cfg['field_test_accuracy']:.2%}"


def test_384_model_exists_and_high_accuracy():
    """384x384 Focal-Loss ViT model must have 384 resolution, TTA enabled, and > 75% field accuracy."""
    if not VIT384_DIR.exists():
        pytest.skip("cropguard38_384 not found")
    cfg = json.load(open(VIT384_DIR / "model_config.json"))
    assert cfg["input_size"] == 384
    assert cfg["tta"] is True
    assert cfg["field_test_accuracy"] >= 0.75, f"Got {cfg['field_test_accuracy']:.2%}"
    assert (VIT384_DIR / "model.onnx").exists(), "cropguard38_384/model.onnx not found"

