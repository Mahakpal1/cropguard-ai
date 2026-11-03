import base64
import io

from PIL import Image

from backend.app.services.pipeline import Pipeline
from tests.conftest import BLUE, GREEN, build_toy_model, leaf_image, png_bytes


def run(settings, img, **kw):
    return Pipeline(settings).predict(png_bytes(img), **kw)


def test_simulated_mode_is_flagged_and_works(settings):
    healthy = run(settings, leaf_image(0.0))
    sick = run(settings, leaf_image(0.3))
    assert healthy["model"]["simulated"] is True
    assert healthy["class_id"] == "Tomato_healthy" and sick["class_id"] == "Tomato_Early_blight"
    assert sick["status"] == "ok" and sick["severity"]["level"] == "Moderate"
    assert set(sick["advice"]) == {"en", "hi"} and sick["advice"]["hi"]["do_now"]
    assert sick["heatmap"]["method"].startswith("lesion-proxy")


def test_no_leaf(settings):
    r = run(settings, Image.new("RGB", (200, 200), (240, 240, 240)))
    assert r["status"] == "no_leaf" and r["class_id"] is None and r["advice"]["en"]["do_now"]


def test_real_onnx_path(toy_settings):
    ok = run(toy_settings, leaf_image(0.0))
    assert ok["model"]["simulated"] is False and ok["model"]["name"] == "toy-test-model"
    assert ok["class_id"] == "Tomato_healthy" and ok["confidence"] > 0.9
    sick = run(toy_settings, leaf_image(0.3))
    assert sick["class_id"] == "Tomato_Early_blight" and sick["status"] == "ok"
    assert len(sick["top3"]) == 3 and abs(sum(t["p"] for t in sick["top3"]) - 1) < 0.2


def test_unsupported_crop_from_38_class_model(toy_settings):
    r = run(toy_settings, leaf_image(0.0, base=BLUE))
    assert r["status"] == "unsupported_crop" and r["class_id"] is None


def test_low_confidence_gate(toy_settings, toy_dir):
    import json
    cfg = json.load(open(toy_dir / "model_config.json"))
    cfg["temperature"] = 50.0                 # flatten probabilities -> unsure
    json.dump(cfg, open(toy_dir / "model_config.json", "w"))
    r = run(toy_settings, leaf_image(0.0))
    assert r["status"] == "low_confidence" and r["advice"]["en"]["do_now"]


def test_occlusion_heatmap_is_valid_rgba_png(toy_settings):
    r = run(toy_settings, leaf_image(0.3), explain=True)
    # Phase 6: pipeline now prefers DINOv2 Grad-CAM++ when torch is available;
    # falls back to occlusion-sensitivity if not. Both are valid.
    valid_methods = {"occlusion-sensitivity", "dinov2-gradcam++", "lesion-proxy (simulated)"}
    assert r["heatmap"]["method"] in valid_methods, f"Unexpected heatmap method: {r['heatmap']['method']}"
    im = Image.open(io.BytesIO(base64.b64decode(r["heatmap"]["png_base64"])))
    assert im.size == (224, 224)
    assert run(toy_settings, leaf_image(0.3), explain=False)["heatmap"] is None
