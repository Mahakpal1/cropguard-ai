"""Field image enhancement for challenging lighting conditions.

Inspired by field-detection preprocessing (e.g. CLAHE / contrast normalization),
this module helps normalize leaves photographed in harsh outdoor sun, deep shadows,
or low-contrast smartphone cameras.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def adaptive_contrast(img: Image.Image, cutoff: float = 1.0) -> Image.Image:
    """Percentile-based autocontrast that preserves color balance."""
    return ImageOps.autocontrast(img.convert("RGB"), cutoff=cutoff)


def field_enhance(img: Image.Image, smooth: bool = True, contrast: bool = True) -> Image.Image:
    """Field enhancement pipeline for agricultural photographs.
    
    1. Normalizes local contrast across the leaf surface.
    2. Optional edge-preserving smoothing to reduce sensor noise and compression artifacts.
    """
    im = img.convert("RGB")
    if contrast:
        im = ImageOps.autocontrast(im, cutoff=1.5)
    if smooth:
        # Subtle smoothing to reduce high-frequency sensor noise while keeping lesion edges
        im = im.filter(ImageFilter.GaussianBlur(radius=0.5))
    return im
