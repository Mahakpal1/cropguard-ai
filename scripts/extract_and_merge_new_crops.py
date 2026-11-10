"""Extract DINOv2 ViT-L/14 features for newly added crops (Cauliflower, Banana, Chilli)
and merge them into the cached feature .npz files for instant training.
"""
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from src.dataset import TaxonomyRegistry
from src.extract_features import DINOv2FeatureExtractor
from src.localize import LeafLocalizer

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("merge_features")

TAXONOMY_PATH = Path("data/taxonomy.csv")
CACHE_DIR = Path("data/cached_features")
RAW_DIR = Path("data/raw")
MODEL_NAME = "dinov2_vitl14"

NEW_CROP_DIRS = [
    RAW_DIR / "cauliflower_field",
    RAW_DIR / "banana_field",
    RAW_DIR / "chilli_field",
]

def collect_new_samples(registry: TaxonomyRegistry):
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    samples = []
    
    for cdir in NEW_CROP_DIRS:
        if not cdir.exists():
            continue
        source_name = cdir.name
        for sub in cdir.iterdir():
            if not sub.is_dir():
                continue
            folder_name = sub.name
            info = registry.get_info(source=source_name, raw_folder=folder_name)
            if not info:
                logger.warning(f"No taxonomy info for {source_name}/{folder_name}")
                continue
            
            imgs = [f for f in sub.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
            for img_p in imgs:
                samples.append({
                    "image_path": str(img_p),
                    "crop": info["canonical_crop"],
                    "disease": info["canonical_disease"],
                    "canonical_key": info["canonical_key"],
                    "is_lab": info["is_lab"],
                    "source": info["source"],
                })
    return samples

def extract_features_for_samples(samples: List[dict], device="cuda"):
    logger.info(f"Loading DINOv2 extractor on {device}...")
    extractor = DINOv2FeatureExtractor(model_name=MODEL_NAME, device=device)
    localizer = LeafLocalizer()
    
    features = []
    batch_imgs = []
    batch_indices = []
    batch_size = 32
    
    logger.info(f"Extracting features for {len(samples)} images...")
    for idx, s in enumerate(tqdm(samples, desc="Extracting")):
        try:
            with Image.open(s["image_path"]) as img:
                loc_res = localizer.localize(img)
                leaf_img = loc_res.cropped_image
                batch_imgs.append(leaf_img)
                batch_indices.append(idx)
        except Exception as e:
            logger.warning(f"Failed to process {s['image_path']}: {e}")
            continue
            
        if len(batch_imgs) >= batch_size or idx == len(samples) - 1:
            if batch_imgs:
                feats = extractor.extract_batch(batch_imgs)
                features.append(feats)
                batch_imgs = []
                batch_indices = []
                
    if features:
        features = np.vstack(features)
    else:
        features = np.zeros((0, 1024), dtype=np.float32)
        
    return features

def split_samples(samples, features, train_ratio=0.70, val_ratio=0.15):
    np.random.seed(42)
    # Stratified split by canonical_key
    key_to_indices = {}
    for i, s in enumerate(samples):
        key_to_indices.setdefault(s["canonical_key"], []).append(i)
        
    train_idx, val_idx, test_idx = [], [], []
    for key, idxs in key_to_indices.items():
        idxs = np.array(idxs)
        np.random.shuffle(idxs)
        n = len(idxs)
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio)) if n > 3 else 1
        
        train_idx.extend(idxs[:n_train])
        val_idx.extend(idxs[n_train:n_train + n_val])
        test_idx.extend(idxs[n_train + n_val:])
        
    logger.info(f"New samples split: Train={len(train_idx)}, Val={len(val_idx)}, Test={len(test_idx)}")
    return train_idx, val_idx, test_idx

def merge_and_save_caches(samples, features, train_idx, val_idx, test_idx):
    splits = [
        ("train", train_idx),
        ("val", val_idx),
        ("test", test_idx),
    ]
    
    # 1. Load existing caches to build unified taxonomy and indices
    cache_files = {
        split: CACHE_DIR / f"cropguard_{split}_{MODEL_NAME}.npz"
        for split in ["train", "val", "test"]
    }
    
    # Back up existing files
    for split, p in cache_files.items():
        bak = CACHE_DIR / f"cropguard_{split}_{MODEL_NAME}.npz.bak"
        if p.exists() and not bak.exists():
            shutil.copy2(p, bak)
            logger.info(f"Backed up {p.name} to {bak.name}")
            
    # Collect all crops and diseases
    base_train = np.load(cache_files["train"], allow_pickle=True)
    existing_crop_to_idx = json.loads(str(base_train["crop_to_idx_json"]))
    existing_disease_to_idx = json.loads(str(base_train["disease_to_idx_json"]))
    existing_crop_disease_map = json.loads(str(base_train["crop_disease_map_json"]))
    
    # Add new crops and diseases
    all_crops = set(existing_crop_to_idx.keys())
    all_diseases = set(existing_disease_to_idx.keys())
    unified_crop_disease_map = {k: set(v) for k, v in existing_crop_disease_map.items()}
    
    for s in samples:
        c = s["crop"]
        d = s["disease"]
        all_crops.add(c)
        all_diseases.add(d)
        unified_crop_disease_map.setdefault(c, set()).add(d)
        
    # Canonical sorting: '__non_crop__' always at the end
    sorted_crops = sorted([c for c in all_crops if c != "__non_crop__"])
    if "__non_crop__" in all_crops:
        sorted_crops.append("__non_crop__")
        
    crop_to_idx = {c: i for i, c in enumerate(sorted_crops)}
    disease_to_idx = {d: i for i, d in enumerate(sorted(all_diseases))}
    unified_crop_disease_map = {k: sorted(list(v)) for k, v in unified_crop_disease_map.items()}
    
    logger.info(f"Total unified crops: {len(crop_to_idx)} (added Cauliflower, Banana, Chilli)")
    logger.info(f"Total unified diseases: {len(disease_to_idx)}")
    
    for split, s_idx in splits:
        cache_path = cache_files[split]
        existing = np.load(cache_path, allow_pickle=True)
        
        # Remap existing crop_labels and disease_labels to new unified indices
        old_crop_to_idx = json.loads(str(existing["crop_to_idx_json"]))
        old_idx_to_crop = {v: k for k, v in old_crop_to_idx.items()}
        remapped_crop_labels = np.array([
            crop_to_idx[old_idx_to_crop[orig_idx]]
            for orig_idx in existing["crop_labels"]
        ], dtype=np.int64)
        
        old_dis_to_idx = json.loads(str(existing["disease_to_idx_json"]))
        old_idx_to_dis = {v: k for k, v in old_dis_to_idx.items()}
        remapped_disease_labels = np.array([
            disease_to_idx[old_idx_to_dis[orig_idx]]
            for orig_idx in existing["disease_labels"]
        ], dtype=np.int64)
        
        # New slice data
        sub_samples = [samples[i] for i in s_idx]
        new_feats = features[s_idx]
        new_crop_labels = np.array([crop_to_idx[s["crop"]] for s in sub_samples], dtype=np.int64)
        new_disease_labels = np.array([disease_to_idx[s["disease"]] for s in sub_samples], dtype=np.int64)
        new_keys = np.array([s["canonical_key"] for s in sub_samples], dtype=object)
        new_is_lab = np.array([s["is_lab"] for s in sub_samples], dtype=bool)
        new_sources = np.array([s["source"] for s in sub_samples], dtype=object)
        new_leaf_groups = np.array([f"new_{split}_{i}" for i in range(len(sub_samples))], dtype=object)
        
        # Concatenate
        merged_feats = np.vstack([existing["features"], new_feats]).astype(np.float32)
        merged_crop_labels = np.concatenate([remapped_crop_labels, new_crop_labels])
        merged_disease_labels = np.concatenate([remapped_disease_labels, new_disease_labels])
        merged_keys = np.concatenate([existing["canonical_keys"], new_keys])
        merged_is_lab = np.concatenate([existing["is_lab"], new_is_lab])
        merged_sources = np.concatenate([existing["source_ids"], new_sources])
        merged_leaf_groups = np.concatenate([existing["leaf_group_ids"], new_leaf_groups])
        
        logger.info(f"Saving merged {split} cache: {merged_feats.shape[0]} total samples -> {cache_path}")
        np.savez_compressed(
            cache_path,
            features=merged_feats,
            crop_labels=merged_crop_labels,
            disease_labels=merged_disease_labels,
            canonical_keys=merged_keys,
            is_lab=merged_is_lab,
            source_ids=merged_sources,
            leaf_group_ids=merged_leaf_groups,
            crop_to_idx_json=json.dumps(crop_to_idx),
            disease_to_idx_json=json.dumps(disease_to_idx),
            crop_disease_map_json=json.dumps(unified_crop_disease_map),
        )

def main():
    registry = TaxonomyRegistry(str(TAXONOMY_PATH))
    samples = collect_new_samples(registry)
    logger.info(f"Collected {len(samples)} valid new samples.")
    
    features = extract_features_for_samples(samples, device="cuda" if torch.cuda.is_available() else "cpu")
    train_idx, val_idx, test_idx = split_samples(samples, features)
    merge_and_save_caches(samples, features, train_idx, val_idx, test_idx)
    logger.info("Feature extraction and cache merge completed successfully!")

if __name__ == "__main__":
    main()
