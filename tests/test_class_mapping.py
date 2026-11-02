from backend.app.services.class_mapping import build_lookup, load_classes, map_label
from tests.conftest import PV38, ROOT

LK = build_lookup(load_classes(ROOT / "contracts" / "class_names.json"))


def test_all_38_scheme_names_for_our_classes_map_uniquely():
    mapped = [map_label(n, LK) for n in PV38]
    assert mapped.count(None) == 1 and mapped[-1] is None          # only the apple class is out of scope
    assert len({m for m in mapped if m}) == 15


def test_emmarex_names_map_to_themselves():
    for c in load_classes(ROOT / "contracts" / "class_names.json"):
        assert map_label(c["id"], LK) == c["id"]


def test_unknown_label():
    assert map_label("Corn___Common_rust", LK) is None
