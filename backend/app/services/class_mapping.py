"""Map any PlantVillage-style label ("Tomato___Early_blight", "Tomato_Early_blight", ...) to our 15 canonical ids."""
import json
import re

_EXTRA = {  # spelling variants seen in other PlantVillage releases
    "tomatoyellowleafcurlvirus": "Tomato__Tomato_YellowLeaf__Curl_Virus",
    "tomatomosaicvirus": "Tomato__Tomato_mosaic_virus",
    "pepperbellhealthy": "Pepper__bell___healthy",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_classes(path):
    return json.load(open(path, encoding="utf-8"))["classes"]


def build_lookup(classes):
    lk = {norm(c["id"]): c["id"] for c in classes}
    ids = set(lk.values())
    lk.update({k: v for k, v in _EXTRA.items() if v in ids})
    return lk


def map_label(label, lookup):
    """Return the canonical class id for `label`, or None if the label is outside our 15 classes."""
    return lookup.get(norm(label))
