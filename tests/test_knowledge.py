import json
import re

import jsonschema
import pytest

from tests.conftest import ROOT

KB = ROOT / "knowledge_base"
SCHEMA = json.load(open(ROOT / "contracts" / "knowledge.schema.json"))
CLASSES = json.load(open(ROOT / "contracts" / "class_names.json", encoding="utf-8"))["classes"]
DOSE = re.compile(r"\b\d+(\.\d+)?\s?(ml|g|kg|l|litre|liter|gram|ppm|%|cc|oz|lb)\b", re.I)


def entries():
    return {p.stem: json.load(open(p, encoding="utf-8")) for p in KB.glob("*.json") if not p.name.startswith("_")}


ALL_ENTRY_IDS = sorted(p.stem for p in KB.glob("*.json") if not p.name.startswith("_"))


def test_every_class_has_an_entry():
    assert {c["id"] for c in CLASSES} <= set(entries()) and len(CLASSES) == 15


@pytest.mark.parametrize("cid", ALL_ENTRY_IDS)      # every advice file is checked, including ones you add later
def test_entry_valid_and_safe(cid):
    e = entries()[cid]
    jsonschema.validate(e, SCHEMA)
    for key in ("symptoms", "do_now", "prevent"):
        assert len(e[key]["en"]) == len(e[key]["hi"]) == 3
    assert len(e["avoid_extra"]["en"]) == len(e["avoid_extra"]["hi"])
    text = json.dumps([e["symptoms"], e["do_now"], e["prevent"], e["avoid_extra"]], ensure_ascii=False)
    assert not DOSE.search(text), "knowledge entries must not contain dosage numbers"


def test_chemical_advice_always_defers_to_label():
    for e in entries().values():
        joined = " ".join(e["do_now"]["en"]).lower()
        if "fungicide" in joined or "miticide" in joined or "copper" in joined:
            assert "label" in joined


def test_common_block_complete():
    c = json.load(open(KB / "_common.json", encoding="utf-8"))
    for k in ("avoid", "disclaimer", "retake_tips", "unsupported_crop", "low_confidence", "no_leaf"):
        assert k in c


