"""Phase 6 Integration Tests — DINOv2 Grad-CAM++ wiring, separated confidence fields, leaf-overlap UI.

These tests verify:
1. PredictResponse schema accepts (and defaults to None) the new Phase 6 optional fields.
2. Pipeline.predict() always returns the new Phase 6 keys in its output dict, defaulting to None.
3. dinov2_gradcam_png() returns the expected dict shape (graceful fallback when torch is absent).
4. The OpenAPI contract YAML includes all Phase 6 new fields.
5. Heatmap method for simulated mode is still "lesion-proxy (simulated)".
"""
import sys
import os
import types

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)


# ---------------------------------------------------------------------------
# 1. Schema validation — new fields are Optional and default to None
# ---------------------------------------------------------------------------
class TestPredictResponseSchema:
    def _make_minimal(self):
        """Return a dict that satisfies all REQUIRED fields of PredictResponse."""
        return {
            "status": "ok",
            "confidence": 0.85,
            "top3": [],
            "sources": [],
            "scores": {"max_prob": 0.85, "margin": 0.10},
            "severity": {"level": "Mild", "affected_pct": 5.0, "leaf_fraction": 0.6, "method": "hsv"},
            "advice": {
                "en": {"symptoms": [], "do_now": [], "avoid": [], "prevent": [], "disclaimer": "test"},
                "hi": {"symptoms": [], "do_now": [], "avoid": [], "prevent": [], "disclaimer": "परीक्षण"},
            },
            "model": {"name": "sim", "simulated": True, "temperature": 1.0, "threshold": 0.5},
            "timings_ms": {"decode": 1.0},
        }

    def test_new_fields_default_none(self):
        """Schema validates without the new Phase 6 keys (they should default to None)."""
        from backend.app.schemas import PredictResponse
        r = PredictResponse(**self._make_minimal())
        assert r.crop_confidence is None
        assert r.disease_confidence is None
        assert r.leaf_overlap_score is None
        assert r.is_grounded is None
        assert r.explainability_note is None
        assert r.top2_crop is None
        assert r.top2_disease is None
        assert r.top2_confidence is None

    def test_new_fields_accepted(self):
        """Schema accepts the new Phase 6 keys when populated."""
        from backend.app.schemas import PredictResponse
        d = self._make_minimal()
        d.update(
            crop_confidence=0.92,
            disease_confidence=0.87,
            leaf_overlap_score=0.73,
            is_grounded=True,
            explainability_note="Attention well-grounded on the leaf.",
            top2_crop="Wheat",
            top2_disease="Yellow Rust",
            top2_confidence=0.11,
        )
        r = PredictResponse(**d)
        assert r.crop_confidence == pytest.approx(0.92)
        assert r.disease_confidence == pytest.approx(0.87)
        assert r.leaf_overlap_score == pytest.approx(0.73)
        assert r.is_grounded is True
        assert "grounded" in r.explainability_note.lower()
        assert r.top2_crop == "Wheat"

    def test_new_fields_nullable(self):
        """Schema accepts explicit None for all new Phase 6 fields."""
        from backend.app.schemas import PredictResponse
        d = self._make_minimal()
        d.update(
            crop_confidence=None,
            disease_confidence=None,
            leaf_overlap_score=None,
            is_grounded=None,
            explainability_note=None,
        )
        r = PredictResponse(**d)
        assert r.crop_confidence is None
        assert r.is_grounded is None


# ---------------------------------------------------------------------------
# 2. Pipeline.predict() always emits Phase 6 keys
# ---------------------------------------------------------------------------
class TestPipelinePhase6Keys:
    PHASE6_KEYS = [
        "crop_confidence", "disease_confidence",
        "leaf_overlap_score", "is_grounded", "explainability_note",
        "top2_crop", "top2_disease", "top2_confidence",
    ]

    def _run_predict(self, explain=False):
        """Run pipeline in simulated mode and return the response dict."""
        import io
        from PIL import Image
        from backend.app.config import Settings

        # Build a 3×3 green leaf-like image
        img = Image.new("RGB", (100, 100), (34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        image_bytes = buf.getvalue()

        from backend.app.services.pipeline import Pipeline

        # Use the real Settings dataclass — simulated mode (no model dir with ONNX)
        s = Settings(
            model_dir=PROJ_ROOT + "/contracts",
            kb_dir=PROJ_ROOT + "/knowledge_base/broad",
            classes_path=PROJ_ROOT + "/contracts/class_names.json",
            explain_default=explain,
        )
        pipe = Pipeline(s)
        return pipe.predict(image_bytes, explain=explain)

    def test_phase6_keys_present_no_explain(self):
        result = self._run_predict(explain=False)
        for key in self.PHASE6_KEYS:
            assert key in result, f"Missing Phase 6 key in pipeline output: {key}"

    def test_phase6_keys_present_with_explain(self):
        result = self._run_predict(explain=True)
        for key in self.PHASE6_KEYS:
            assert key in result, f"Missing Phase 6 key in pipeline output: {key}"

    def test_phase6_keys_none_in_simulated_mode(self):
        """In simulated mode the DINOv2 Grad-CAM++ path is skipped; leaf_overlap_score stays None."""
        result = self._run_predict(explain=True)
        # simulated mode → falls back to lesion_proxy_png; leaf_overlap_score is None
        assert result["leaf_overlap_score"] is None


# ---------------------------------------------------------------------------
# 3. dinov2_gradcam_png() graceful fallback
# ---------------------------------------------------------------------------
class TestDinoV2GradcamPng:
    def test_returns_dict_with_required_keys(self):
        """dinov2_gradcam_png returns a dict with 'method' and 'png_base64', even on fallback."""
        import numpy as np
        from PIL import Image
        from backend.app.services.explain import dinov2_gradcam_png

        img = Image.new("RGB", (64, 64), (50, 120, 50))
        leaf_mask = np.ones((64, 64), dtype=np.float32) * 0.8

        result = dinov2_gradcam_png(img, leaf_mask=leaf_mask, target_class_idx=0)
        assert isinstance(result, dict)
        assert "method" in result
        assert "png_base64" in result
        assert isinstance(result["png_base64"], str)
        assert len(result["png_base64"]) > 0

    def test_no_data_uri_prefix(self):
        """png_base64 must NOT include the 'data:image/png;base64,' prefix (JS prepends it)."""
        import numpy as np
        from PIL import Image
        from backend.app.services.explain import dinov2_gradcam_png

        img = Image.new("RGB", (64, 64), (50, 120, 50))
        result = dinov2_gradcam_png(img, target_class_idx=0)
        assert not result["png_base64"].startswith("data:")

    def test_method_is_string(self):
        from PIL import Image
        from backend.app.services.explain import dinov2_gradcam_png

        img = Image.new("RGB", (32, 32), (60, 130, 60))
        result = dinov2_gradcam_png(img)
        assert isinstance(result["method"], str)
        assert len(result["method"]) > 0


# ---------------------------------------------------------------------------
# 4. OpenAPI contract YAML includes Phase 6 fields
# ---------------------------------------------------------------------------
class TestOpenApiContractPhase6:
    YAML_PATH = os.path.join(PROJ_ROOT, "contracts", "api.openapi.yaml")

    def _load_yaml_text(self):
        with open(self.YAML_PATH, encoding="utf-8") as f:
            return f.read()

    def test_crop_confidence_in_contract(self):
        assert "crop_confidence" in self._load_yaml_text()

    def test_disease_confidence_in_contract(self):
        assert "disease_confidence" in self._load_yaml_text()

    def test_leaf_overlap_score_in_contract(self):
        assert "leaf_overlap_score" in self._load_yaml_text()

    def test_is_grounded_in_contract(self):
        assert "is_grounded" in self._load_yaml_text()

    def test_explainability_note_in_contract(self):
        assert "explainability_note" in self._load_yaml_text()

    def test_top2_fields_in_contract(self):
        text = self._load_yaml_text()
        assert "top2_crop" in text
        assert "top2_disease" in text
        assert "top2_confidence" in text


# ---------------------------------------------------------------------------
# 5. Heatmap method is correct for simulated vs Grad-CAM paths
# ---------------------------------------------------------------------------
class TestHeatmapMethodNames:
    def test_lesion_proxy_method_name(self):
        """lesion_proxy_png always returns method='lesion-proxy (simulated)'."""
        import numpy as np
        from backend.app.services.explain import lesion_proxy_png

        mask = np.random.rand(56, 56).astype(np.float32)
        out = lesion_proxy_png(mask)
        assert out["method"] == "lesion-proxy (simulated)"

    def test_occlusion_method_name(self):
        """occlusion_png returns method='occlusion-sensitivity'."""
        import numpy as np
        from backend.app.services.explain import occlusion_png

        # Build a minimal fake classifier that supports probs_all
        class _FakeClf:
            def probs_all(self, x):
                n = x.shape[0]
                p = np.zeros((n, 3), dtype=np.float32)
                p[:, 0] = 0.9
                return p

        x = np.zeros((1, 3, 48, 48), dtype=np.float32)
        out = occlusion_png(_FakeClf(), x, target_index=0, grid=3, batch=4)
        assert out["method"] == "occlusion-sensitivity"

    def test_dinov2_gradcam_method_name_contains_gradcam(self):
        """dinov2_gradcam_png method name should contain 'gradcam' (even on fallback)."""
        from PIL import Image
        from backend.app.services.explain import dinov2_gradcam_png

        img = Image.new("RGB", (32, 32), (60, 130, 60))
        out = dinov2_gradcam_png(img)
        # either "dinov2-gradcam++" (torch available) or fallback with lesion-proxy
        assert "gradcam" in out["method"].lower() or "lesion" in out["method"].lower()
