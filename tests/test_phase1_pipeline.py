"""Tests for Phase 1: Foundation & Data Pipeline.

Verifies:
1. Master taxonomy schema and coverage.
2. Leaf localizer: color segmentation, 15% padding margin, and leaf gate rejection.
3. Deduplication and honest leakage-free splitting.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.dataset import DatasetSample, Deduplicator, HonestSplitter, TaxonomyRegistry
from src.localize import LeafLocalizer, LocalizationResult

ROOT = Path(__file__).resolve().parents[1]


# ── 1. Taxonomy Tests ────────────────────────────────────────────────────────

def test_taxonomy_csv_schema_and_contents():
    tax_path = ROOT / "data" / "taxonomy.csv"
    assert tax_path.exists(), "data/taxonomy.csv does not exist"

    with open(tax_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"source", "raw_folder_name", "canonical_crop", "canonical_disease", "canonical_key", "is_lab", "license"}
        assert required_cols.issubset(set(reader.fieldnames or []))
        rows = list(reader)

    assert len(rows) >= 50, f"Expected at least 50 taxonomy rows, found {len(rows)}"

    sources = {r["source"] for r in rows}
    assert "plantvillage" in sources
    assert "plantdoc" in sources
    assert "rice_dslr" in sources
    assert "generic_negative" in sources

    # Verify negative class mapping
    neg_rows = [r for r in rows if r["canonical_crop"] == "__non_crop__"]
    assert len(neg_rows) >= 1
    assert any(r["canonical_disease"] == "__not_a_leaf__" for r in neg_rows)


def test_taxonomy_registry_lookups():
    tax_path = ROOT / "data" / "taxonomy.csv"
    reg = TaxonomyRegistry(str(tax_path))
    
    # Test known lookup
    info = reg.get_info("plantvillage", "Tomato_Early_blight")
    assert info is not None
    assert info["canonical_crop"] == "Tomato"
    assert info["canonical_disease"] == "Early_Blight"
    assert info["is_lab"] is True

    # Test field lookup
    info_rice = reg.get_info("rice_dslr", "Brown_spot")
    assert info_rice is not None
    assert info_rice["canonical_crop"] == "Rice"
    assert info_rice["canonical_disease"] == "Brown_Spot"
    assert info_rice["is_lab"] is False


# ── 2. Leaf Localizer Tests ──────────────────────────────────────────────────

def test_leaf_localizer_detects_and_crops_green_leaf():
    localizer = LeafLocalizer(margin=0.15, target_size=(224, 224))

    # Create a synthetic 400x400 image: white background with green leaf rectangle in center
    img = np.ones((400, 400, 3), dtype=np.uint8) * 240
    # Paint a green leaf patch from (100, 100) to (250, 260)
    img[100:250, 100:260] = [34, 139, 34]  # Forest Green in BGR
    # Add a yellowish/brown spot inside the leaf patch (simulating lesion)
    img[150:180, 150:180] = [20, 160, 200]

    pil_img = Image.fromarray(img)
    result = localizer.localize(pil_img)

    assert isinstance(result, LocalizationResult)
    assert result.has_leaf is True
    assert result.leaf_coverage_ratio > 0.05
    assert result.cropped_image.size == (224, 224)
    assert result.leaf_mask.shape == (224, 224)

    # Check padding margin: cropped bbox should extend beyond (100, 100, 250, 260)
    ymin, xmin, ymax, xmax = result.original_bbox
    assert ymin <= 100
    assert xmin <= 100
    assert ymax >= 250
    assert xmax >= 260


def test_leaf_localizer_rejects_blank_or_non_leaf():
    localizer = LeafLocalizer(min_leaf_ratio=0.04)

    # Plain gray/white non-leaf surface
    blank = np.ones((300, 300, 3), dtype=np.uint8) * 128
    result = localizer.localize(blank)

    assert result.has_leaf is False
    assert result.leaf_coverage_ratio < 0.04


# ── 3. Deduplication & Honest Splitting Tests ────────────────────────────────

def test_deduplicator_and_honest_splitting():
    # Construct 6 mock samples: 2 pairs of near-duplicates with same pHash, 2 unique
    samples = [
        DatasetSample("p1.jpg", "field1", "Tomato", "Early_Blight", "Tomato___Early_Blight", False, "a1b2c3d4e5f60000", ""),
        DatasetSample("p2.jpg", "field1", "Tomato", "Early_Blight", "Tomato___Early_Blight", False, "a1b2c3d4e5f60000", ""),  # Duplicate of p1
        DatasetSample("p3.jpg", "field1", "Tomato", "Early_Blight", "Tomato___Early_Blight", False, "1111222233334444", ""),
        DatasetSample("p4.jpg", "field2", "Potato", "Late_Blight", "Potato___Late_Blight", False, "ffffffff00000000", ""),
        DatasetSample("p5.jpg", "field2", "Potato", "Late_Blight", "Potato___Late_Blight", False, "ffffffff00000000", ""),  # Duplicate of p4
        DatasetSample("p6.jpg", "field2", "Potato", "Late_Blight", "Potato___Late_Blight", False, "8888888899999999", ""),
    ]

    dedup = Deduplicator(hamming_distance_threshold=3)
    grouped = dedup.group_near_duplicates(samples)

    # Verify duplicates share identical leaf_group_id
    assert grouped[0].leaf_group_id == grouped[1].leaf_group_id
    assert grouped[3].leaf_group_id == grouped[4].leaf_group_id
    assert grouped[0].leaf_group_id != grouped[2].leaf_group_id

    # Test honest splitting
    splitter = HonestSplitter(train_ratio=0.5, val_ratio=0.25, test_ratio=0.25, random_seed=42)
    df_train, df_val, df_test = splitter.split_by_leaf_group(grouped)

    train_groups = set(df_train["leaf_group_id"])
    val_groups = set(df_val["leaf_group_id"])
    test_groups = set(df_test["leaf_group_id"])

    # Crucial guarantee: Zero group leakage across splits
    assert len(train_groups.intersection(val_groups)) == 0
    assert len(train_groups.intersection(test_groups)) == 0
    assert len(val_groups.intersection(test_groups)) == 0
