"""Download a ready-made 38-class PlantVillage ONNX model and write ml/models/model_config.json for the backend.

    python ml/download_pretrained.py [--activate]

Source (community model on Hugging Face): BiernyVR/crop-disease-classifier  (EfficientNetV2-S, ONNX Runtime, 38 classes).
IMPORTANT before you use it in a report:
  1. Read the model card and licence at https://huggingface.co/BiernyVR/crop-disease-classifier
  2. Run `python ml/evaluate_onnx.py` on YOUR held-out test images; do not quote someone else's accuracy as yours.
  3. PlantVillage models are trained on lab photos; expect lower accuracy on real field photos.
The backend maps the 38 classes down to CropGuard's 15 (tomato, potato, pepper) and reports other crops as unsupported.
"""
import json
import sys
import urllib.request
from pathlib import Path

REPO = "BiernyVR/crop-disease-classifier"
BASE = f"https://huggingface.co/{REPO}/resolve/main/"
FILES = ["efficientnet_v2_s_best.onnx", "efficientnet_v2_s_best.onnx.data", "classes.json"]
OUT = Path(__file__).resolve().parent / "models" / "community"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from switch_model import activate  # noqa: E402


def fetch(name):
    dst = OUT / name
    if dst.exists() and dst.stat().st_size > 0:
        print("have", name)
        return
    print("downloading", name, "...")
    try:
        urllib.request.urlretrieve(BASE + name, dst)
    except Exception as e:
        sys.exit(f"Could not download {name}: {e}\nDownload the files manually from the model page into {OUT}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        fetch(f)
    classes = json.load(open(OUT / "classes.json", encoding="utf-8"))
    labels = classes["classes"] if isinstance(classes, dict) else classes
    cfg = {"name": "efficientnetv2s-plantvillage38 (community)", "onnx": FILES[0], "labels": labels,
           "input_size": 224, "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225],
           "temperature": 1.0, "confidence_threshold": 0.6}
    json.dump(cfg, open(OUT / "model_config.json", "w", encoding="utf-8"), indent=2)
    top = OUT.parent / "model_config.json"
    if not top.exists() or "--activate" in sys.argv:
        activate(OUT.parent, "community")
        print("Activated: the backend will use the community model after you restart it.")
    else:
        print("Another model is already active; run `python ml/switch_model.py community` to use this one.")
    print(f"Wrote {OUT/'model_config.json'} with {len(labels)} labels.\n"
          "input_size is read from the ONNX file when it is fixed; check mean/std against the model card.\n"
          "Next: python ml/evaluate_onnx.py --data <folder with class sub-folders>")


if __name__ == "__main__":
    main()
