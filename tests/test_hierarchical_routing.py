"""Two-Stage Hierarchical Routing Tests.

Covers:
- Stage 1 Taxonomic Crop Routing (BioCLIP) & Stage 2 Conditioned Disease Classification (ViT)
- Cross-species hallucination elimination
- Safe rejection of unsupported species (e.g. Rice, Wheat, Sugarcane)
- Conditional probability renormalization
- Live pipeline hierarchical metadata
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.app.config import Settings
from backend.app.services.hierarchical_router import HierarchicalRouter
from backend.app.services.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_hierarchical_routing_restricts_to_crop():
    router = HierarchicalRouter()
    classes = json.load(open(ROOT / "ml" / "models" / "cropguard38" / "class_names.json", encoding="utf-8"))["classes"]
    by_id = {c["id"]: c for c in classes}
    supported = sorted({c["crop"]["en"] for c in classes})

    # Simulated flat disease probs spanning Tomato, Potato, and Apple
    disease_probs = {
        "Tomato___Early_blight": 0.45,
        "Potato___Early_blight": 0.35,
        "Apple___Apple_scab": 0.15,
        "Apple___Black_rot": 0.05,
    }

    # BioCLIP identifies Apple with 92% confidence
    crop_res = {
        "name": "Apple",
        "p": 0.92,
        "probs": {"Apple": 0.92, "Tomato": 0.05, "Potato": 0.03},
        "threshold": 0.5,
    }

    out = router.route(disease_probs, crop_res, by_id, supported)
    assert not out["is_unsupported_crop"]
    assert out["class_id"].startswith("Apple___")
    # Both Apple classes must sum to 1.0
    assert pytest.approx(sum(out["probs"].values())) == 1.0
    # Tomato and Potato should be eliminated from the conditioned space
    assert "Tomato___Early_blight" not in out["probs"]
    assert "Potato___Early_blight" not in out["probs"]
    # Ratio between Apple scab (0.15) and Apple black rot (0.05) should be preserved: 0.75 vs 0.25
    assert pytest.approx(out["probs"]["Apple___Apple_scab"]) == 0.75
    assert pytest.approx(out["probs"]["Apple___Black_rot"]) == 0.25


def test_hierarchical_routing_unsupported_crop():
    router = HierarchicalRouter()
    classes = json.load(open(ROOT / "ml" / "models" / "cropguard38" / "class_names.json", encoding="utf-8"))["classes"]
    by_id = {c["id"]: c for c in classes}
    supported = sorted({c["crop"]["en"] for c in classes})

    disease_probs = {"Tomato___healthy": 0.8, "Potato___healthy": 0.2}

    # BioCLIP identifies Rice (an unsupported crop)
    crop_res = {
        "name": "Rice",
        "p": 0.95,
        "probs": {"Rice": 0.95, "Wheat": 0.03, "Tomato": 0.02},
        "threshold": 0.5,
    }

    out = router.route(disease_probs, crop_res, by_id, supported)
    assert out["is_unsupported_crop"] is True
    assert out["class_id"] is None


def test_hierarchical_routing_low_confidence_crop():
    router = HierarchicalRouter()
    classes = json.load(open(ROOT / "ml" / "models" / "cropguard38" / "class_names.json", encoding="utf-8"))["classes"]
    by_id = {c["id"]: c for c in classes}
    supported = sorted({c["crop"]["en"] for c in classes})

    disease_probs = {"Apple___healthy": 0.9}

    # BioCLIP confidence is 0.35, below the 0.50 threshold
    crop_res = {
        "name": "Apple",
        "p": 0.35,
        "probs": {"Apple": 0.35, "Peach": 0.35, "Cherry": 0.30},
        "threshold": 0.5,
    }

    out = router.route(disease_probs, crop_res, by_id, supported)
    assert out["is_unsupported_crop"] is True
    assert out["routing_mode"] == "low_crop_confidence_rejection"


def test_live_pipeline_hierarchical_prediction():
    img_path = ROOT / "data" / "test" / "test" / "AppleCedarRust1.JPG"
    if not img_path.exists():
        pytest.skip("Test image AppleCedarRust1.JPG not available")

    pipe = Pipeline(Settings())
    res = pipe.predict(img_path.read_bytes(), explain=False)

    assert res["status"] == "ok"
    assert res["class_id"] == "Apple___Cedar_apple_rust"
    assert res["crop_id"]["name"] == "Apple"
    assert res["hierarchical_meta"] is not None
    assert res["hierarchical_meta"]["routing_mode"] == "hierarchical_crop_conditioned"
    assert res["hierarchical_meta"]["species_agreement"] == 1.0


def test_hierarchical_routing_soft_fallback():
    """Soft fallback prevents false crop rejections when ViT is confident in a supported crop."""
    router = HierarchicalRouter()
    classes = json.load(open(ROOT / "ml" / "models" / "cropguard38" / "class_names.json", encoding="utf-8"))["classes"]
    by_id = {c["id"]: c for c in classes}
    supported = sorted({c["crop"]["en"] for c in classes})

    # ViT is 88% confident in Apple scab
    disease_probs = {"Apple___Apple_scab": 0.88, "Apple___Black_rot": 0.12}

    # BioCLIP zero-shot model mistook the background for Jute (unsupported)
    crop_res = {
        "name": "Jute",
        "p": 0.72,
        "probs": {"Jute": 0.72, "Apple": 0.18, "Tea": 0.10},
        "threshold": 0.5,
    }

    # Strict mode: rejects as unsupported crop
    strict_out = router.route(disease_probs, crop_res, by_id, supported, soft_fallback=False)
    assert strict_out["is_unsupported_crop"] is True
    assert strict_out["class_id"] is None

    # Soft fallback mode: preserves high-confidence ViT prediction
    soft_out = router.route(disease_probs, crop_res, by_id, supported, soft_fallback=True, fusion_weight=0.15)
    assert soft_out["is_unsupported_crop"] is False
    assert soft_out["class_id"] == "Apple___Apple_scab"
    assert soft_out["routing_mode"] == "bayesian_fusion_fallback"

