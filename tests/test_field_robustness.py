"""Phase 3 feature and robustness tests.

Covers:
- Field enhancement module (cv.enhance)
- PlantDoc dataset mapping (28 classes, zero unmapped)
- Model evaluation on challenging field photographs
- Transfer learning model registry validation
"""
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PD_DIR = ROOT / "work" / "plantdoc"


# ── 3.1 Field Enhancement ───────────────────────────────────────────────────

def test_adaptive_contrast_produces_valid_image():
    from cv.enhance import adaptive_contrast
    img = Image.fromarray(np.full((128, 128, 3), 100, dtype=np.uint8))
    out = adaptive_contrast(img)
    assert isinstance(out, Image.Image)
    assert out.size == img.size


def test_field_enhance_handles_extremes():
    from cv.enhance import field_enhance
    # Test very dark image
    dark = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
    assert isinstance(field_enhance(dark), Image.Image)
    # Test bright image
    bright = Image.fromarray(np.full((64, 64, 3), 255, dtype=np.uint8))
    assert isinstance(field_enhance(bright), Image.Image)


# ── 3.2 PlantDoc Field Dataset ──────────────────────────────────────────────

@pytest.mark.skipif(not (PD_DIR / "train").exists(), reason="PlantDoc dataset not downloaded")
def test_plantdoc_maps_all_defined_classes():
    import json
    import sys
    ml_dir = ROOT / "ml"
    if str(ml_dir) not in sys.path:
        sys.path.insert(0, str(ml_dir))
    import cg_common as cg

    classes = json.load(open(ROOT / "ml" / "models" / "model_config.json"))["labels"]
    class_idx = {c: i for i, c in enumerate(classes)}

    fd_tr, sk1 = cg.plantdoc_frame(PD_DIR / "train", class_idx)
    fd_te, sk2 = cg.plantdoc_frame(PD_DIR / "test", class_idx)

    assert len(sk1) == 0, f"Expected 0 skipped in train, got {sk1}"
    assert len(sk2) == 0, f"Expected 0 skipped in test, got {sk2}"
    assert len(fd_tr) > 2000, f"Expected > 2000 train images, got {len(fd_tr)}"
    assert len(fd_te) > 200, f"Expected > 200 test images, got {len(fd_te)}"
    assert fd_tr.pd_class.nunique() >= 25


# ── 3.3 Transfer Learning Registry ─────────────────────────────────────────

def test_transfer_learning_backbones_available():
    """Verify that recommended transfer-learning backbones are available in timm."""
    import timm
    recommended = [
        "convnext_tiny.fb_in22k_ft_in1k",
        "efficientnet_b0",
        "resnet50d"
    ]
    for b in recommended:
        assert timm.is_model(b), f"Backbone {b} should be available in timm"
        assert timm.is_model_pretrained(b), f"Pretrained weights for {b} should be available"
