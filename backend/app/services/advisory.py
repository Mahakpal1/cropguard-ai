"""Curated knowledge base. Advice is NEVER generated at run time: it is read from reviewed JSON files."""
import json
from pathlib import Path

from .class_mapping import norm


class Advisory:
    def __init__(self, kb_dir):
        kb_dir = Path(kb_dir)
        self.common = json.load(open(kb_dir / "_common.json", encoding="utf-8"))
        self.entries = {}
        for p in sorted(kb_dir.glob("*.json")):
            if p.name.startswith("_"):
                continue
            e = json.load(open(p, encoding="utf-8"))
            self.entries[e["id"]] = e
        self.by_norm = {norm(k): v for k, v in self.entries.items()}   # Tomato___Early_blight == Tomato_Early_blight

    def entry(self, class_id):
        return self.entries.get(class_id) or self.by_norm.get(norm(class_id))

    def tier(self, class_id):
        """reviewed (expert signed off) | draft (written, not yet reviewed) | none (no entry: generic advice only)."""
        e = self.entry(class_id)
        return "none" if e is None else ("reviewed" if e.get("review", {}).get("status") == "reviewed" else "draft")

    def advice(self, class_id):
        """Advice in both languages so the UI can switch language without another request."""
        e = self.entry(class_id)
        if e is None:
            return self.generic_advice(healthy=norm(class_id).endswith("healthy"))
        out = {}
        for lang in ("en", "hi"):
            out[lang] = {
                "symptoms": e["symptoms"][lang],
                "do_now": e["do_now"][lang],
                "avoid": e["avoid_extra"][lang] + self.common["avoid"][lang],
                "prevent": e["prevent"][lang],
                "disclaimer": self.common["disclaimer"][lang],
            }
        return out

    def generic_advice(self, healthy=False):
        c = self.common
        if healthy:
            return {l: {"symptoms": [c["generic_healthy_note"][l]], "do_now": c["generic_healthy_do"][l], "avoid": c["generic_healthy_avoid"][l],
                        "prevent": c["generic_healthy_prevent"][l], "disclaimer": c["disclaimer"][l]} for l in ("en", "hi")}
        return {l: {"symptoms": [c["no_entry_note"][l]], "do_now": c["no_entry_do"][l], "avoid": c["avoid"][l], "prevent": [],
                    "disclaimer": c["disclaimer"][l]} for l in ("en", "hi")}

    def fallback_advice(self, status):
        """Advice block for non-diagnosis outcomes (retake the photo, unsupported crop)."""
        msg = self.common.get(status) or self.common["low_confidence"]
        return {lang: {"symptoms": [msg[lang]], "do_now": self.common["retake_tips"][lang], "avoid": [],
                       "prevent": [], "disclaimer": self.common["disclaimer"][lang]} for lang in ("en", "hi")}
