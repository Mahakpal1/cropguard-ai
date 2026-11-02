"""Create empty knowledge-base entries (in knowledge_base/drafts/) for classes that have no entry yet.

    python ml/datasets/make_kb_scaffolds.py --classes contracts/class_names.broad.json

An agriculture expert (and a Hindi reviewer) fills the TODO lines, then the file is moved up into knowledge_base/.
Until a class has a real entry, the app shows only generic advice and says so (advice_tier = none).
Rules: no dosage numbers; chemical suggestions must say 'follow the label and your agricultural officer'; cite sources.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", default=str(ROOT / "contracts" / "class_names.broad.json"))
    a = ap.parse_args()
    kb = ROOT / "knowledge_base"; drafts = kb / "drafts"; drafts.mkdir(exist_ok=True)
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    have = {norm(p.stem) for p in kb.glob("*.json") if not p.name.startswith("_")} | {norm(p.stem) for p in drafts.glob("*.json")}
    made = 0
    for c in json.load(open(a.classes, encoding="utf-8"))["classes"]:
        if norm(c["id"]) in have:
            continue
        todo = lambda what: {"en": [f"TODO ({what} {i})" for i in (1, 2, 3)], "hi": [f"TODO ({what} {i})" for i in (1, 2, 3)]}
        entry = {"id": c["id"], "crop": c["crop"], "disease": c["disease"], "scientific_name": None,
                 "type": "healthy" if c["healthy"] else "fungal", "healthy": c["healthy"],
                 "symptoms": todo("symptom"), "do_now": todo("action"), "avoid_extra": {"en": [], "hi": []}, "prevent": todo("prevention"),
                 "sources": [{"name": "TODO exact extension page", "url": "https://extension.psu.edu/"}],
                 "review": {"status": "draft", "note": "Scaffold. Fill every TODO, fix `type`, add exact sources, get expert + Hindi review."}}
        json.dump(entry, open(drafts / f"{c['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        made += 1
    print(f"{made} scaffolds written to {drafts}")


if __name__ == "__main__":
    main()
