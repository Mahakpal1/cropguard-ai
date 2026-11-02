import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


class History:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""CREATE TABLE IF NOT EXISTS scans(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, class_id TEXT, display_en TEXT, confidence REAL,
            status TEXT, severity_level TEXT, affected_pct REAL, thumb TEXT)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, scan_id INTEGER, is_correct INTEGER,
            corrected_class_id TEXT, notes TEXT, expert_verified INTEGER,
            FOREIGN KEY (scan_id) REFERENCES scans(id))""")
        self.conn.commit()

    def add(self, r):
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO scans(ts,class_id,display_en,confidence,status,severity_level,affected_pct,thumb) VALUES(?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), r.get("class_id"), r.get("display_en"),
                 r.get("confidence"), r.get("status"), r.get("severity_level"), r.get("affected_pct"), r.get("thumb")))
            self.conn.commit()
            return cur.lastrowid

    def list(self, limit=20):
        with self.lock:
            rows = self.conn.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def clear(self):
        with self.lock:
            self.conn.execute("DELETE FROM scans")
            self.conn.execute("DELETE FROM feedback")
            self.conn.commit()

    def add_feedback(self, fb):
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO feedback(ts,scan_id,is_correct,corrected_class_id,notes,expert_verified) VALUES(?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), fb.get("scan_id"),
                 1 if fb.get("is_correct") else 0, fb.get("corrected_class_id"), fb.get("notes"),
                 1 if fb.get("expert_verified") else 0))
            self.conn.commit()
            return cur.lastrowid

    def list_feedback(self, limit=50):
        with self.lock:
            rows = self.conn.execute(
                """SELECT f.*, s.class_id AS predicted_class_id, s.display_en, s.confidence
                   FROM feedback f
                   LEFT JOIN scans s ON f.scan_id = s.id
                   ORDER BY f.id DESC LIMIT ?""", (limit,)).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            d["is_correct"] = bool(d["is_correct"])
            d["expert_verified"] = bool(d["expert_verified"])
            items.append(d)
        return items

    def get_feedback_stats(self):
        with self.lock:
            total = self.conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            correct = self.conn.execute("SELECT COUNT(*) FROM feedback WHERE is_correct = 1").fetchone()[0]
            corrected = total - correct
            acc = float(correct / total) if total > 0 else 0.0
        return {
            "total_feedback": total,
            "confirmed_correct": correct,
            "corrections_reported": corrected,
            "accuracy_rate": round(acc, 4)
        }
