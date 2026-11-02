"""Merge several class-folder datasets into ONE dataset with ONE label list (Crop___Disease).

    python ml/datasets/prepare_union.py \\
        --src plantvillage=data/raw/plantvillage --src plantdoc=data/raw/plantdoc/train --src plantwild=data/raw/plantwild \\
        --map ml/datasets/label_map.csv --out data/union [--link]

Folder names that contain '___' (PlantVillage style, e.g. Tomato___Early_blight) are understood automatically.
Any other folder needs a row in the map CSV (source,folder,crop,disease). Folders without a mapping are listed in
ml/datasets/unmapped_<source>.csv (a ready-made template: fill crop and disease, copy the rows into label_map.csv, run again).
Exact duplicate images (same bytes) are dropped. Output: data/union/<label>/*.jpg and data/union/manifest.csv.
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXT = (".jpg", ".jpeg", ".png", ".webp")
CROP_ALIAS = {"Corn_maize": "Maize", "Cherry_including_sour": "Cherry", "Pepper_bell": "Pepper", "Pepper__bell": "Pepper", "Soyabean": "Soybean"}


def tok(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def label_for(source, folder, mapping):
    """Return (crop, disease) or None (unmapped) or 'skip' (explicitly ignored)."""
    if (source, folder) in mapping:
        crop, dis = mapping[(source, folder)]
        return "skip" if not crop else (tok(crop), tok(dis))
    if "___" in folder:
        crop, dis = folder.split("___", 1)
        crop = tok(crop)
        return CROP_ALIAS.get(crop, crop), tok(dis)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", action="append", required=True, help="name=path (repeat)")
    ap.add_argument("--map", default=str(Path(__file__).with_name("label_map.csv")))
    ap.add_argument("--out", default="data/union")
    ap.add_argument("--link", action="store_true", help="hard-link instead of copying (saves disk)")
    a = ap.parse_args(argv)
    mapping = {}
    if Path(a.map).exists():
        for r in csv.DictReader(open(a.map, encoding="utf-8")):
            mapping[(r["source"].strip(), r["folder"].strip())] = (r["crop"].strip(), r["disease"].strip())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    seen, rows, dups = set(), [], 0
    per_source, unmapped = Counter(), defaultdict(list)
    for spec in a.src:
        name, path = spec.split("=", 1)
        for d in sorted(p for p in Path(path).iterdir() if p.is_dir()):
            lab = label_for(name, d.name, mapping)
            if lab is None:
                unmapped[name].append(d.name); continue
            if lab == "skip":
                continue
            label = f"{lab[0]}___{lab[1]}"
            (out / label).mkdir(exist_ok=True)
            for f in sorted(p for p in d.rglob("*") if p.suffix.lower() in EXT):
                h = hashlib.md5(f.read_bytes()).hexdigest()
                if h in seen:
                    dups += 1; continue
                seen.add(h)
                dst = out / label / f"{name}__{tok(f.stem)}{f.suffix.lower()}"
                if not dst.exists():
                    (os.link if a.link else shutil.copy2)(f, dst)
                group = f.stem.split("___")[0] if name == "plantvillage" else h[:12]
                rows.append((str(dst.relative_to(out)), label, name, group))
                per_source[name] += 1
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["path", "label", "source", "group"]); w.writerows(rows)
    for name, folders in unmapped.items():
        t = Path(__file__).with_name(f"unmapped_{name}.csv")
        with open(t, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["source", "folder", "crop", "disease"]); w.writerows((name, f, "", "") for f in folders)
        print(f"! {len(folders)} unmapped folders in '{name}': fill {t.name} and append the rows to label_map.csv")
    labels = Counter(r[1] for r in rows); crops = Counter(r[1].split("___")[0] for r in rows)
    print(f"\n{len(rows)} images | {dups} exact duplicates removed | {len(labels)} classes | {len(crops)} crops")
    print("per source:", dict(per_source)); print("per crop:", dict(crops.most_common()))
    small = sorted(l for l, n in labels.items() if n < 30)
    if small:
        print(f"! {len(small)} classes have fewer than 30 images (get more photos or treat as experimental):", ", ".join(small[:12]))


if __name__ == "__main__":
    main(sys.argv[1:])
