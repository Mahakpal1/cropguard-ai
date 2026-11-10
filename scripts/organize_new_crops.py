"""Script to organize downloaded Cauliflower, Banana, and Chilli datasets into canonical raw folders."""
import os
import shutil
from pathlib import Path

BASE_DIR = Path("data/raw")

def organize_cauliflower():
    dest_base = BASE_DIR / "cauliflower_field"
    dest_base.mkdir(parents=True, exist_ok=True)
    
    mapping = {
        "Downy_Mildew": [
            BASE_DIR / "cauliflower_download2" / "Disease_final_Dataset" / "DowneyMildew__",
            BASE_DIR / "cauliflower_download" / "Couliflower_Disease" / "downey mildew",
        ],
        "Alternaria_Leaf_Spot": [
            BASE_DIR / "cauliflower_download2" / "Disease_final_Dataset" / "AlternariaLeafSpot__",
            BASE_DIR / "cauliflower_download" / "Couliflower_Disease" / "Alternaria Leaf Spot",
        ],
        "Black_Rot": [
            BASE_DIR / "cauliflower_download2" / "Disease_final_Dataset" / "BlackRot__",
            BASE_DIR / "cauliflower_download" / "Couliflower_Disease" / "black rot",
        ],
        "Bacterial_Soft_Rot": [
            BASE_DIR / "cauliflower_download2" / "Disease_final_Dataset" / "BacterialSoftRot__",
            BASE_DIR / "cauliflower_download" / "Couliflower_Disease" / "bacterial soft rot",
        ],
        "White_Rust": [
            BASE_DIR / "cauliflower_download2" / "Disease_final_Dataset" / "WhiteRust__",
            BASE_DIR / "cauliflower_download" / "Couliflower_Disease" / "White rust",
        ],
    }
    
    for label, src_dirs in mapping.items():
        out_dir = dest_base / label
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for src in src_dirs:
            if src.exists():
                for img_p in src.glob("*.*"):
                    if img_p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                        target_name = f"{src.name}_{img_p.name}"
                        target_path = out_dir / target_name
                        if not target_path.exists():
                            shutil.copy2(img_p, target_path)
                            count += 1
        print(f"Cauliflower [{label}]: {count} images copied to {out_dir}")

def organize_banana():
    dest_base = BASE_DIR / "banana_field"
    dest_base.mkdir(parents=True, exist_ok=True)
    
    src_base = BASE_DIR / "banana_download" / "BananaLSD" / "OriginalSet"
    mapping = {
        "Sigatoka": src_base / "sigatoka",
        "Cordana": src_base / "cordana",
        "Pestalotiopsis": src_base / "pestalotiopsis",
        "Healthy": src_base / "healthy",
    }
    
    for label, src_dir in mapping.items():
        out_dir = dest_base / label
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        if src_dir.exists():
            for img_p in src_dir.glob("*.*"):
                if img_p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                    target_path = out_dir / img_p.name
                    if not target_path.exists():
                        shutil.copy2(img_p, target_path)
                        count += 1
        print(f"Banana [{label}]: {count} images copied to {out_dir}")

def organize_chilli():
    dest_base = BASE_DIR / "chilli_field"
    dest_base.mkdir(parents=True, exist_ok=True)
    
    curl_dir = dest_base / "Leaf_Curl"
    curl_dir.mkdir(parents=True, exist_ok=True)
    
    healthy_dir = dest_base / "Healthy"
    healthy_dir.mkdir(parents=True, exist_ok=True)
    
    src_roots = [
        BASE_DIR / "chilli_sohan" / "train",
        BASE_DIR / "chilli_sohan" / "valid",
        BASE_DIR / "chilli_sohan" / "test",
    ]
    
    curl_count = 0
    healthy_count = 0
    for sroot in src_roots:
        if not sroot.exists():
            continue
        for f in sroot.glob("*.*"):
            if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                continue
            name_lower = f.name.lower()
            if name_lower.startswith("curly"):
                target = curl_dir / f.name
                if not target.exists():
                    shutil.copy2(f, target)
                    curl_count += 1
            elif name_lower.startswith("healthy"):
                target = healthy_dir / f.name
                if not target.exists():
                    shutil.copy2(f, target)
                    healthy_count += 1
                    
    print(f"Chilli [Leaf_Curl]: {curl_count} images copied")
    print(f"Chilli [Healthy]: {healthy_count} images copied")

if __name__ == "__main__":
    organize_cauliflower()
    organize_banana()
    organize_chilli()
