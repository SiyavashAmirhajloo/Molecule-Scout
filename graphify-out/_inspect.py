import json
from collections import Counter
from pathlib import Path

detect = json.loads(Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8"))
root = r"D:\Learning\Molecule-Scout"

def rel_of(f: str) -> str:
    return f[len(root):].lstrip("/\\").replace("\\", "/")

for cat in ("code", "document"):
    fl = detect["files"].get(cat, [])
    tops = Counter()
    for f in fl:
        r = rel_of(f)
        tops[r.split("/")[0] if "/" in r else "(root)"] += 1
    print(f"--- {cat} ({len(fl)}) ---")
    for k, v in tops.most_common(15):
        print(f"  {k}: {v}")

print()
print("--- documents (all 133) ---")
for f in detect["files"].get("document", []):
    print("  ", rel_of(f))
