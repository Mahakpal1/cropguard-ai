"""Convenience launcher for CropGuard DINOv2 Hierarchical Training.

Usage:
    python ml/train_dinov2_hierarchical.py --data-dirs data/PlantVillage work/plantdoc/train
"""
import os
import sys

# Ensure repository root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.build_and_train import main

if __name__ == "__main__":
    main()
