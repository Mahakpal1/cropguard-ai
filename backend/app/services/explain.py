"""Visual explanations returned as RGBA PNG overlays (base64).

* occlusion_png: model-agnostic occlusion sensitivity. Hide one patch at a time and measure how much the predicted
  class probability drops; big drops = regions the model relied on. Needs only ONNX Runtime (no gradients).
  (Proper Grad-CAM, which needs PyTorch, is produced in the training notebook for the report.)
* lesion_proxy_png: used only in simulated mode, from the lesion mask.
"""
import base64
import io

import numpy as np
from PIL import Image, ImageFilter


def _colorize(t):
    """t: float HxW in [0,1] -> RGBA PNG base64 (transparent where low)."""
    c0, c1 = np.array([236, 205, 120], np.float32), np.array([204, 98, 88], np.float32)
    rgb = c0 + (c1 - c0) * t[..., None]
    alpha = np.where(t > 0.08, 170 * np.minimum(1.0, t * 1.5), 0)
    rgba = np.dstack([rgb, alpha]).clip(0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def occlusion_png(clf, x, target_index, grid=6, batch=12):
    size = x.shape[-1]
    step = int(np.ceil(size / grid))
    base = float(clf.probs_all(x)[0, target_index])
    variants, boxes = [], []
    for gy in range(grid):
        for gx in range(grid):
            v = x.copy()
            v[:, :, gy * step:(gy + 1) * step, gx * step:(gx + 1) * step] = 0.0   # 0 = mean colour after normalisation
            variants.append(v)
    drops = []
    for i in range(0, len(variants), batch):
        p = clf.probs_all(np.concatenate(variants[i:i + batch], 0))[:, target_index]
        drops.extend(np.maximum(0.0, base - p))
    g = np.array(drops, np.float32).reshape(grid, grid)
    g = g / g.max() if g.max() > 1e-6 else g
    up = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC), np.float32) / 255.0
    return {"method": "occlusion-sensitivity", "png_base64": _colorize(up.clip(0, 1))}


def lesion_proxy_png(lesion, size=224):
    im = Image.fromarray((lesion * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR).filter(ImageFilter.GaussianBlur(8))
    a = np.asarray(im, np.float32)
    a = a / a.max() if a.max() > 0 else a
    return {"method": "lesion-proxy (simulated)", "png_base64": _colorize(a)}
