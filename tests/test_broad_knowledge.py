import json
import re

import jsonschema
import pytest

from tests.conftest import ROOT

BROAD_KB = ROOT / "knowledge_base" / "broad"
SCHEMA = json.load(open(ROOT / "contracts" / "knowledge.schema.json"))
CLASSES = json.load(open(ROOT / "ml" / "models" / "cropguard38_recovered" / "class_names.json", encoding="utf-8"))["classes"]
DOSE = re.compile(r"\b\d+(\.\d+)?\s?(ml|g|kg|l|litre|liter|gram|ppm|%|cc|oz|lb)\b", re.I)


def broad_entries():
    return {p.stem: json.load(open(p, encoding="utf-8")) for p in BROAD_KB.glob("*.json") if not p.name.startswith("_")}


ALL_BROAD_ENTRY_IDS = sorted(p.stem for p in BROAD_KB.glob("*.json") if not p.name.startswith("_"))


def test_every_38_class_has_an_entry_in_broad_kb():
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    entries_map = {norm(k): v for k, v in broad_entries().items()}
    class_norms = {norm(c["id"]) for c in CLASSES}
    assert class_norms <= set(entries_map)
    assert len(CLASSES) == 38


@pytest.mark.parametrize("cid", ALL_BROAD_ENTRY_IDS)
def test_broad_entry_valid_and_safe(cid):
    e = broad_entries()[cid]
    jsonschema.validate(e, SCHEMA)
    for key in ("symptoms", "do_now", "prevent"):
        assert len(e[key]["en"]) == len(e[key]["hi"]) == 3, f"{cid} must have 3 bullets in en and hi for {key}"
    assert len(e["avoid_extra"]["en"]) == len(e["avoid_extra"]["hi"])
    text = json.dumps([e["symptoms"], e["do_now"], e["prevent"], e["avoid_extra"]], ensure_ascii=False)
    assert not DOSE.search(text), f"{cid}: knowledge entries must not contain dosage numbers"


def test_broad_chemical_advice_always_defers_to_label():
    for cid, e in broad_entries().items():
        joined = " ".join(e["do_now"]["en"]).lower()
        if "fungicide" in joined or "miticide" in joined or "copper" in joined:
            assert "label" in joined, f"{cid} must defer chemical advice to label"
