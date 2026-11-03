"""CropGuard Vision Core Modules."""
from src.localize import LeafLocalizer, LocalizationResult
from src.dataset import TaxonomyRegistry, Deduplicator, HonestSplitter, DatasetSample
from src.augment import BackgroundRandomizer, PhotometricFieldAugmenter
from src.extract_features import DINOv2FeatureExtractor, FeatureCacheEngine
from src.heads import CropClassifierHead, PerCropDiseaseHead, HierarchicalClassifier, HierarchicalPrediction
from src.train import HeadTrainer
from src.calibrate import TemperatureCalibrator, EnergyOODCalibrator, SystemCalibrator
from src.gradcam import vit_reshape_transform, LeafOverlapVerifier, DINOv2GradCAM, ExplainabilityResult
from src.infer import CropGuardInferenceEngine, EndToEndDiagnosis
from src.build_and_train import PipelineBuilder

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
    "CropClassifierHead",
    "PerCropDiseaseHead",
    "HierarchicalClassifier",
    "HierarchicalPrediction",
    "HeadTrainer",
    "TemperatureCalibrator",
    "EnergyOODCalibrator",
    "SystemCalibrator",
    "vit_reshape_transform",
    "LeafOverlapVerifier",
    "DINOv2GradCAM",
    "ExplainabilityResult",
    "CropGuardInferenceEngine",
    "EndToEndDiagnosis",
    "PipelineBuilder",
]
