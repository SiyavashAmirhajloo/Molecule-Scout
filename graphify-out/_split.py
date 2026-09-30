import json
from pathlib import Path

root = r"D:\Learning\Molecule-Scout"

# Vendored third-party skill libraries are not project knowledge — exclude them.
SKIP_DIRS = ("\\.agents\\", "\\.shared\\", "\\.claude\\skills\\")

def rel_of(f: str) -> str:
    return f[len(root):].lstrip("/\\").replace("\\", "/")

detect = json.loads(Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8"))
docs = [f for f in detect["files"].get("document", [])
        if not rel_of(f).lower().startswith((".agents/", ".shared/", ".claude/skills/"))]

print(f"project docs: {len(docs)}")
for d in docs:
    print("  ", rel_of(d))

# Persist as the uncached set so Part C merges exactly what we extract.
Path("graphify-out/.graphify_uncached.txt").write_text("\n".join(docs), encoding="utf-8")
Path("graphify-out/.graphify_cached.json").unlink(missing_ok=True)

# Two chunks, grouped by directory so cross-file relationships land together.
prompts = [d for d in docs if rel_of(d).startswith("prompts/")]
core = [d for d in docs if not rel_of(d).startswith("prompts/")]
chunks = [core[: len(core) // 2], core[len(core) // 2:], prompts[:6], prompts[6:]]
chunks = [c for c in chunks if c]
for i, c in enumerate(chunks, 1):
    out = Path(f"graphify-out/.graphify_filelist_{i}.txt")
    out.write_text("\n".join(c), encoding="utf-8")
    print(f"chunk {i}: {len(c)} files -> {out}")
