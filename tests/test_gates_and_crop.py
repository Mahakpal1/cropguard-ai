import json

from PIL import Image

from backend.app.services.advisory import Advisory
from backend.app.services.classifier import Classifier
from backend.app.services.class_mapping import load_classes
from backend.app.services.pipeline import Pipeline, pad_square
from tests.conftest import BLUE, GREEN, ROOT, build_toy_crop_id, leaf_image, patch_config, png_bytes, settings_for

GREEN_VEC = [50 / 255, 130 / 255, 50 / 255]


def run(s, img):
    return Pipeline(s).predict(png_bytes(img), explain=False)


def test_scores_are_reported(toy_settings):
    r = run(toy_settings, leaf_image(0.3))
    assert r["scores"]["max_prob"] > 0.9 and r["scores"]["margin"] > 0.9 and r["scores"]["energy"] is not None


def test_energy_gate_flags_unfamiliar_inputs(tmp_path, toy_dir):
    patch_config(toy_dir, energy_threshold=-1000.0)            # nothing is "familiar enough"
    assert run(settings_for(tmp_path, toy_dir), leaf_image(0.3))["status"] == "unsupported_crop"
    patch_config(toy_dir, energy_threshold=1000.0)             # everything passes
    assert run(settings_for(tmp_path, toy_dir), leaf_image(0.3))["status"] == "ok"


def test_margin_gate_makes_close_calls_low_confidence(tmp_path, toy_dir):
    patch_config(toy_dir, margin_threshold=1.1)
    r = run(settings_for(tmp_path, toy_dir), leaf_image(0.3))
    assert r["status"] == "low_confidence" and r["top3"]          # candidates are still returned for the UI


def test_tta_views(toy_dir):
    clf = Classifier(toy_dir, load_classes(ROOT / "contracts" / "class_names.json"))
    x, views = clf.prepare(leaf_image(0.2))
    assert x.shape == (1, 3, 224, 224) and views.shape == (3, 3, 224, 224)
    patch_config(toy_dir, tta=False)
    x, views = Classifier(toy_dir, load_classes(ROOT / "contracts" / "class_names.json")).prepare(leaf_image(0.2))
    assert views.shape[0] == 1


def test_pad_square_keeps_everything_visible():
    im = pad_square(Image.new("RGB", (200, 100), (0, 200, 0)))
    assert im.size == (200, 200) and im.getpixel((0, 0)) == (128, 128, 128) and im.getpixel((100, 100)) == (0, 200, 0)


def test_crop_stage_restricts_diseases_to_the_detected_crop(tmp_path, toy_dir):
    build_toy_crop_id(toy_dir, {"Potato": GREEN_VEC, "Tomato": [1, 0, 0], "Apple": [0, 0, 1]})
    r = run(settings_for(tmp_path, toy_dir), leaf_image(0.0))     # classifier alone says Tomato_healthy
    assert r["crop_id"]["name"] == "Potato" and r["class_id"].startswith("Potato")


def test_crop_stage_rejects_crops_we_have_no_diseases_for(tmp_path, toy_dir):
    build_toy_crop_id(toy_dir, {"Potato": GREEN_VEC, "Tomato": [1, 0, 0], "Apple": [0, 0, 1]})
    r = run(settings_for(tmp_path, toy_dir), leaf_image(0.0, base=BLUE))
    assert r["status"] == "unsupported_crop" and r["crop_id"]["name"] == "Apple"


def test_crop_stage_threshold(tmp_path, toy_dir):
    build_toy_crop_id(toy_dir, {"Potato": GREEN_VEC, "Tomato": [1, 0, 0]}, threshold=1.1)
    assert run(settings_for(tmp_path, toy_dir), leaf_image(0.0))["status"] == "unsupported_crop"


def test_advice_tiers_and_generic_fallback():
    a = Advisory(ROOT / "knowledge_base")
    assert a.tier("Tomato_Early_blight") == a.tier("Tomato___Early_blight") == "draft" and a.tier("Rice___Brown_spot") == "none"
    g = a.advice("Rice___Brown_spot")
    assert g["en"]["do_now"] and g["hi"]["do_now"] and "officer" in " ".join(g["en"]["do_now"]).lower()


def test_response_has_tier(toy_settings):
    assert run(toy_settings, leaf_image(0.3))["advice_tier"] == "draft"


def test_model_folder_can_ship_its_own_class_list(tmp_path, toy_dir):
    base = json.load(open(ROOT / "contracts" / "class_names.json", encoding="utf-8"))
    base["classes"].append({"id": "Apple___Apple_scab", "crop": {"en": "Apple", "hi": "सेब"}, "disease": {"en": "Apple Scab", "hi": "सेब का स्कैब"}, "healthy": False})
    json.dump(base, open(toy_dir / "my_classes.json", "w", encoding="utf-8"), ensure_ascii=False)
    patch_config(toy_dir, classes_file="my_classes.json")
    pipe = Pipeline(settings_for(tmp_path, toy_dir))
    assert len(pipe.classes) == 16
    r = pipe.predict(png_bytes(leaf_image(0.0, base=BLUE)), explain=False)        # the toy model's "Apple" output is now in scope
    assert r["status"] == "ok" and r["class_id"] == "Apple___Apple_scab"
    # advice_tier is "draft" when broad KB has an entry, "none" when only root KB is active
    assert r["advice_tier"] in ("none", "draft")
    assert r["advice"]["en"]["do_now"] and r["advice"]["hi"]["do_now"]


def test_generic_advice_for_unlisted_healthy_class_is_sensible():
    g = Advisory(ROOT / "knowledge_base").advice("Apple___healthy")
    assert "spray pesticides on healthy" in " ".join(g["en"]["avoid"]).lower()
