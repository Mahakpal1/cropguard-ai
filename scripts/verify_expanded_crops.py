import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app.config import Settings
from backend.app.main import create_app
from tests.conftest import leaf_image, png_bytes

def verify():
    settings = Settings()
    app = create_app(settings)
    with TestClient(app) as client:
        # 1. Verify /api/v1/classes returns all expanded classes
        res = client.get("/api/v1/classes")
        assert res.status_code == 200
        classes = res.json()["classes"]
        print(f"Total classes returned by /api/v1/classes: {len(classes)}")
        assert len(classes) >= 87, f"Expected at least 87 classes, got {len(classes)}"

        crops = {c["crop"]["en"] for c in classes if isinstance(c, dict) and "crop" in c}
        print(f"Unique crops in /api/v1/classes ({len(crops)}): {sorted(crops)}")
        for expected_crop in ["Rice", "Sugarcane", "Cotton", "Groundnut", "Mango", "Wheat", "Maize", "Tomato", "Potato"]:
            assert expected_crop in crops, f"Missing expected crop: {expected_crop}"

        # 2. Verify supported_crops in Pipeline
        pipe = app.state.pipe
        print(f"Pipeline supported_crops count: {len(pipe.supported_crops)}")
        for expected_crop in ["Rice", "Sugarcane", "Cotton", "Groundnut", "Mango", "Wheat", "Maize"]:
            assert expected_crop in pipe.supported_crops, f"Pipeline missing {expected_crop} in supported_crops"

        # 3. Verify knowledge base entries for new field crops
        for kb_id in [
            "Rice___Blast", "Rice___Brown_Spot", "Rice___Bacterial_Blight",
            "Sugarcane___Red_Rot", "Sugarcane___Yellow_Leaf",
            "Cotton___Bacterial_Blight",
            "Groundnut___Early_Leaf_Spot", "Groundnut___Rust",
            "Mango___Anthracnose", "Mango___Die_Back",
            "Wheat___Yellow_Rust", "Wheat___Brown_Rust",
            "Corn_maize___Common_rust"
        ]:
            entry = pipe.adv.entry(kb_id)
            assert entry is not None, f"Missing knowledge base entry for {kb_id}"
            print(f"KB [{kb_id}] -> {entry['crop']['en']} · {entry['disease']['en']} (status: {entry['review']['status']})")

        # 4. Verify feedback endpoint accepts expanded classes
        img_bytes = png_bytes(leaf_image(0.3))
        pred_res = client.post("/api/v1/predict", files={"file": ("leaf.png", img_bytes, "image/png")})
        assert pred_res.status_code == 200
        pred_data = pred_res.json()
        scan_id = pred_data["id"]

        for test_class in ["Rice___Blast", "Sugarcane___Red_Rot", "Cotton___Bacterial_Blight", "Groundnut___Early_Leaf_Spot", "Mango___Anthracnose", "Wheat___Yellow_Rust"]:
            fb_res = client.post("/api/v1/feedback", json={
                "scan_id": scan_id,
                "is_correct": False,
                "corrected_class_id": test_class,
                "notes": f"Verified correction for {test_class}"
            })
            assert fb_res.status_code == 200, f"Feedback failed for {test_class}: {fb_res.text}"
            print(f"Feedback accepted for {test_class} -> {fb_res.json()['corrected_class_id']}")

        print("\nALL EXPANDED CROPS & DISEASES SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    verify()
