"""Choose which model folder the backend uses.

    python ml/switch_model.py --list
    python ml/switch_model.py community     # the downloaded pretrained model   (ml/models/community/)
    python ml/switch_model.py cropguard     # the model you trained             (ml/models/cropguard/)

Each folder holds its own model_config.json. This script writes ml/models/model_config.json pointing into the chosen
folder; the backend always reads that top-level file. Restart the server afterwards.
"""
import json
import sys
from pathlib import Path

MODELS = Path(__file__).resolve().parent / "models"


def available(models_dir=MODELS):
    return sorted(p.name for p in Path(models_dir).iterdir() if (p / "model_config.json").exists())


def activate(models_dir, name):
    models_dir = Path(models_dir)
    cfg = json.load(open(models_dir / name / "model_config.json", encoding="utf-8"))
    if "onnx" in cfg:
        cfg["onnx"] = f"{name}/{cfg['onnx']}"
    if "checkpoint" in cfg:
        cfg["checkpoint"] = f"{name}/{cfg['checkpoint']}"
    for key in ("labels_file", "classes_file"):
        if key in cfg:
            cfg[key] = f"{name}/{cfg[key]}"
    cfg["model_folder"] = name
    json.dump(cfg, open(models_dir / "model_config.json", "w", encoding="utf-8"), indent=2)
    return cfg


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if argv[0] == "--list":
        print("available:", available() or "none yet")
        top = MODELS / "model_config.json"
        if top.exists():
            top_cfg = json.load(open(top, encoding="utf-8"))
            act = top_cfg.get("model_folder") or top_cfg.get("onnx") or top_cfg.get("name")
            print("active:", act)
        else:
            print("active: none (simulated mode)")
        return
    if argv[0] not in available():
        sys.exit(f"'{argv[0]}' not found in ml/models. Available: {available() or 'none'}")
    cfg = activate(MODELS, argv[0])
    target = cfg.get("onnx") or cfg.get("checkpoint") or cfg.get("name")
    print(f"Active model: {cfg['name']}  ({target}). Restart the server.")


if __name__ == "__main__":
    main(sys.argv[1:])
