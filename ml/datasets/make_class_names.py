"""Build the class list the backend needs from the unified dataset.

    python ml/datasets/make_class_names.py --manifest data/union/manifest.csv --out contracts/class_names.broad.json

Use it with  CLASSES_PATH=contracts/class_names.broad.json  (backend) after you install a model trained on this class list.
Hindi names are filled for common crops and 'healthy'; everything else is copied from English and flagged
`needs_translation` so a native speaker can fix it. Keep contracts/class_names.json (15 classes) for the tests.
"""
import argparse
import csv
import json
from pathlib import Path

CROP_HI = {"Tomato": "टमाटर", "Potato": "आलू", "Pepper": "शिमला मिर्च", "Rice": "धान (चावल)", "Wheat": "गेहूँ", "Maize": "मक्का",
           "Cotton": "कपास", "Sugarcane": "गन्ना", "Soybean": "सोयाबीन", "Groundnut": "मूँगफली", "Mustard": "सरसों", "Cabbage": "पत्तागोभी",
           "Cauliflower": "फूलगोभी", "Brinjal": "बैंगन", "Okra": "भिंडी", "Cucumber": "खीरा", "Pumpkin": "कद्दू", "Squash": "स्क्वैश (कद्दू वर्ग)",
           "Watermelon": "तरबूज", "Mango": "आम", "Banana": "केला", "Orange": "संतरा", "Citrus": "नींबू वर्गीय फल", "Apple": "सेब", "Grape": "अंगूर",
           "Peach": "आड़ू", "Cherry": "चेरी", "Strawberry": "स्ट्रॉबेरी", "Raspberry": "रसभरी", "Blueberry": "ब्लूबेरी", "Onion": "प्याज़",
           "Garlic": "लहसुन", "Chickpea": "चना", "Pigeonpea": "अरहर", "Lentil": "मसूर", "Sorghum": "ज्वार", "Millet": "बाजरा", "Cassava": "कसावा",
           "Coffee": "कॉफ़ी", "Tea": "चाय", "Jute": "जूट", "Sunflower": "सूरजमुखी", "Bean": "सेम"}


def pretty(s):
    s = s.replace("_", " ").strip()
    return s[:1].upper() + s[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--out", default="contracts/class_names.broad.json")
    a = ap.parse_args()
    labels = sorted({r["label"] for r in csv.DictReader(open(a.manifest, encoding="utf-8"))})
    classes = []
    for lab in labels:
        crop, dis = lab.split("___", 1)
        healthy = dis.lower() == "healthy"
        c = {"id": lab, "crop": {"en": pretty(crop), "hi": CROP_HI.get(crop, pretty(crop))},
             "disease": {"en": pretty(dis), "hi": "स्वस्थ" if healthy else pretty(dis)}, "healthy": healthy}
        if crop not in CROP_HI or not healthy:
            c["needs_translation"] = [k for k, ok in (("crop", crop in CROP_HI), ("disease", healthy)) if not ok]
        classes.append(c)
    json.dump({"version": 2, "input_size": 224, "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225], "classes": classes},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(classes)} classes, {len({c['crop']['en'] for c in classes})} crops -> {a.out}")
    print("classes still needing a Hindi name:", sum(1 for c in classes if c.get("needs_translation")))


if __name__ == "__main__":
    main()
