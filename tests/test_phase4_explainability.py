"""Tests for Phase 4: Explainability (Grad-CAM++) and Physiological Grounding.

Verifies:
1. ViT token reshape transform to 2D spatial feature map.
2. LeafOverlapVerifier detection of grounded vs background-drifted heatmaps.
3. Grad-CAM++ generation and PNG / base64 overlay encoding.
4. End-to-end CropGuardInferenceEngine integration.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn
from PIL import Image

from src.gradcam import (
    DINOv2GradCAM,
    ExplainabilityResult,
    LeafOverlapVerifier,
    vit_reshape_transform,
)
from src.heads import HierarchicalClassifier
from src.infer import CropGuardInferenceEngine, EndToEndDiagnosis

ROOT = Path(__file__).resolve().parents[1]


# ── 1. Reshape Transform Tests ───────────────────────────────────────────────

def test_vit_reshape_transform_shape():
    batch_size = 2
    seq_len = 257  # 1 [CLS] token + 256 patch tokens (16x16)
    embed_dim = 384

    # Simulated transformer output (B, 1+N, C)
    tokens = torch.randn(batch_size, seq_len, embed_dim)
    spatial_map = vit_reshape_transform(tokens, height=16, width=16)

    # Expected spatial shape: (B, C, H, W)
    assert spatial_map.shape == (batch_size, embed_dim, 16, 16)


# ── 2. Leaf Overlap Verifier Tests ───────────────────────────────────────────

def test_leaf_overlap_verifier_grounded_vs_drifted():
    verifier = LeafOverlapVerifier(grounding_threshold=0.65)
    h, w = 100, 100

    # Leaf mask: circle in center
    leaf_mask = np.zeros((h, w), dtype=np.uint8)
    leaf_mask[20:80, 20:80] = 255

    # Case A: Well-grounded heatmap (activation is inside the leaf center)
    grounded_heatmap = np.zeros((h, w), dtype=np.float32)
    grounded_heatmap[35:65, 35:65] = 1.0

    score_a, is_grounded_a, note_a = verifier.evaluate(grounded_heatmap, leaf_mask)
    assert score_a > 0.95
    assert is_grounded_a is True
    assert "Well-grounded" in note_a

    # Case B: Drifted heatmap (activation is completely in background border)
    drifted_heatmap = np.zeros((h, w), dtype=np.float32)
    drifted_heatmap[0:15, 0:15] = 1.0  # Outside leaf

    score_b, is_grounded_b, note_b = verifier.evaluate(drifted_heatmap, leaf_mask)
    assert score_b < 0.10
    assert is_grounded_b is False
    assert "warning" in note_b.lower()


# ── 3. Grad-CAM++ & Encoding Tests ───────────────────────────────────────────

def test_gradcam_overlay_encoding():
    # Synthetic RGB overlay array
    overlay = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

    # Test PNG bytes encoding
    png_bytes = DINOv2GradCAM.overlay_to_png_bytes(overlay)
    assert len(png_bytes) > 100
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    # Test base64 URI encoding
    uri = DINOv2GradCAM.overlay_to_base64_data_uri(overlay)
    assert uri.startswith("data:image/png;base64,")


# ── 4. End-to-End Inference Engine Tests ─────────────────────────────────────

def test_end_to_end_inference_engine():
    # Setup lightweight hierarchical classifier
    in_dim = 384
    crops = ["Tomato"]
    disease_map = {"Tomato": ["Early_Blight", "Healthy"]}

    classifier = HierarchicalClassifier(
        in_features=in_dim,
        crop_names=crops,
        crop_disease_map=disease_map,
        crop_threshold=0.10,  # Allow passage for test
        energy_threshold=50.0,
    )
    # Set positive bias towards supported crop for deterministic test evaluation
    with torch.no_grad():
        classifier.crop_head.net[-1].bias[0] = 5.0
        classifier.crop_head.net[-1].bias[1] = -5.0

    engine = CropGuardInferenceEngine(
        classifier=classifier,
        model_name="dinov2_vits14",
        grounding_threshold=0.50,
    )

    # Test with synthetic green leaf photo
    img = np.ones((200, 200, 3), dtype=np.uint8) * 200
    img[40:160, 40:160] = [34, 139, 34]  # Green leaf patch
    pil_leaf = Image.fromarray(img)

    diagnosis = engine.diagnose(pil_leaf, explain=True)
    assert isinstance(diagnosis, EndToEndDiagnosis)
    assert diagnosis.is_supported is True
    assert diagnosis.crop == "Tomato"
    assert diagnosis.disease in disease_map["Tomato"]
    assert diagnosis.leaf_overlap_score is not None
    assert diagnosis.heatmap_data_uri is not None
    assert diagnosis.heatmap_data_uri.startswith("data:image/png;base64,")

    # Test with blank image (should trigger leaf rejection gate)
    blank = np.ones((200, 200, 3), dtype=np.uint8) * 128
    blank_diag = engine.diagnose(blank, explain=False)
    assert blank_diag.status == "REJECTED"
    assert blank_diag.is_supported is False
