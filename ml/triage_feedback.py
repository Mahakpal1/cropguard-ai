"""Active Learning & Field Feedback Triage CLI.

    python ml/triage_feedback.py [--db data/scans.db] [--report] [--export-dir data/raw/feedback]

Analyzes user/expert feedback recorded through the app:
- Accuracy perceived by farmers/experts on real fields
- Top confusion pairs (what the model predicted vs the true field label)
- Export of candidate retraining cases for active learning loops
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    p = argparse.ArgumentParser(description="Triage field feedback for active learning.")
    p.add_argument("--db", default=str(ROOT / "data" / "scans.db"), help="Path to SQLite database")
    p.add_argument("--report", action="store_true", default=True, help="Print summary report")
    p.add_argument("--export-manifest", help="Optional CSV output path for retraining manifest")
    return p.parse_args()


def main():
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Database {db_path} does not exist yet. No feedback collected.")
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Check if feedback table exists
    has_table = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='feedback'"
    ).fetchone()[0]
    if not has_table:
        print("Feedback table has not been initialized yet.")
        return 0

    rows = conn.execute("""
        SELECT f.*, s.class_id AS predicted_class_id, s.display_en, s.confidence
        FROM feedback f
        LEFT JOIN scans s ON f.scan_id = s.id
        ORDER BY f.id DESC
    """).fetchall()

    if not rows:
        print("No feedback entries recorded yet.")
        return 0

    total = len(rows)
    correct = sum(1 for r in rows if r["is_correct"])
    incorrect = total - correct
    acc = correct / total if total > 0 else 0.0

    print("=" * 60)
    print(" CROPGUARD ACTIVE LEARNING & FIELD FEEDBACK REPORT")
    print("=" * 60)
    print(f"Total Feedback Submissions : {total}")
    print(f"Confirmed Correct          : {correct} ({acc*100:.1f}%)")
    print(f"Corrections Reported       : {incorrect} ({(1-acc)*100:.1f}%)")

    # Confusion breakdown
    mismatches = [r for r in rows if not r["is_correct"] and r["corrected_class_id"]]
    if mismatches:
        print("\nTop Misclassifications (Predicted -> Farmer/Expert Label):")
        confusion = {}
        for r in mismatches:
            pred = r["predicted_class_id"] or "Unknown"
            true_lbl = r["corrected_class_id"]
            pair = f"{pred}  -->  {true_lbl}"
            confusion[pair] = confusion.get(pair, 0) + 1

        for pair, count in sorted(confusion.items(), key=lambda kv: -kv[1]):
            print(f"  [{count}x] {pair}")

    # Export manifest if requested
    if args.export_manifest and mismatches:
        out_p = Path(args.export_manifest)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write("scan_id,timestamp,predicted_class,corrected_class,notes,expert_verified\n")
            for r in mismatches:
                f.write(f"{r['scan_id']},{r['ts']},{r['predicted_class_id']},{r['corrected_class_id']},"
                        f"\"{r['notes'] or ''}\",{bool(r['expert_verified'])}\n")
        print(f"\nRetraining candidate manifest exported to: {out_p}")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
