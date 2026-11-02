"""Helpers shared by the local training script (no PyTorch needed, so they are unit-tested):
dataset scanning, class metadata, near-duplicate grouping (honest split), augmentation classes, PlantDoc mapping."""
import os
import random
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageFilter

EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


# ------------------------------------------------------------------ dataset layout
def find_split_dirs(base):
    """Find folders called train and valid (or val/validation) that contain class sub-folders."""
    found = {}
    for r, d, _ in os.walk(base):
        n = Path(r).name.lower()
        if n in ("train", "valid", "val", "validation") and len(d) >= 5:
            found[n] = Path(r)
    return found.get("train"), found.get("valid") or found.get("val") or found.get("validation")


def scan(root, split):
    return [(str(f), d.name, split) for d in sorted(p for p in Path(root).iterdir() if p.is_dir())
            for f in d.iterdir() if f.suffix.lower() in EXT]


# ------------------------------------------------------------------ class metadata
def tok(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


CROP_ALIAS = {"Corn_maize": "Maize", "Cherry_including_sour": "Cherry", "Pepper_bell": "Pepper"}
CROP_HI = {"Tomato": "टमाटर", "Potato": "आलू", "Pepper": "शिमला मिर्च", "Maize": "मक्का", "Apple": "सेब", "Grape": "अंगूर", "Peach": "आड़ू",
           "Cherry": "चेरी", "Strawberry": "स्ट्रॉबेरी", "Raspberry": "रसभरी", "Blueberry": "ब्लूबेरी", "Orange": "संतरा",
           "Squash": "स्क्वैश (कद्दू वर्ग)", "Soybean": "सोयाबीन"}
DIS_HI = {"healthy": "स्वस्थ", "Bacterial_spot": "जीवाणु धब्बा रोग", "Early_blight": "अगेती झुलसा", "Late_blight": "पछेती झुलसा",
          "Leaf_Mold": "पर्ण फफूंद (लीफ मोल्ड)", "Septoria_leaf_spot": "सेप्टोरिया पत्ती धब्बा", "Target_Spot": "टारगेट स्पॉट (लक्ष्य धब्बा)",
          "Tomato_mosaic_virus": "मोज़ेक विषाणु", "Tomato_Yellow_Leaf_Curl_Virus": "पीला पत्ती मोड़क विषाणु",
          "Spider_mites_Two_spotted_spider_mite": "मकड़ी माइट (लाल मकड़ी)", "Powdery_mildew": "चूर्णिल आसिता (पाउडरी मिल्ड्यू)",
          "Common_rust": "सामान्य रतुआ (रस्ट)", "Black_rot": "काला सड़न रोग (ब्लैक रॉट)", "Apple_scab": "सेब का स्कैब (पपड़ी रोग)",
          "Cedar_apple_rust": "सीडर एप्पल रस्ट", "Northern_Leaf_Blight": "उत्तरी पत्ती झुलसा", "Leaf_scorch": "पत्ती झुलसा (लीफ स्कॉर्च)",
          "Haunglongbing_Citrus_greening": "सिट्रस ग्रीनिंग (हुआंगलोंगबिंग)", "Esca_Black_Measles": "एस्का (ब्लैक मीज़ल्स)",
          "Leaf_blight_Isariopsis_Leaf_Spot": "पत्ती झुलसा (इसारियोप्सिस पत्ती धब्बा)", "Cercospora_leaf_spot_Gray_leaf_spot": "सर्कोस्पोरा / ग्रे पत्ती धब्बा"}
DIS_EN = {"Spider_mites_Two_spotted_spider_mite": "Spider Mites", "Haunglongbing_Citrus_greening": "Citrus Greening (Huanglongbing)",
          "Esca_Black_Measles": "Esca (Black Measles)", "Leaf_blight_Isariopsis_Leaf_Spot": "Leaf Blight (Isariopsis Leaf Spot)",
          "Cercospora_leaf_spot_Gray_leaf_spot": "Cercospora / Gray Leaf Spot", "Tomato_mosaic_virus": "Mosaic Virus",
          "Tomato_Yellow_Leaf_Curl_Virus": "Yellow Leaf Curl Virus"}


def parse_class(raw):
    """-> (display crop, disease token, crop token). The class ID keeps the original crop token (Pepper_bell) so it matches the
    advice files and the model labels exactly; only the DISPLAY name is shortened (Pepper, Maize, Cherry)."""
    crop_raw, dis = raw.split("___", 1)
    crop_tok = tok(crop_raw)
    return CROP_ALIAS.get(crop_tok, crop_tok), tok(dis), crop_tok


def build_meta(raw_classes):
    classes, by_crop = [], {}
    for raw in raw_classes:
        crop, dis, crop_tok = parse_class(raw)
        healthy = dis.lower() == "healthy"
        c = {"id": f"{crop_tok}___{dis}", "crop": {"en": crop, "hi": CROP_HI.get(crop, crop)},
             "disease": {"en": DIS_EN.get(dis, "Healthy" if healthy else dis.replace("_", " ").capitalize()), "hi": DIS_HI.get(dis, dis.replace("_", " "))},
             "healthy": healthy}
        if crop not in CROP_HI or dis not in DIS_HI:
            c["needs_translation"] = True
        classes.append(c)
        by_crop.setdefault(crop, []).append(healthy)
    return classes, sorted(c for c, hs in by_crop.items() if all(hs))


# ------------------------------------------------------------------ near-duplicate grouping (honest split)
def d4_variants(a):
    out = []
    for k in range(4):
        r = np.rot90(a, k)
        out += [r, r[:, ::-1]]
    return out


def canon_hash(path):
    """64-bit hash that is the same for flips/rotations (and fairly robust to brightness changes)."""
    try:
        im = Image.open(path)
        im.draft("L", (64, 64))
        g = np.asarray(im.convert("L").resize((16, 16), Image.BILINEAR), dtype=np.float32)
    except Exception:
        return 0
    best = None
    for v in d4_variants(g):
        s = v.reshape(8, 2, 8, 2).mean((1, 3))
        h = int(np.packbits((s > s.mean()).flatten()).view(">u8")[0])
        best = h if best is None else min(best, h)
    return best


_POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def popcount(x):
    return _POP[np.ascontiguousarray(x).view(np.uint8).reshape(x.shape + (8,))].sum(-1)


def group_ids(labels, hashes, max_dist=4, max_bucket=400):
    """Union images of the same class whose hashes differ in <= max_dist bits (5 chunks: such a pair shares one chunk exactly)."""
    n = len(labels)
    parent = list(range(n))
    H = np.array(hashes, dtype=np.uint64)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for sh, bits in zip([0, 13, 26, 39, 52], [13, 13, 13, 13, 12]):
        key = ((H >> np.uint64(sh)) & np.uint64((1 << bits) - 1)).astype(np.int64)
        tmp = pd.DataFrame({"l": np.asarray(labels), "k": key, "i": np.arange(n)})
        for _, g in tmp.groupby(["l", "k"])["i"]:
            idx = g.values
            if len(idx) < 2 or len(idx) > max_bucket:
                continue
            d = popcount(H[idx][:, None] ^ H[idx][None, :])
            for a, b in np.argwhere(np.triu(d <= max_dist, 1)):
                ra, rb = find(idx[a]), find(idx[b])
                if ra != rb:
                    parent[ra] = rb
    return np.array([find(i) for i in range(n)])


def compute_hashes(paths, cache_file=None, workers=None, log=print):
    """Hash all images with threads (works on Windows and Linux). Re-uses a cache when the file list is unchanged."""
    paths = list(paths)
    if cache_file and Path(cache_file).exists():
        z = np.load(cache_file, allow_pickle=False)
        if len(z["paths"]) == len(paths) and (z["paths"] == np.array(paths)).all():
            log(f"hash cache found: {cache_file}")
            return [int(h) for h in z["hashes"]]
    from concurrent.futures import ThreadPoolExecutor
    t0, out = time.time(), []
    with ThreadPoolExecutor(max_workers=workers or min(16, (os.cpu_count() or 4))) as ex:
        for i, h in enumerate(ex.map(canon_hash, paths), 1):
            out.append(h)
            if i % 10000 == 0:
                log(f"  hashed {i}/{len(paths)} ({time.time()-t0:.0f}s)")
    if cache_file:
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache_file, paths=np.array(paths), hashes=np.array(out, dtype=np.uint64))
    return out


# ------------------------------------------------------------------ augmentation (PIL/numpy only)
class PadSquare:
    """Same as the backend: keep the WHOLE photo, grey padding."""
    def __call__(self, im):
        w, h = im.size
        if w == h:
            return im
        s = max(w, h)
        out = Image.new("RGB", (s, s), (128, 128, 128))
        out.paste(im, ((s - w) // 2, (s - h) // 2))
        return out


class BGReplace:
    """Paste the leaf on random soil/grass/grey textures (lab photos have plain backgrounds)."""
    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        a = np.asarray(img).astype(np.float32) / 255
        sat = (a.max(2) - a.min(2)) / (a.max(2) + 1e-6)
        m = ((sat > .18) & (a.max(2) > .12)).astype(np.uint8) * 255
        m = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)[..., None] / 255
        h, w = a.shape[:2]
        base = np.array(random.choice([[.35, .25, .17], [.25, .45, .2], [.6, .6, .6], [.5, .5, .5]])) + np.random.uniform(-.1, .1, 3)
        bg = np.ones((h, w, 3), np.float32) * base
        yy, xx = np.ogrid[:h, :w]
        for _ in range(random.randint(8, 20)):
            cy, cx, r = random.randint(0, h), random.randint(0, w), random.randint(10, 60)
            bg[(yy - cy) ** 2 + (xx - cx) ** 2 < r * r] = np.clip(base + np.random.uniform(-.2, .2, 3), 0, 1)
        bg = np.asarray(Image.fromarray((bg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(random.uniform(2, 8)))).astype(np.float32) / 255
        return Image.fromarray(((a * m + bg * (1 - m)) * 255).astype(np.uint8))


# ------------------------------------------------------------------ PlantDoc (real field photos)
PLANTDOC_MAP = {
    "Apple Scab Leaf": "Apple___Apple_scab", "Apple leaf": "Apple___healthy", "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf": "Pepper,_bell___healthy", "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot", "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy", "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight", "Corn rust leaf": "Corn_(maize)___Common_rust_", "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight", "Potato leaf late blight": "Potato___Late_blight", "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy", "Squash Powdery mildew leaf": "Squash___Powdery_mildew", "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight", "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot", "Tomato leaf": "Tomato___healthy",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot", "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus", "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato mold leaf": "Tomato___Leaf_Mold", "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "grape leaf": "Grape___healthy", "grape leaf black rot": "Grape___Black_rot"}


def _nk(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def plantdoc_frame(root, class_idx):
    lookup = {_nk(k): v for k, v in PLANTDOC_MAP.items()}
    class_lookup = {_nk(k): idx for k, idx in class_idx.items()}
    rows, skipped = [], []
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        raw = lookup.get(_nk(d.name))
        target_idx = class_lookup.get(_nk(raw)) if raw else None
        if target_idx is None:
            skipped.append(d.name)
            continue
        rows += [(str(f), target_idx, d.name) for f in d.iterdir() if f.suffix.lower() in EXT]
    return pd.DataFrame(rows, columns=["path", "y", "pd_class"]), skipped
