"""
CropGuard Dataset Downloader
Downloads all Indian crop disease datasets to data/raw/

Sources:
  1. MangoLeafBD - GitHub (pypi-ahmad)
  2. Sugarcane - GitHub (sabidarrow)
  3. Wheat field - GitHub (multiple sources)
  4. Cotton - GitHub (gallayagnesh)
  5. Groundnut/Peanut - GitHub (vipoooool)
  6. Rice additional classes
  7. Generic negatives (iNaturalist-style)
"""

import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import io
import shutil
import zipfile
import urllib.request
import urllib.error
import hashlib
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

CHUNK = 1 << 20  # 1 MB


def download(url: str, dest: Path, desc: str = "") -> bool:
    """Download a URL to dest with progress. Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n⬇  {desc or url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cropguard-downloader/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            while True:
                chunk = r.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    mb = downloaded / 1e6
                    print(f"\r   {pct:3d}% ({mb:.1f} MB)", end="", flush=True)
        print(f"\r   ✓ {downloaded/1e6:.1f} MB saved to {dest.name}")
        return True
    except Exception as e:
        print(f"\n   ✗ FAILED: {e}")
        if dest.exists():
            dest.unlink()
        return False


def extract_zip_folder(zip_path: Path, src_prefix: str, dst: Path, exts: set = {".jpg", ".jpeg", ".png"}):
    """Extract files matching src_prefix from zip to dst, preserving one level of class subfolders."""
    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.startswith(src_prefix) and not n.endswith("/")]
        count = 0
        for name in names:
            ext = Path(name).suffix.lower()
            if ext not in exts:
                continue
            # relative path after prefix
            rel = name[len(src_prefix):]
            dst_file = dst / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as src_f, open(dst_file, "wb") as out_f:
                shutil.copyfileobj(src_f, out_f)
            count += 1
    print(f"   ✓ Extracted {count} files → {dst}")
    return count


# ─────────────────────────────────────────────────────────────────────────────
# 1. MANGOLEAFBD
# ─────────────────────────────────────────────────────────────────────────────
def download_mango():
    dest = RAW / "mangoleafbd"
    if dest.exists() and any(dest.iterdir()):
        imgs = sum(1 for _ in dest.rglob("*.jpg"))
        print(f"✓ mangoleafbd already present ({imgs} jpg images)")
        return

    zip_path = ROOT / "data" / "_tmp_mango.zip"
    url = "https://github.com/pypi-ahmad/Mango-Leaf-Disease-Prediction/archive/refs/heads/main.zip"
    if not download(url, zip_path, "MangoLeafBD (~109MB)"):
        # Fallback: try alternative
        url2 = "https://github.com/SabbirAhmad26/MangoLeafBD/archive/refs/heads/main.zip"
        if not download(url2, zip_path, "MangoLeafBD (fallback)"):
            print("   ✗ MangoLeafBD download failed. Download manually from:")
            print("     https://www.kaggle.com/datasets/aryashah2k/mango-leaf-disease-dataset")
            return

    # Extract from: Mango-Leaf-Disease-Prediction-main/data/MangoLeafBD Dataset/{class}/*.jpg
    print("   Extracting MangoLeafBD...")
    prefix_candidates = [
        "Mango-Leaf-Disease-Prediction-main/data/MangoLeafBD Dataset/",
        "Mango-Leaf-Disease-Prediction-main/data/MangoLeafBD_Dataset/",
        "MangoLeafBD-main/Dataset/",
        "MangoLeafBD-main/data/",
    ]
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()
        # auto-detect prefix
        detected = None
        for pref in prefix_candidates:
            if any(n.startswith(pref) for n in all_names):
                detected = pref
                break
        if not detected:
            # scan for jpg files and find common path
            jpg_names = [n for n in all_names if n.lower().endswith(".jpg")]
            if jpg_names:
                # find deepest common path that has class subdirs
                parts = jpg_names[0].split("/")
                print(f"   Sample path: {jpg_names[0]}")
                print(f"   Showing first 10 entries: {all_names[:10]}")
                detected = "/".join(parts[:3]) + "/"

        if detected:
            extract_zip_folder(zip_path, detected, dest)
        else:
            print("   ✗ Could not detect MangoLeafBD folder structure in zip. Listing top entries:")
            for n in all_names[:20]:
                print(f"      {n}")

    zip_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. SUGARCANE (YOLOv8 → classification)
# ─────────────────────────────────────────────────────────────────────────────
def download_sugarcane():
    dest = RAW / "sugarcane_field"
    if dest.exists() and any(dest.iterdir()):
        imgs = sum(1 for _ in dest.rglob("*.jpg")) + sum(1 for _ in dest.rglob("*.png"))
        print(f"✓ sugarcane_field already present ({imgs} images)")
        return

    # Try multiple GitHub repos for sugarcane
    sources = [
        (
            "https://github.com/sabidarrow/Sugarcane-Disease-Dataset/archive/refs/heads/main.zip",
            "sabidarrow/Sugarcane-Disease-Dataset",
            "sugarcane_sabidarrow.zip"
        ),
        (
            "https://github.com/imvab/sugarcane-disease-detection/archive/refs/heads/main.zip",
            "imvab/sugarcane-disease-detection",
            "sugarcane_imvab.zip"
        ),
    ]

    zip_path = None
    for url, repo, fname in sources:
        zp = ROOT / "data" / f"_tmp_{fname}"
        if download(url, zp, f"Sugarcane ({repo})"):
            zip_path = zp
            break

    if not zip_path:
        print("   ✗ Sugarcane: all sources failed.")
        return

    print("   Extracting Sugarcane...")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()
        print(f"   First 30 zip entries:")
        for n in all_names[:30]:
            print(f"      {n}")

        # Try to find inner zip first (common pattern)
        inner_zips = [n for n in all_names if n.endswith(".zip") and "sg" in n.lower()]
        if inner_zips:
            print(f"   Found inner zip: {inner_zips[0]}")
            inner_bytes = z.read(inner_zips[0])
            with zipfile.ZipFile(io.BytesIO(inner_bytes)) as iz:
                iz_names = iz.namelist()
                print(f"   Inner zip entries (first 20): {iz_names[:20]}")
                _extract_sugarcane_yolo(iz, iz_names, dest)
        else:
            # Direct structure
            _extract_sugarcane_yolo(z, all_names, dest)

    zip_path.unlink(missing_ok=True)


def _extract_sugarcane_yolo(z_obj, names, dest: Path):
    """Extract images from a YOLOv8 zip (train/images/, test/images/),
    using label files to assign class folders."""
    import re

    # Collect images and labels
    img_map = {}  # stem → zip_name
    lbl_map = {}  # stem → zip_name

    for n in names:
        p = n.lower()
        if "/images/" in p and not n.endswith("/"):
            ext = Path(n).suffix.lower()
            if ext in {".jpg", ".jpeg", ".png"}:
                stem = Path(n).stem
                img_map[stem] = n
        elif "/labels/" in p and n.endswith(".txt"):
            stem = Path(n).stem
            lbl_map[stem] = n

    # Class mapping for sugarcane: 0=Bacterial_Blight, 1=Healthy, 2=Red_Rot
    # (from YOLOv8 data.yaml if available, else guess)
    class_names = ["Bacterial_Blight", "Healthy", "Red_Rot"]
    # Check for data.yaml
    yaml_names = [n for n in names if "data.yaml" in n.lower() or "classes.txt" in n.lower()]
    if yaml_names:
        try:
            content = z_obj.read(yaml_names[0]).decode("utf-8", errors="replace")
            print(f"   data.yaml content:\n{content[:500]}")
            # Try parse names
            import re
            m = re.search(r"names:\s*\[(.*?)\]", content, re.DOTALL)
            if m:
                parsed = [x.strip().strip("'\"") for x in m.group(1).split(",")]
                if parsed:
                    class_names = [c.replace(" ", "_") for c in parsed]
            else:
                # Try list format
                found = re.findall(r"-\s*(.+)", content)
                if found:
                    class_names = [c.strip().replace(" ", "_") for c in found]
        except Exception as e:
            print(f"   Warning: couldn't parse data.yaml: {e}")

    print(f"   Class names: {class_names}")

    count = 0
    unclassified = 0
    for stem, img_name in img_map.items():
        if stem in lbl_map:
            lbl_content = z_obj.read(lbl_map[stem]).decode("utf-8", errors="replace").strip()
            if lbl_content:
                # Get first class ID from first line
                first_class = int(lbl_content.split("\n")[0].split()[0])
                cls_name = class_names[first_class] if first_class < len(class_names) else f"class_{first_class}"
            else:
                cls_name = "Healthy"  # empty label = healthy
        else:
            cls_name = "Unknown"
            unclassified += 1

        out_path = dest / cls_name / Path(img_name).name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with z_obj.open(img_name) as src:
            with open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        count += 1

    print(f"   ✓ Extracted {count} sugarcane images ({unclassified} unclassified)")


# ─────────────────────────────────────────────────────────────────────────────
# 3. WHEAT FIELD DATASET
# ─────────────────────────────────────────────────────────────────────────────
def download_wheat():
    dest = RAW / "wheat_field"
    if dest.exists() and any(dest.iterdir()):
        imgs = sum(1 for _ in dest.rglob("*.jpg")) + sum(1 for _ in dest.rglob("*.png")) + sum(1 for _ in dest.rglob("*.JPG"))
        print(f"✓ wheat_field already present ({imgs} images)")
        return

    sources = [
        (
            "https://github.com/AhmadManzoor/Wheat-Leaf-Disease-Detection/archive/refs/heads/main.zip",
            "AhmadManzoor wheat leaf detection"
        ),
        (
            "https://github.com/ChinaWheatLeaf/Wheat-leaf-disease/archive/refs/heads/main.zip",
            "ChinaWheatLeaf"
        ),
        (
            "https://github.com/imjai/Wheat-Rust-Disease-Classification/archive/refs/heads/main.zip",
            "imjai wheat rust"
        ),
    ]

    zip_path = None
    for url, desc in sources:
        zp = ROOT / "data" / "_tmp_wheat.zip"
        if download(url, zp, desc):
            zip_path = zp
            break

    if not zip_path:
        print("   ✗ Wheat: all GitHub sources failed. Please download manually from:")
        print("     https://www.kaggle.com/datasets/nirmalsankalana/wheat-leaf-disease-dataset")
        print("     Then extract to data/raw/wheat_field/{Yellow_Rust,Brown_Rust,Healthy,...}/")
        return

    print("   Extracting Wheat...")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()
        print(f"   First 30 zip entries:")
        for n in all_names[:30]:
            print(f"      {n}")

        # Look for class folders containing images
        img_names = [n for n in all_names if Path(n).suffix.lower() in {".jpg", ".jpeg", ".png", ".JPG"} and not n.endswith("/")]
        if img_names:
            # Find common classification structure
            for img_n in img_names[:5]:
                print(f"   Sample: {img_n}")

            # Map known wheat disease names to canonical
            wheat_class_map = {
                "yellowrust": "Yellow_Rust", "yellow_rust": "Yellow_Rust", "stripe_rust": "Yellow_Rust",
                "brownrust": "Brown_Rust", "brown_rust": "Brown_Rust", "leaf_rust": "Brown_Rust",
                "stemrust": "Stem_Rust", "stem_rust": "Stem_Rust",
                "powdery": "Powdery_Mildew", "powdery_mildew": "Powdery_Mildew",
                "septoria": "Septoria", "septoria_leaf": "Septoria",
                "healthy": "Healthy", "normal": "Healthy",
            }

            count = 0
            for img_n in img_names:
                parts = Path(img_n).parts
                # folder name that contains the image = class
                if len(parts) >= 2:
                    folder = parts[-2].lower().replace(" ", "_").replace("-", "_")
                    cls_name = wheat_class_map.get(folder, folder.replace("_", "_").title())
                    out_path = dest / cls_name / Path(img_n).name
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(img_n) as src:
                        with open(out_path, "wb") as dst_f:
                            shutil.copyfileobj(src, dst_f)
                    count += 1
            print(f"   ✓ Extracted {count} wheat images")
        else:
            print("   ✗ No images found in wheat zip")

    zip_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. COTTON DATASET
# ─────────────────────────────────────────────────────────────────────────────
def download_cotton():
    dest = RAW / "cotton_field"
    if dest.exists() and any(dest.iterdir()):
        imgs = sum(1 for _ in dest.rglob("*.jpg")) + sum(1 for _ in dest.rglob("*.png")) + sum(1 for _ in dest.rglob("*.JPG"))
        print(f"✓ cotton_field already present ({imgs} images)")
        return

    sources = [
        (
            "https://github.com/gallayagnesh/cotton_crop_disease_detection_using_SWIN_transformers/archive/refs/heads/main.zip",
            "gallayagnesh cotton SWIN"
        ),
        (
            "https://github.com/Md-Emon-Hasan/Cotton-Disease-Detection-Web-App/archive/refs/heads/main.zip",
            "Md-Emon-Hasan cotton"
        ),
    ]

    zip_path = None
    for url, desc in sources:
        zp = ROOT / "data" / "_tmp_cotton.zip"
        if download(url, zp, desc):
            zip_path = zp
            break

    if not zip_path:
        print("   ✗ Cotton: all sources failed. Please download manually from:")
        print("     https://www.kaggle.com/datasets/janmejaybhoi/cotton-disease-dataset")
        print("     Then extract to data/raw/cotton_field/{Bacterial_Blight,Curl_Virus,Healthy}/")
        return

    print("   Extracting Cotton...")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()
        print(f"   First 30 zip entries:")
        for n in all_names[:30]:
            print(f"      {n}")

        cotton_class_map = {
            "bacterial_blight": "Bacterial_Blight", "bacterialblight": "Bacterial_Blight",
            "curl_virus": "Curl_Virus", "curlvirus": "Curl_Virus", "leaf_curl": "Curl_Virus", "leafcurl": "Curl_Virus",
            "fusarium_wilt": "Fusarium_Wilt", "fusariumwilt": "Fusarium_Wilt",
            "healthy": "Healthy", "fresh": "Healthy",
            "diseased": "Curl_Virus",  # fallback for 2-class datasets
        }

        img_names = [n for n in all_names if Path(n).suffix.lower() in {".jpg", ".jpeg", ".png"} and not n.endswith("/")]
        if img_names:
            for img_n in img_names[:3]:
                print(f"   Sample: {img_n}")
            count = 0
            for img_n in img_names:
                parts = Path(img_n).parts
                if len(parts) >= 2:
                    folder = parts[-2].lower().replace(" ", "_").replace("-", "_")
                    cls_name = cotton_class_map.get(folder, folder.title())
                    out_path = dest / cls_name / Path(img_n).name
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(img_n) as src:
                        with open(out_path, "wb") as df:
                            shutil.copyfileobj(src, df)
                    count += 1
            print(f"   ✓ Extracted {count} cotton images")
        else:
            print("   ✗ No images in cotton zip")

    zip_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. GROUNDNUT / PEANUT DATASET
# ─────────────────────────────────────────────────────────────────────────────
def download_groundnut():
    dest = RAW / "groundnut_field"
    if dest.exists() and any(dest.iterdir()):
        imgs = sum(1 for _ in dest.rglob("*.jpg")) + sum(1 for _ in dest.rglob("*.png"))
        print(f"✓ groundnut_field already present ({imgs} images)")
        return

    sources = [
        (
            "https://github.com/vipoooool/Peanut-Disease-Dataset/archive/refs/heads/main.zip",
            "vipoooool Peanut-Disease-Dataset"
        ),
        (
            "https://github.com/wfcyliyuheng-dev/PD40-Dataset/archive/refs/heads/main.zip",
            "wfcyliyuheng-dev PD40 groundnut"
        ),
        (
            "https://github.com/Sugi-Piyumal/Groundnut-Leaf-Disease-Detection/archive/refs/heads/main.zip",
            "Sugi-Piyumal groundnut"
        ),
    ]

    zip_path = None
    for url, desc in sources:
        zp = ROOT / "data" / "_tmp_groundnut.zip"
        if download(url, zp, desc):
            zip_path = zp
            break

    if not zip_path:
        print("   ✗ Groundnut: all sources failed. Please download manually from:")
        print("     https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset")
        print("     (use any groundnut/peanut dataset available)")
        return

    print("   Extracting Groundnut...")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()
        print(f"   First 30 zip entries:")
        for n in all_names[:30]:
            print(f"      {n}")

        gn_class_map = {
            "early_leaf_spot": "Early_Leaf_Spot", "early_spot": "Early_Leaf_Spot",
            "late_leaf_spot": "Late_Leaf_Spot", "late_spot": "Late_Leaf_Spot",
            "rust": "Rust",
            "bud_necrosis": "Bud_Necrosis",
            "rosette": "Rosette",
            "healthy": "Healthy", "normal": "Healthy",
            "nutrition_deficiency": "Bud_Necrosis",  # map similar
        }

        img_names = [n for n in all_names if Path(n).suffix.lower() in {".jpg", ".jpeg", ".png"} and not n.endswith("/")]
        if img_names:
            for img_n in img_names[:3]:
                print(f"   Sample: {img_n}")
            count = 0
            for img_n in img_names:
                parts = Path(img_n).parts
                if len(parts) >= 2:
                    folder = parts[-2].lower().replace(" ", "_").replace("-", "_")
                    cls_name = gn_class_map.get(folder, folder.title())
                    out_path = dest / cls_name / Path(img_n).name
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(img_n) as src:
                        with open(out_path, "wb") as df:
                            shutil.copyfileobj(src, df)
                    count += 1
            print(f"   ✓ Extracted {count} groundnut images")
        else:
            print("   ✗ No images in groundnut zip")

    zip_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. RICE ADDITIONAL CLASSES (Healthy + extras via IRRI)
# ─────────────────────────────────────────────────────────────────────────────
def download_rice_extra():
    dest = RAW / "rice_dslr"
    healthy = dest / "healthy"
    if healthy.exists() and any(healthy.iterdir()):
        print(f"✓ rice_dslr/healthy already present")
        return

    sources = [
        (
            "https://github.com/nscalo/paddy-disease-dataset/archive/refs/heads/main.zip",
            "nscalo paddy-disease-dataset",
            "paddy-disease-dataset"
        ),
        (
            "https://github.com/GuhaPranav09/Rice-Plant-Disease-Detection/archive/refs/heads/main.zip",
            "GuhaPranav09 rice disease",
            "rice_guha"
        ),
    ]

    for url, desc, prefix_hint in sources:
        zp = ROOT / "data" / f"_tmp_{prefix_hint}.zip"
        if not download(url, zp, desc):
            continue

        print(f"   Extracting {desc}...")
        rice_class_map = {
            "healthy": "healthy", "normal": "healthy",
            "blast": "Leaf_blast", "leaf_blast": "Leaf_blast",
            "brown_spot": "Brown_spot", "brownspot": "Brown_spot",
            "bacterial_leaf_blight": "Bacterial_leaf_blight", "bacterial_blight": "Bacterial_leaf_blight",
            "leaf_scald": "Leaf_scald", "sheath_blight": "Sheath_blight",
            "tungro": "Tungro", "hispa": "Hispa",
        }

        with zipfile.ZipFile(zp) as z:
            all_names = z.namelist()
            print(f"   First 20 entries: {all_names[:20]}")
            img_names = [n for n in all_names if Path(n).suffix.lower() in {".jpg", ".jpeg", ".png"} and not n.endswith("/")]
            if img_names:
                count = 0
                for img_n in img_names:
                    parts = Path(img_n).parts
                    if len(parts) >= 2:
                        folder = parts[-2].lower().replace(" ", "_").replace("-", "_")
                        cls_name = rice_class_map.get(folder, None)
                        if cls_name is None:
                            continue  # skip unknown classes from this source
                        out_path = dest / cls_name / Path(img_n).name
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(img_n) as src:
                            with open(out_path, "wb") as df:
                                shutil.copyfileobj(src, df)
                        count += 1
                print(f"   ✓ {count} extra rice images")
                zp.unlink(missing_ok=True)
                break
        zp.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. GENERIC NEGATIVES (non-leaf, non-crop images)
# ─────────────────────────────────────────────────────────────────────────────
def download_negatives():
    dest = RAW / "generic_negative"
    if dest.exists():
        existing = sum(1 for _ in dest.rglob("*.jpg"))
        if existing >= 100:
            print(f"✓ generic_negative already present ({existing} images)")
            return

    print("\n→ Downloading generic negative samples (soil, weeds, tools, sky)")

    # Use a small curated set of URLs for each negative class
    # These are public domain images from various sources
    negative_sources = {
        "soil_and_dirt": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bliss_%28Windows_XP%29.png/320px-Bliss_%28Windows_XP%29.png",
        ],
    }

    # Better approach: download from GitHub repos with non-plant images
    sources = [
        (
            "https://github.com/fastai/imagenette/archive/refs/heads/master.zip",
            "imagenette (negatives)",
        ),
    ]

    # Actually, let's use PlantVillage's background class if available,
    # or create a placeholder directory structure and note what's needed
    for cls in ["soil_and_dirt", "weeds_and_grass", "human_hands_and_tools", "sky_and_background"]:
        cls_dir = dest / cls
        cls_dir.mkdir(parents=True, exist_ok=True)

    # Download a small set from COCO-style negative images via a public source
    negative_url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"
    zp = ROOT / "data" / "_tmp_coco128.zip"
    if download(negative_url, zp, "COCO128 for negative samples"):
        with zipfile.ZipFile(zp) as z:
            all_names = z.namelist()
            # Extract non-plant images (indoor/outdoor scenes)
            img_names = [n for n in all_names if "/images/" in n and Path(n).suffix.lower() in {".jpg", ".png"} and not n.endswith("/")]
            count = 0
            for i, img_n in enumerate(img_names[:200]):  # take first 200 as negatives
                out_cls = ["soil_and_dirt", "weeds_and_grass", "human_hands_and_tools", "sky_and_background"][i % 4]
                out_path = dest / out_cls / Path(img_n).name
                with z.open(img_n) as src:
                    with open(out_path, "wb") as df:
                        shutil.copyfileobj(src, df)
                count += 1
            print(f"   ✓ {count} generic negative images extracted from COCO128")
        zp.unlink(missing_ok=True)
    else:
        print("   ⚠ Could not download COCO128. Creating placeholder structure.")
        print("   → For best results, add 50+ images per class in data/raw/generic_negative/{class}/")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CropGuard Dataset Downloader")
    print("=" * 60)
    print(f"Target: {RAW}")

    steps = [
        ("MangoLeafBD", download_mango),
        ("Sugarcane field", download_sugarcane),
        ("Wheat field", download_wheat),
        ("Cotton field", download_cotton),
        ("Groundnut field", download_groundnut),
        ("Rice extra classes", download_rice_extra),
        ("Generic negatives", download_negatives),
    ]

    results = {}
    for name, fn in steps:
        print(f"\n{'─'*50}")
        print(f"→ {name}")
        print(f"{'─'*50}")
        try:
            fn()
            results[name] = "OK"
        except Exception as e:
            print(f"   ✗ ERROR in {name}: {e}")
            import traceback; traceback.print_exc()
            results[name] = f"ERROR: {e}"

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    for name, status in results.items():
        icon = "✓" if status == "OK" else "✗"
        print(f"  {icon} {name}: {status}")

    print("\nDataset counts after download:")
    for d in sorted(RAW.iterdir()):
        if d.is_dir():
            imgs = sum(1 for f in d.rglob("*") if f.suffix.lower() in {".jpg", ".jpeg", ".png"})
            classes = [c.name for c in d.iterdir() if c.is_dir()]
            print(f"  {d.name}: {imgs} images, {len(classes)} classes: {classes}")


if __name__ == "__main__":
    main()
