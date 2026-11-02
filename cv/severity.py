"""Severity = affected area = lesion pixels / leaf pixels (an image-based ESTIMATE, not a lab measurement)."""
from .segmentation import to_rgb, leaf_mask, lesion_mask

DEFAULT_BINS = (10.0, 35.0)   # Mild < 10 <= Moderate < 35 <= Severe  (configurable)


def level_for(pct, bins=DEFAULT_BINS):
    return "Mild" if pct < bins[0] else "Moderate" if pct < bins[1] else "Severe"


def estimate(img, bins=DEFAULT_BINS, size=256, return_masks=False):
    rgb = to_rgb(img, size)
    leaf = leaf_mask(rgb)
    n_leaf = int(leaf.sum())
    total = leaf.size
    if n_leaf == 0:
        out = {"level": "Mild", "affected_pct": 0.0, "leaf_fraction": 0.0, "method": "hsv-threshold"}
        return (out, leaf, leaf) if return_masks else out
    les = lesion_mask(rgb, leaf)
    pct = 100.0 * float(les.sum()) / n_leaf
    out = {"level": level_for(pct, bins), "affected_pct": round(pct, 1),
           "leaf_fraction": round(n_leaf / total, 3), "method": "hsv-threshold"}
    return (out, leaf, les) if return_masks else out
