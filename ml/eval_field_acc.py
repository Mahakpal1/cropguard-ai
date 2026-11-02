import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))
import cg_common as cg
from backend.app.config import Settings
from backend.app.services.pipeline import Pipeline

pipe = Pipeline(Settings())
classes = json.load(open(ROOT / "ml" / "models" / "model_config.json", encoding="utf-8"))["labels"]
class_idx = {c: i for i, c in enumerate(classes)}

fd_te, _ = cg.plantdoc_frame(ROOT / "work" / "plantdoc" / "test", class_idx)
print(f"Total test images: {len(fd_te)}")

correct = 0
total = 0
by_crop = {}

for _, row in fd_te.iterrows():
    try:
        data = Path(row["path"]).read_bytes()
        res = pipe.predict(data, explain=False)
        target = classes[row["y"]]
        crop = target.split("___")[0]
        if crop not in by_crop:
            by_crop[crop] = [0, 0]
        by_crop[crop][1] += 1

        if res["class_id"] == target:
            correct += 1
            by_crop[crop][0] += 1
        total += 1
    except Exception as e:
        print(f"Error on {row['path']}: {e}")

acc = correct / total if total > 0 else 0
print(f"\nOverall Field Accuracy: {correct}/{total} = {acc*100:.2f}%")
print("\nAccuracy by crop:")
for c, (hit, tot) in sorted(by_crop.items()):
    print(f"  {c:15s}: {hit:3d}/{tot:3d} ({hit/tot*100:.1f}%)")
