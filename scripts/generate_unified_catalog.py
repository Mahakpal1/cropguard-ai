import json
import pandas as pd
from pathlib import Path

# Load taxonomy
df = pd.read_csv("data/taxonomy.csv")
unique_rows = df.drop_duplicates(subset=["canonical_key"]).sort_values("canonical_key")

CROP_HI = {
    "Apple": "सेब",
    "Banana": "केला",
    "Blueberry": "ब्लूबेरी",
    "Cauliflower": "फूलगोभी",
    "Cherry": "चेरी",
    "Chilli": "मिर्च",
    "Cotton": "कपास",
    "Grape": "अंगूर",
    "Groundnut": "मूंगफली",
    "Maize": "मक्का",
    "Mango": "आम",
    "Orange": "संतरा",
    "Peach": "आड़ू",
    "Pepper": "शिमला मिर्च",
    "Potato": "आलू",
    "Radish": "मूली",
    "Raspberry": "रसभरी",
    "Rice": "धान",
    "Soybean": "सोयाबीन",
    "Squash": "कद्दू / तोरी",
    "Strawberry": "स्ट्रॉबेरी",
    "Sugarcane": "गन्ना",
    "Tomato": "टमाटर",
    "Wheat": "गेहूं",
    "__non_crop__": "गैर-फसल",
}

DISEASE_TRANSLATIONS = {
    "Healthy": ("Healthy", "स्वस्थ"),
    "Apple_Scab": ("Apple Scab", "सेब का पपड़ी रोग"),
    "Black_Rot": ("Black Rot", "काला सड़न रोग"),
    "Cedar_Apple_Rust": ("Cedar Apple Rust", "देवदार सेब रतुआ"),
    "Powdery_Mildew": ("Powdery Mildew", "चूर्णिल आसिता (पाउडरी मिल्ड्यू)"),
    "Gray_Leaf_Spot": ("Gray Leaf Spot", "भूरा पत्ती धब्बा"),
    "Common_Rust": ("Common Rust", "सामान्य रतुआ"),
    "Northern_Leaf_Blight": ("Northern Leaf Blight", "उत्तरी पत्ती झुलसा"),
    "Esca_Black_Measles": ("Esca (Black Measles)", "एस्का (काला चेचक)"),
    "Leaf_Blight": ("Leaf Blight", "पत्ती झुलसा"),
    "Citrus_Greening": ("Citrus Greening", "सिट्रस ग्रीनिंग (हौंगलोंगबिंग)"),
    "Bacterial_Spot": ("Bacterial Spot", "जीवाणु धब्बा रोग"),
    "Early_Blight": ("Early Blight", "अगेती झुलसा"),
    "Late_Blight": ("Late Blight", "पछेती झुलसा"),
    "Leaf_Scorch": ("Leaf Scorch", "पत्ती झुलसन"),
    "Leaf_Mold": ("Leaf Mold", "पत्ती फफूंद"),
    "Septoria_Leaf_Spot": ("Septoria Leaf Spot", "सेप्टोरिया पत्ती धब्बा"),
    "Spider_Mites": ("Spider Mites", "मकड़ी माइट्स"),
    "Target_Spot": ("Target Spot", "टारगेट स्पॉट (लक्ष्य धब्बा)"),
    "Yellow_Leaf_Curl_Virus": ("Yellow Leaf Curl Virus", "पीला पत्ती मरोड़िया वायरस"),
    "Mosaic_Virus": ("Mosaic Virus", "मोज़ेक वायरस"),
    "Bacterial_Blight": ("Bacterial Blight", "जीवाणु झुलसा"),
    "Brown_Spot": ("Brown Spot", "भूरा धब्बा रोग"),
    "Blast": ("Blast", "ब्लास्ट (झोंका रोग)"),
    "Leaf_Scald": ("Leaf Scald", "पत्ती अंगमारी (स्कैल्ड)"),
    "Sheath_Blight": ("Sheath Blight", "शीथ ब्लाइट (पर्णच्छद झुलसा)"),
    "Tungro": ("Tungro Virus", "टुंग्रो वायरस"),
    "Hispa": ("Rice Hispa", "राइस हिस्पा (कीट)"),
    "Yellow_Rust": ("Yellow Rust", "पीला रतुआ (स्ट्राइप रस्ट)"),
    "Brown_Rust": ("Brown Rust", "भूरा रतुआ (लीफ रस्ट)"),
    "Stem_Rust": ("Stem Rust", "तना रतुआ (ब्लैक रस्ट)"),
    "Septoria_Leaf_Blotch": ("Septoria Leaf Blotch", "सेप्टोरिया पत्ती धब्बा"),
    "Red_Rot": ("Red Rot", "लाल सड़न रोग"),
    "Yellow_Leaf": ("Yellow Leaf Disease", "पीली पत्ती रोग"),
    "Pokkah_Boeng": ("Pokkah Boeng", "पोक्का बोइंग रोग"),
    "Smut": ("Smut", "कंडुआ रोग"),
    "Rust": ("Rust", "रतुआ रोग"),
    "Mosaic": ("Mosaic Disease", "मोज़ेक रोग"),
    "Early_Leaf_Spot": ("Early Leaf Spot (Tikka)", "अगेती टिक्का रोग"),
    "Late_Leaf_Spot": ("Late Leaf Spot (Tikka)", "पछेती टिक्का रोग"),
    "Bud_Necrosis": ("Bud Necrosis", "कलिका परिगलन रोग"),
    "Rosette": ("Rosette Disease", "रोज़ेट (गुच्छा) रोग"),
    "Leaf_Curl_Virus": ("Leaf Curl Virus", "पत्ती मरोड़ वायरस"),
    "Fusarium_Wilt": ("Fusarium Wilt", "फ्यूजेरियम उकठा रोग"),
    "Anthracnose": ("Anthracnose", "एंथ्रेक्नोज़ (श्याम वर्ण)"),
    "Bacterial_Canker": ("Bacterial Canker", "जीवाणु कैंकर"),
    "Cutting_Weevil": ("Shoot / Cutting Weevil", "शाखा / कली घुन"),
    "Die_Back": ("Die Back", "डाई बैक (उल्टा सूखा रोग)"),
    "Gall_Midge": ("Gall Midge", "गाल मिज कीट"),
    "Sooty_Mould": ("Sooty Mould", "काली फफूंद (सूटी मोल्ड)"),
    "Sigatoka": ("Sigatoka Leaf Spot", "सिगाटोका पत्ती धब्बा"),
    "Leaf_Curl": ("Leaf Curl", "पत्ती मरोड़ रोग"),
    "White_Rust": ("White Rust", "सफेद रतुआ"),
    "Downy_Mildew": ("Downy Mildew", "मृदु रोमिल आसिता (डाउनी मिल्ड्यू)"),
    "__not_a_leaf__": ("Not a leaf", "पत्ती नहीं"),
}

classes_list = []
for _, row in unique_rows.iterrows():
    cid = row["canonical_key"]
    crop_en = row["canonical_crop"]
    dis_raw = row["canonical_disease"]
    
    crop_hi = CROP_HI.get(crop_en, crop_en)
    dis_en, dis_hi = DISEASE_TRANSLATIONS.get(dis_raw, (dis_raw.replace("_", " "), dis_raw.replace("_", " ")))
    is_healthy = (dis_raw.lower() == "healthy")

    classes_list.append({
        "id": cid,
        "crop": {
            "en": crop_en,
            "hi": crop_hi,
        },
        "disease": {
            "en": dis_en,
            "hi": dis_hi,
        },
        "healthy": is_healthy,
    })

catalog_obj = {
    "version": 2,
    "total_classes": len(classes_list),
    "classes": classes_list,
}

# Write to ml/models/class_names.json and ml/models/dinov2_hierarchical/class_names.json
out1 = Path("ml/models/class_names.json")
out2 = Path("ml/models/dinov2_hierarchical/class_names.json")
out3 = Path("contracts/classes.json")

for p in (out1, out2, out3):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(catalog_obj, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(classes_list)} classes to {p}")
