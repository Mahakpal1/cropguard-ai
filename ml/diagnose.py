"""Phase 0: find out WHY a photo is rejected or wrong. Prints what the model really thinks.

    python ml/diagnose.py path/to/photo.jpg            (or a folder of photos)

Shows: top-5 over ALL model outputs (including crops we do not support), how much probability sits on out-of-scope classes,
the restricted top-3 for our classes, uncertainty scores (max prob, margin, energy), whether the test-time-augmentation
views agree, severity, and a plain-language hint about the likely cause.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings  # noqa: E402
from backend.app.services.classifier import softmax  # noqa: E402
from backend.app.services.pipeline import Pipeline  # noqa: E402
from cv import severity  # noqa: E402


def main(argv):
    if not argv:
        sys.exit(__doc__)
    pipe = Pipeline(Settings())
    clf = pipe.clf
    if clf.simulated:
        sys.exit("No model installed (simulated mode). Install one first: see docs/SETUP_AND_TRAINING_GUIDE.md")
    target = Path(argv[0])
    files = [target] if target.is_file() else sorted(p for p in target.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    labels = [None] * clf.n_out
    for i, cid in zip(clf.keep_idx, clf.keep_ids):
        labels[i] = cid
    raw_labels = clf.raw_labels
    for f in files:
        img = Pipeline.decode(f.read_bytes())
        x, views = clf.prepare(img)
        logits_v = clf.infer(views)                                   # one row per view
        logits = logits_v.mean(0)
        p_all = softmax(logits / clf.temperature)
        order = np.argsort(-p_all)[:5]
        in_scope = float(p_all[clf.keep_idx].sum())
        r = clf.predict(x, views=views)
        sev = severity.estimate(img)
        print(f"\n=== {f.name}  (padded to {img.size[0]}x{img.size[1]}) ===")
        print("top-5 over ALL model outputs:")
        for i in order:
            tag = "" if labels[i] else "   <- NOT one of our classes"
            print(f"   {p_all[i]*100:5.1f}%  {raw_labels[i]}{tag}")
        print(f"probability on our supported classes: {in_scope*100:.1f}%   |   on other crops/classes: {(1-in_scope)*100:.1f}%")
        print("restricted top-3:", ", ".join(f"{c} {p*100:.1f}%" for c, p in r["top3"]))
        s = r["scores"]
        print(f"scores: max_prob={s['max_prob']:.3f}  margin={s['margin']:.3f}  energy={s['energy']:.2f}  (lower energy = more familiar)")
        per_view = [raw_labels[int(l.argmax())] for l in logits_v]
        print("views agree:", len(set(per_view)) == 1, "->", per_view)
        print(f"severity estimate: {sev['affected_pct']}% ({sev['level']}), leaf fraction {sev['leaf_fraction']}")
        print(f"active gates: confidence>={clf.threshold}, energy<={clf.energy_threshold}, margin>={clf.margin_threshold}")
        hints = []
        if in_scope < 0.5:
            hints.append("most probability is on OTHER crops: this is probably a crop the model does not cover (coverage problem, not a threshold problem)")
        if len(set(per_view)) > 1:
            hints.append("the views disagree: the model is sensitive to framing/scale (more field data and scale augmentation will help)")
        if s["max_prob"] < clf.threshold and in_scope >= 0.5 and s["margin"] < 0.2:
            hints.append("flat distribution between look-alike classes: ambiguous disease or domain shift")
        if s["max_prob"] < clf.threshold and clf.threshold >= 0.85:
            hints.append(f"the confidence gate is {clf.threshold}: check how it was chosen (python ml/calibrate_gates.py)")
        print("hint:", "; ".join(hints) if hints else "model is reasonably sure; if it is still wrong, collect this photo for training")


if __name__ == "__main__":
    main(sys.argv[1:])
