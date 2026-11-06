"""Visual explanations returned as RGBA PNG overlays (base64).

* occlusion_png: model-agnostic occlusion sensitivity. Hide one patch at a time and measure how much the predicted
  class probability drops; big drops = regions the model relied on. Needs only ONNX Runtime (no gradients).
  (Proper Grad-CAM, which needs PyTorch, is produced in the training notebook for the report.)
* lesion_proxy_png: used only in simulated mode, from the lesion mask.
* dinov2_gradcam_png: Phase 6 — full-colour Grad-CAM++ from the frozen DINOv2 backbone + hierarchical head.
  Requires PyTorch and src.gradcam; falls back to lesion_proxy_png if imports fail.
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


def dinov2_gradcam_png(pil_image, leaf_mask=None, target_class_idx=0, dinov2_engine=None):
    """Phase 6: Generate a full-colour Grad-CAM++ overlay and Attention Rollout using DINOv2.

    Imports from ``src.gradcam`` lazily so the backend does not fail when PyTorch is absent
    (e.g. in a lightweight production container). Falls back to ``lesion_proxy_png`` on any error.

    Parameters
    ----------
    pil_image : PIL.Image  — the leaf photo (any size)
    leaf_mask  : np.ndarray | None — boolean/float 2-D mask from the severity estimator
    target_class_idx : int — class index to explain (default 0, i.e. the top predicted class)
    dinov2_engine : CropGuardInferenceEngine | None — active engine to reuse loaded backbone

    Returns
    -------
    dict with keys ``method`` (str), ``png_base64`` (str, no data-URI prefix),
    ``rollout_png_base64`` (optional str), ``leaf_overlap_score`` (float),
    ``is_grounded`` (bool), ``is_reliable`` (bool), ``explainability_note`` (str).
    """
    try:
        import sys
        import os
        # Make sure the project root is on sys.path so `src` is importable
        proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        if proj_root not in sys.path:
            sys.path.insert(0, proj_root)

        from src.gradcam import DINOv2GradCAM, LeafOverlapVerifier  # noqa: PLC0415
        import torch  # noqa: PLC0415
        import torch.nn as nn  # noqa: PLC0415

        if dinov2_engine is not None and hasattr(dinov2_engine, "extractor"):
            backbone = dinov2_engine.extractor.model
            device = dinov2_engine.device
            feat_dim = dinov2_engine.extractor.dino_dim
            gcam = dinov2_engine.gradcam_engine
        else:
            backbone = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14", trust_repo=True)
            backbone.eval()
            device = "cpu"
            feat_dim = 384
            gcam = DINOv2GradCAM(backbone, device="cpu")

        # Thin probe head if not passing full classifier head
        head = nn.Linear(feat_dim, max(target_class_idx + 1, 2), bias=False).to(device)
        head.eval()

        # Build mask if none supplied
        if leaf_mask is None:
            mask_np = np.ones((224, 224), dtype=np.uint8) * 255
        else:
            mask_np = np.asarray(leaf_mask, dtype=np.uint8)
            if mask_np.max() <= 1:
                mask_np = (mask_np * 255).astype(np.uint8)

        # Preprocess
        from torchvision import transforms  # noqa: PLC0415
        img_size = getattr(dinov2_engine.extractor, "img_size", 224) if dinov2_engine else 224
        tf = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        tensor = tf(pil_image.convert("RGB")).unsqueeze(0).to(device)

        result = gcam.generate_cam(
            head=head,
            input_tensor=tensor,
            raw_rgb=pil_image,
            leaf_mask=mask_np,
            target_class_idx=target_class_idx,
            compute_rollout=True,
        )

        grounding = {
            "leaf_overlap_score": round(float(result.leaf_overlap_score), 4),
            "is_grounded": bool(result.is_grounded),
            "is_reliable": bool(result.is_reliable),
            "explainability_note": result.status_note,
        }

        png_bytes = DINOv2GradCAM.overlay_to_png_bytes(result.overlay_rgb)
        png_b64 = base64.b64encode(png_bytes).decode()
        out = {"method": "dinov2-gradcam++", "png_base64": png_b64, **grounding}

        if result.rollout_overlay_rgb is not None:
            rollout_bytes = DINOv2GradCAM.overlay_to_png_bytes(result.rollout_overlay_rgb)
            out["rollout_png_base64"] = base64.b64encode(rollout_bytes).decode()
            if result.rollout_overlap_score is not None:
                out["rollout_overlap_score"] = round(float(result.rollout_overlap_score), 4)

        return out

    except Exception as exc:  # noqa: BLE001
        # Graceful fallback — lesion_proxy_png requires a mask array
        fallback_mask = leaf_mask if leaf_mask is not None else np.zeros((224, 224), np.float32)
        out = lesion_proxy_png(fallback_mask)
        out["explainability_note"] = f"Grad-CAM++ unavailable ({type(exc).__name__}); showing lesion proxy."
        return out
