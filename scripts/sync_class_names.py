"""Synchronize class_names.json with the newly trained classes_hierarchy.json."""
import json
from pathlib import Path

HI_CROPS = {
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
    "Raspberry": "रसभरी",
    "Rice": "धान",
    "Soybean": "सोयाबीन",
    "Squash": "कद्दू / स्क्वैश",
    "Strawberry": "स्ट्रॉबेरी",
    "Sugarcane": "गन्ना",
    "Tomato": "टमाटर",
    "Wheat": "गेहूं",
    "__non_crop__": "गैर-फसल",
}

HI_DISEASES = {
    "Healthy": "स्वस्थ",
    "Downy_Mildew": "डाउनी मिल्ड्यू (मृदुरोमिल फफूंद)",
    "Alternaria_Leaf_Spot": "अल्टरनेरिया पत्ती धब्बा",
    "Black_Rot": "काला सड़न रोग",
    "Bacterial_Soft_Rot": "जीवाणु मृदु सड़न",
    "White_Rust": "सफेद रतुआ",
    "Sigatoka": "सिगाटोका पत्ती धब्बा",
    "Cordana": "कोरडाना पत्ती धब्बा",
    "Pestalotiopsis": "पेस्टालोटियोप्सिस पत्ती झुलसा",
    "Leaf_Curl": "पत्ती मरोड़ (पर्ण कुंचन)",
    "Bacterial_Spot": "जीवाणु धब्बा",
    "Early_Blight": "अगेती झुलसा",
    "Late_Blight": "पछेती झुलसा",
    "Leaf_Mold": "पत्ती फफूंद",
    "Mosaic_Virus": "मोज़ेक वायरस",
    "Septoria_Leaf_Spot": "सेप्टोरिया पत्ती धब्बा",
    "Spider_Mites": "लाल मकड़ी कीट",
    "Target_Spot": "लक्ष्य धब्बा",
    "Yellow_Leaf_Curl_Virus": "पीली पत्ती मरोड़ वायरस",
    "Powdery_Mildew": "चूर्णिल आसिता",
    "Citrus_Greening": "सिट्रस ग्रीनिंग",
    "Esca_Black_Measles": "एस्का (काला खसरा)",
    "Leaf_Blight": "पत्ती झुलसा",
    "Apple_Scab": "सेब पपड़ी रोग",
    "Cedar_Apple_Rust": "देवदार सेब रतुआ",
    "Common_Rust": "सामान्य रतुआ",
    "Gray_Leaf_Spot": "धूसर पत्ती धब्बा",
    "Northern_Leaf_Blight": "उत्तरी पत्ती झुलसा",
    "Anthracnose": "एंथ्रेक्नोज़",
    "Bacterial_Canker": "जीवाणु कैंकर",
    "Cutting_Weevil": "काटने वाला घुन कीट",
    "Die_Back": "डाई बैक रोग",
    "Gall_Midge": "गॉल मिज कीट",
    "Sooty_Mould": "काली फफूंद",
    "Bacterial_Blight": "जीवाणु झुलसा",
    "Blast": "झोंका रोग (ब्लास्ट)",
    "Brown_Spot": "भूरा धब्बा",
    "Tungro": "टुंग्रो वायरस",
    "Red_Rot": "लाल सड़न",
    "Rust": "रतुआ रोग",
    "Yellow_Leaf": "पीली पत्ती रोग",
    "Mosaic": "मोज़ेक",
    "Brown_Rust": "भूरा रतुआ",
    "Stem_Rust": "तना रतुआ",
    "Yellow_Rust": "पीला रतुआ",
    "Leaf_Scorch": "पत्ती झुलसन",
    "Rosette": "रोज़ेट रोग",
    "__not_a_leaf__": "पत्ती नहीं है",
}

def format_en_name(name: str) -> str:
    return name.replace("_", " ").strip()

def sync():
    hierarchy_path = Path("ml/models/dinov2_hierarchical/classes_hierarchy.json")
    hierarchy = json.load(open(hierarchy_path, encoding="utf-8"))
    
    classes = []
    for crop in sorted(hierarchy["crops"]):
        diseases = hierarchy["taxonomy"].get(crop, [])
        for dis in sorted(diseases):
            class_id = f"{crop}___{dis}"
            en_crop = format_en_name(crop)
            hi_crop = HI_CROPS.get(crop, en_crop)
            
            en_dis = format_en_name(dis)
            hi_dis = HI_DISEASES.get(dis, en_dis)
            
            is_healthy = (dis.lower() == "healthy")
            
            classes.append({
                "id": class_id,
                "crop": {
                    "en": en_crop,
                    "hi": hi_crop,
                },
                "disease": {
                    "en": en_dis,
                    "hi": hi_dis,
                },
                "healthy": is_healthy,
            })
            
    payload = {
        "version": 2,
        "total_classes": len(classes),
        "classes": classes,
    }
    
    out_paths = [
        Path("ml/models/class_names.json"),
        Path("ml/models/dinov2_hierarchical/class_names.json"),
    ]
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Updated {p} ({len(classes)} classes)")

if __name__ == "__main__":
    sync()
