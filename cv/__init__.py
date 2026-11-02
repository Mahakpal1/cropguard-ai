"""CropGuard computer-vision helpers (leaf segmentation and severity). Pure numpy + Pillow."""
from .segmentation import rgb_to_hsv, leaf_mask, lesion_mask, to_rgb  # noqa: F401
from .severity import estimate, level_for, DEFAULT_BINS  # noqa: F401
