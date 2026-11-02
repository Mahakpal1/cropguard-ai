import csv
import json
import subprocess
import sys

from tests.conftest import ROOT, leaf_image

PREP = ROOT / "ml" / "datasets" / "prepare_union.py"


def make_img(path, frac, seed=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    leaf_image(frac, size=64 + seed).save(path)


def test_prepare_union_merges_sources_and_removes_duplicates(tmp_path):
    pv, pd = tmp_path / "pv", tmp_path / "pd"
    make_img(pv / "Tomato___Early_blight" / "u1___a.png", 0.3, 1)
    make_img(pv / "Corn_(maize)___healthy" / "u2___b.png", 0.0, 2)
    make_img(pd / "Tomato Early blight leaf" / "x.png", 0.2, 3)
    (pd / "Tomato Early blight leaf" / "copy.png").write_bytes((pd / "Tomato Early blight leaf" / "x.png").read_bytes())   # exact duplicate
    make_img(pd / "Mystery plant" / "m.png", 0.1, 4)
    out = tmp_path / "union"
    r = subprocess.run([sys.executable, str(PREP), "--src", f"plantvillage={pv}", "--src", f"plantdoc={pd}", "--out", str(out),
                        "--map", str(ROOT / "ml" / "datasets" / "label_map.csv")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader(open(out / "manifest.csv")))
    labels = {x["label"] for x in rows}
    assert labels == {"Tomato___Early_blight", "Maize___healthy"}                    # both sources land in ONE class
    assert {x["source"] for x in rows if x["label"] == "Tomato___Early_blight"} == {"plantvillage", "plantdoc"}
    assert "1 exact duplicates removed" in r.stdout and "unmapped folders" in r.stdout
    t = ROOT / "ml" / "datasets" / "unmapped_plantdoc.csv"
    assert "Mystery plant" in t.read_text(); t.unlink()


def test_class_names_and_kb_scaffolds(tmp_path):
    man = tmp_path / "manifest.csv"
    man.write_text("path,label,source,group\na.jpg,Rice___Brown_spot,x,1\nb.jpg,Rice___healthy,x,2\nc.jpg,Tomato___Early_blight,x,3\n")
    out = tmp_path / "broad.json"
    r = subprocess.run([sys.executable, str(ROOT / "ml/datasets/make_class_names.py"), "--manifest", str(man), "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    cls = {c["id"]: c for c in json.load(open(out, encoding="utf-8"))["classes"]}
    assert cls["Rice___healthy"]["disease"]["hi"] == "स्वस्थ" and cls["Rice___healthy"]["crop"]["hi"] == "धान (चावल)"
    assert cls["Rice___Brown_spot"]["needs_translation"] == ["disease"] and cls["Rice___healthy"]["healthy"] is True
    drafts = ROOT / "knowledge_base" / "drafts"
    try:
        r = subprocess.run([sys.executable, str(ROOT / "ml/datasets/make_kb_scaffolds.py"), "--classes", str(out)], capture_output=True, text=True)
        assert r.returncode == 0 and "2 scaffolds" in r.stdout      # Tomato___Early_blight already has an entry (same normalised id)
        e = json.load(open(drafts / "Rice___Brown_spot.json", encoding="utf-8"))
        assert e["review"]["status"] == "draft" and e["prevent"]["en"][0].startswith("TODO")
    finally:
        if drafts.exists():
            for f in list(drafts.glob("*.json")):
                f.unlink()
            drafts.rmdir()
