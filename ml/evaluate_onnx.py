"""Evaluate the model in ml/models on an ImageFolder-style test set (one sub-folder per class).

    python ml/evaluate_onnx.py --data /path/to/test_images [--limit 500]

Folder names are mapped to CropGuard classes (PlantVillage naming), so both 15- and 38-class folders work.
Reports accuracy, macro-F1, top-3, per-class recall, calibration error (ECE) and risk-coverage at several thresholds.
Use it to check any model before you quote numbers, and to measure lab vs field accuracy (run it on both folders).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings  # noqa: E402
from backend.app.services.class_mapping import build_lookup, load_classes, map_label  # noqa: E402
from backend.app.services.classifier import Classifier  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--limit", type=int, default=0, help="max images per class (0 = all)")
    a = ap.parse_args()
    s = Settings()
    classes = load_classes(s.classes_path)
    clf = Classifier(s.model_dir, classes, s.default_threshold)
    if clf.simulated:
        sys.exit("No model found in ml/models (run download_pretrained.py or train with the notebook first).")
    lk, ids = build_lookup(classes), [c["id"] for c in classes]
    y, p, conf, top3 = [], [], [], []
    for d in sorted(Path(a.data).iterdir()):
        cid = map_label(d.name, lk)
        if not d.is_dir() or cid is None:
            print("skipping folder:", d.name)
            continue
        files = [f for f in sorted(d.iterdir()) if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
        for f in files[: a.limit or None]:
            r = clf.predict(clf.preprocess(Image.open(f).convert("RGB")))
            y.append(ids.index(cid)); p.append(ids.index(r["class_id"])); conf.append(r["confidence"])
            top3.append(ids.index(cid) in [ids.index(c) for c, _ in r["top3"]])
    y, p, conf = np.array(y), np.array(p), np.array(conf)
    print(f"\nimages: {len(y)} | model: {clf.name} | temperature {clf.temperature}")
    print(f"accuracy {np.mean(y == p):.4f} | top-3 {np.mean(top3):.4f}")
    f1s = []
    for k in sorted(set(y)):
        tp = np.sum((p == k) & (y == k)); fp = np.sum((p == k) & (y != k)); fn = np.sum((p != k) & (y == k))
        f1s.append(2 * tp / max(2 * tp + fp + fn, 1))
        print(f"  {ids[k]:48s} recall {tp / max(tp + fn, 1):.3f}  n={int(np.sum(y == k))}")
    print(f"macro-F1 {np.mean(f1s):.4f}")
    edges, e = np.linspace(0, 1, 11), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs(np.mean(y[m] == p[m]) - conf[m].mean())
    print(f"ECE {e:.4f}\nthreshold  coverage  accuracy-when-answering")
    for t in (0.3, 0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= t
        print(f"  {t:.1f}      {m.mean():.3f}    {np.mean(y[m] == p[m]) if m.any() else float('nan'):.3f}")


if __name__ == "__main__":
    main()
