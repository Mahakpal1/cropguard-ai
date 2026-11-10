import requests

r = requests.post(
    "http://127.0.0.1:8000/api/v1/predict?explain=false",
    files={"file": ("leaf.jpg", open("data/raw/cauliflower_field/Downy_Mildew/downey mildew_1.jpg", "rb"), "image/jpeg")},
)
d = r.json()
print("Live Backend API Response:")
print("  Class ID:   ", d.get("class_id"))
print("  English:    ", d.get("display", {}).get("en"))
print("  Confidence: ", f"{d.get('confidence', 0):.1%}")
print("  Status:     ", d.get("status"))
