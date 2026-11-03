"""CropGuard Vision Core Modules."""
from src.localize import LeafLocalizer, LocalizationResult
from src.dataset import TaxonomyRegistry, Deduplicator, HonestSplitter, DatasetSample

__all__ = [
    "LeafLocalizer",
    "LocalizationResult",
    "TaxonomyRegistry",
    "Deduplicator",
    "HonestSplitter",
    "DatasetSample",
]
