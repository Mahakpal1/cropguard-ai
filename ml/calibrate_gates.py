"""Phase 1: set the confidence and out-of-distribution (energy) gates from DATA instead of guessing.

    python ml/calibrate_gates.py --id-dir <held-out field photos, one sub-folder per class> \\
                                 [--ood-dir <photos of crops/things we do NOT support>] [--target-precision 0.9] [--write]

* confidence threshold: lowest value at which answered photos reach the target precision (accuracy when answering).
* energy threshold: keeps 95 % of in-distribution photos; with --ood-dir it also reports how well unknown photos are rejected
  (AUROC and false-positive rate at 95 % true-positive rate).
Never calibrate on the images you test on: use a separate held-out field set.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings  # noqa: E402
from backend.app.services.class_mapping import map_label  # noqa: E402
from backend.app.services.pipeline import Pipeline  # noqa: E402

EXT = (".jpg", ".jpeg", ".png")


def auroc(pos, neg):
    """P(score of a random OOD photo > score of a random ID photo); both are 'higher = more out-of-distribution'."""
    s = np.concatenate([pos, neg]); r = s.argsort().argsort() + 1
    return float((r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def score(pipe, path):
    img = Pipeline.decode(Path(path).read_bytes())
    x, views = pipe.clf.prepare(img)
    return pipe.clf.predict(x, views=views)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id-dir", required=True); ap.add_argument("--ood-dir")
    ap.add_argument("--target-precision", type=float, default=0.9); ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    s = Settings(); pipe = Pipeline(s)
    if pipe.clf.simulated:
        sys.exit("No model installed.")
    lk = pipe.clf.lookup
    conf, ok, en = [], [], []
    for d in sorted(Path(a.id_dir).iterdir()):
        cid = map_label(d.name, lk)
        if not d.is_dir() or cid is None:
            print("skipping folder:", d.name); continue
        for f in (p for p in d.iterdir() if p.suffix.lower() in EXT):
            r = score(pipe, f); conf.append(r["confidence"]); ok.append(r["class_id"] == cid); en.append(r["scores"]["energy"])
    conf, ok, en = np.array(conf), np.array(ok), np.array(en)
    print(f"in-distribution photos: {len(conf)} | accuracy {ok.mean():.3f}")
    chosen = None
    print("threshold  coverage  precision-when-answering")
    for t in np.round(np.arange(0.3, 0.96, 0.05), 2):
        m = conf >= t
        prec = ok[m].mean() if m.any() else float("nan")
        print(f"  {t:.2f}     {m.mean():.3f}     {prec:.3f}")
        if chosen is None and m.sum() >= 20 and prec >= a.target_precision:
            chosen = float(t)
    energy_thr = float(np.percentile(en, 95))
    print(f"\nconfidence threshold for {a.target_precision:.0%} precision: {chosen if chosen is not None else 'NOT REACHABLE (model too weak on this data)'}")
    print(f"energy threshold (keeps 95% of in-distribution photos): {energy_thr:.3f}")
    if a.ood_dir:
        ood = np.array([score(pipe, f)["scores"]["energy"] for f in Path(a.ood_dir).rglob("*") if f.suffix.lower() in EXT])
        print(f"OOD photos: {len(ood)} | AUROC {auroc(ood, en):.3f} | caught at this threshold: {(ood > energy_thr).mean():.1%} (95% of ID photos pass)")
    if a.write:
        p = s.model_dir / "model_config.json"; cfg = json.load(open(p, encoding="utf-8"))
        cfg["energy_threshold"] = round(energy_thr, 4)
        if chosen is not None:
            cfg["confidence_threshold"] = chosen
        json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2)
        print("written to", p, "-> restart the server")


if __name__ == "__main__":
    main()
