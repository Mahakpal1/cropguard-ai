"""Leaf and lesion segmentation using simple, explainable HSV colour rules.

Leaf   = pixels that are coloured enough (saturation > S_MIN) and not too dark (value > V_MIN).
Lesion = leaf pixels that are NOT healthy green (hue 60-170 degrees with enough saturation).
A small median filter removes isolated speckles.
"""
import numpy as np
from PIL import Image, ImageFilter

S_MIN, V_MIN = 0.20, 0.12          # leaf vs background
GREEN_H = (60.0, 170.0)            # healthy green hue band (degrees)
GREEN_S_MIN = 0.25


def to_rgb(img, size=256):
    """PIL image -> float array HxWx3 in [0,1], longest side resized to `size`."""
    img = img.convert("RGB")
    w, h = img.size
    scale = size / max(w, h)
    if scale < 1:
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def rgb_to_hsv(a):
    """Vectorised RGB (0-1) -> (h in degrees, s, v)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rc = (mx == r) & m
    gc = (mx == g) & m & ~rc
    bc = m & ~rc & ~gc
    h[rc] = ((g - b)[rc] / d[rc]) % 6
    h[gc] = (b - r)[gc] / d[gc] + 2
    h[bc] = (r - g)[bc] / d[bc] + 4
    h *= 60.0
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0.0)
    return h, s, mx


def _clean(mask, k=5):
    im = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(k))
    return np.asarray(im) > 127


def leaf_mask(rgb, clean=True):
    _, s, v = rgb_to_hsv(rgb)
    m = (s > S_MIN) & (v > V_MIN)
    return _clean(m) if clean else m


def lesion_mask(rgb, leaf, clean=True):
    h, s, _ = rgb_to_hsv(rgb)
    green = (h >= GREEN_H[0]) & (h <= GREEN_H[1]) & (s > GREEN_S_MIN)
    m = leaf & ~green
    return (_clean(m, 3) & leaf) if clean else m
