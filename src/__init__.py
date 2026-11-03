"""CropGuard Vision Core Modules."""
from src.localize import LeafLocalizer, LocalizationResult
from src.dataset import TaxonomyRegistry, Deduplicator, HonestSplitter, DatasetSample
from src.augment import BackgroundRandomizer, PhotometricFieldAugmenter
from src.extract_features import DINOv2FeatureExtractor, FeatureCacheEngine

__all__ = [
    "LeafLocalizer",
    "LocalizationResult",
    "TaxonomyRegistry",
    "Deduplicator",
    "HonestSplitter",
    "DatasetSample",
    "BackgroundRandomizer",
    "PhotometricFieldAugmenter",
    "DINOv2FeatureExtractor",
    "FeatureCacheEngine",
]
