"""Extract and sanitize PlantDoc git archive for Windows compatibility."""
import io
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PD_DIR = ROOT / "work" / "plantdoc"

def main():
    if not (PD_DIR / ".git").exists():
        print("work/plantdoc/.git not found.")
        return
    print("Reading git tree via ls-tree...")
    p = subprocess.Popen(["git", "ls-tree", "-r", "HEAD"], cwd=str(PD_DIR), stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    lines = p.communicate()[0].splitlines()
    print(f"Total entries in tree: {len(lines)}")

    # Launch git cat-file --batch
    cat = subprocess.Popen(["git", "cat-file", "--batch"], cwd=str(PD_DIR), stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    count = 0
    for line in lines:
        if not line.strip():
            continue
        # line format: <mode> SP <type> SP <object> TAB <file>
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        obj_type, sha = parts[1], parts[2]
        filepath = line.split("\t", 1)[1]
        if obj_type != "blob":
            continue

        # Sanitize Windows illegal characters (?, :, *, ", <, >, |)
        clean_rel = re.sub(r'[\?\"\:\<\>\|\*]', '_', filepath)
        target = PD_DIR / clean_rel
        target.parent.mkdir(parents=True, exist_ok=True)

        # Query git cat-file
        cat.stdin.write(f"{sha}\n".encode("ascii"))
        cat.stdin.flush()
        header = cat.stdout.readline().decode("ascii")
        # header format: <sha> SP <type> SP <size> LF
        size = int(header.split()[2])
        content = cat.stdout.read(size)
        cat.stdout.read(1)  # trailing LF

        target.write_bytes(content)
        count += 1
        if count % 500 == 0:
            print(f"  extracted {count} files...")

    cat.stdin.close()
    cat.wait()
    print(f"Successfully extracted {count} files to {PD_DIR}")

if __name__ == "__main__":
    main()
