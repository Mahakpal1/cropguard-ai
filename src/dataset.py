"""Dataset Pipeline and Deduplication Manager for CropGuard.

Implements:
1. Canonical taxonomy matching against data/taxonomy.csv.
2. Perceptual hashing (pHash) deduplication to cluster burst shots and near-duplicate leaves.
3. Honest split generation: Grouped by leaf/hash cluster and source dataset to prevent leakage.
4. Leave-One-Dataset-Out (LODO) split generation for rigorous cross-domain field evaluation.
"""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import imagehash
import numpy as np
import pandas as pd
from PIL import Image

logger = logging.getLogger("cropguard.dataset")


@dataclass
class DatasetSample:
    image_path: str
    source: str
    canonical_crop: str
    canonical_disease: str
    canonical_key: str
    is_lab: bool
    phash: str
    leaf_group_id: str


class TaxonomyRegistry:
    """Manages mapping between raw source folder names and canonical crop/disease labels."""

    def __init__(self, taxonomy_path: str = "data/taxonomy.csv"):
        self.taxonomy_path = Path(taxonomy_path)
        self.mappings: Dict[Tuple[str, str], Dict[str, str]] = {}
        self.crops: Set[str] = set()
        self.diseases: Set[str] = set()
        self._load()

    def _load(self):
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found at {self.taxonomy_path}")

        df = pd.read_csv(self.taxonomy_path)
        for _, row in df.iterrows():
            source = str(row["source"]).strip().lower()
            raw_folder = str(row["raw_folder_name"]).strip()
            self.mappings[(source, raw_folder)] = {
                "canonical_crop": str(row["canonical_crop"]).strip(),
                "canonical_disease": str(row["canonical_disease"]).strip(),
                "canonical_key": str(row["canonical_key"]).strip(),
                "is_lab": str(row["is_lab"]).strip().lower() in ("true", "1", "yes"),
                "license": str(row.get("license", "unknown")).strip(),
                "scientific_name": str(row.get("scientific_name", "")).strip(),
            }
            self.crops.add(str(row["canonical_crop"]).strip())
            self.diseases.add(str(row["canonical_disease"]).strip())

    def get_info(self, source: str, raw_folder: str) -> Optional[Dict[str, str]]:
        key = (source.strip().lower(), raw_folder.strip())
        if key in self.mappings:
            return self.mappings[key]
        # Fallback: check without source if unambiguous
        matches = [v for k, v in self.mappings.items() if k[1] == raw_folder.strip()]
        if len(matches) == 1:
            return matches[0]
        return None


class Deduplicator:
    """Detects duplicate and near-duplicate images using 64-bit DCT perceptual hashing."""

    def __init__(self, hamming_distance_threshold: int = 4):
        self.threshold = hamming_distance_threshold

    @staticmethod
    def compute_phash(image_path: Union[str, Path]) -> str:
        """Compute 64-bit perceptual hash."""
        try:
            with Image.open(image_path) as img:
                return str(imagehash.phash(img.convert("RGB")))
        except Exception as e:
            logger.warning(f"Failed to compute pHash for {image_path}: {e}")
            return "0000000000000000"

    def group_near_duplicates(self, samples: List[DatasetSample]) -> List[DatasetSample]:
        """
        Group near-duplicate samples (Hamming distance <= threshold) under a common leaf_group_id.
        Uses Union-Find connected components to prevent leakage of the same leaf across splits.
        """
        n = len(samples)
        parent = list(range(n))

        def find(i: int) -> int:
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        def union(i: int, j: int):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_j] = root_i

        # Convert hex pHashes to imagehash objects for fast hamming distance
        hash_objs = []
        for s in samples:
            try:
                hash_objs.append(imagehash.hex_to_hash(s.phash))
            except Exception:
                hash_objs.append(None)

        # Pairwise comparison within the same canonical class
        # (reduces O(N^2) comparison space to only within-class pairs)
        class_buckets: Dict[str, List[int]] = {}
        for idx, s in enumerate(samples):
            class_buckets.setdefault(s.canonical_key, []).append(idx)

        for _, indices in class_buckets.items():
            k = len(indices)
            for a in range(k):
                idx_a = indices[a]
                hash_a = hash_objs[idx_a]
                if hash_a is None:
                    continue
                for b in range(a + 1, k):
                    idx_b = indices[b]
                    hash_b = hash_objs[idx_b]
                    if hash_b is None:
                        continue
                    if (hash_a - hash_b) <= self.threshold:
                        union(idx_a, idx_b)

        # Assign unified leaf_group_id
        for idx, s in enumerate(samples):
            root_id = find(idx)
            s.leaf_group_id = f"leaf_grp_{root_id:06d}"

        return samples


class HonestSplitter:
    """
    Creates leakage-free train/val/test splits grouped by leaf_group_id,
    and Leave-One-Dataset-Out (LODO) cross-domain splits.
    """

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.rng = np.random.RandomState(random_seed)

    def split_by_leaf_group(self, samples: List[DatasetSample]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split dataset into train, val, test such that all images belonging
        to the same leaf_group_id reside strictly in ONE split.
        """
        df = pd.DataFrame([s.__dict__ for s in samples])
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Group by canonical_key and leaf_group_id
        unique_groups = df.groupby(["canonical_key", "leaf_group_id"]).size().reset_index()

        train_groups = set()
        val_groups = set()
        test_groups = set()

        for canonical_key, group_sub in unique_groups.groupby("canonical_key"):
            group_ids = group_sub["leaf_group_id"].tolist()
            self.rng.shuffle(group_ids)
            n = len(group_ids)

            n_train = max(1, int(n * self.train_ratio))
            n_val = int(n * self.val_ratio)

            train_groups.update(group_ids[:n_train])
            val_groups.update(group_ids[n_train:n_train + n_val])
            test_groups.update(group_ids[n_train + n_val:])

        df_train = df[df["leaf_group_id"].isin(train_groups)].copy()
        df_val = df[df["leaf_group_id"].isin(val_groups)].copy()
        df_test = df[df["leaf_group_id"].isin(test_groups)].copy()

        df_train["split"] = "train"
        df_val["split"] = "val"
        df_test["split"] = "test"

        return df_train, df_val, df_test

    @staticmethod
    def generate_lodo_splits(df: pd.DataFrame, out_path: str = "data/splits/lodo_splits.json"):
        """
        Generate Leave-One-Dataset-Out (LODO) cross-domain folds.
        For each distinct source dataset, holds it out as the test set while training on all others.
        """
        sources = df["source"].unique().tolist()
        lodo = {}

        for test_source in sources:
            train_sources = [s for s in sources if s != test_source]
            lodo[f"holdout_{test_source}"] = {
                "test_source": test_source,
                "train_sources": train_sources,
                "test_count": int((df["source"] == test_source).sum()),
                "train_count": int((df["source"] != test_source).sum()),
            }

        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(lodo, f, indent=2)

        return lodo
