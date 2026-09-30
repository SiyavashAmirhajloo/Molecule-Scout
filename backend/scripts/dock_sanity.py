"""DUD-E EGFR docking smoke test.

SMOKE TEST, NOT A BENCHMARK. It answers one narrow question: does our docking
setup rank known EGFR actives above property-matched decoys? It does NOT
reproduce a published DUD-E number — our active:decoy ratio is ~1:4-1:10, where
real DUD-E sits at ~1:60. Enrichment factor is far more meaningful at DUD-E's
real prevalence than at ours, so read the ROC AUC first and treat EF as
supporting.

IF THIS FAILS, before touching the threshold: check the bounding box, then
receptor prep, then protonation — in that order. Vina's per-target DUD-E
performance is modest, so a fail here is a signal to investigate, not proof of
a bug. Do not lower AUC_GATE after seeing a result; the point of a gate is that
it is fixed in advance.

Run: python scripts/dock_sanity.py [--n-actives N] [--n-decoys N] [--seed S]
"""

import argparse
import random
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.docking import (  # noqa: E402
    dock,
    inspect_receptor,
    prep_ligand,
    prepare_receptor,
)

PDB_ID = "1M17"
TARGET = "EGFR"
DUDE_URL = f"https://dude.docking.org/datasets/{TARGET}.tar.gz"
CACHE = Path(__file__).resolve().parent.parent.parent / ".cache" / "dude"

# Fixed in advance. AUC is prevalence-independent, so it is the honest gate
# even at our non-DUD-E ratio; EF@5 is reported alongside it, never alone.
AUC_GATE = 0.7
BOOTSTRAP_ITERS = 2000


def fetch_dataset() -> tuple[list[str], list[str]]:
    """Return (actives, decoys) SMILES, downloading the tarball once."""
    CACHE.mkdir(parents=True, exist_ok=True)
    tar_path = CACHE / f"{TARGET}.tar.gz"
    if not tar_path.exists():
        print(f"downloading {DUDE_URL}")
        try:
            with urllib.request.urlopen(DUDE_URL, timeout=300) as r, open(
                tar_path, "wb"
            ) as f:
                f.write(r.read())
        except (urllib.error.URLError, OSError) as e:
            raise SystemExit(
                f"could not download DUD-E {TARGET}: {e}\n"
                f"If this host cannot reach dude.docking.org, download the tarball "
                f"manually to {tar_path} and re-run."
            )
    extract_dir = CACHE / TARGET
    if not extract_dir.exists():
        with tarfile.open(tar_path) as t:
            t.extractall(extract_dir)
    # DUD-E archives nest everything under a lowercase target/ dir.
    root = extract_dir / TARGET.lower()
    if not root.is_dir():
        root = extract_dir
    actives_file = root / "actives_final.ism"
    decoys_file = root / "decoys_final.ism"
    for p in (actives_file, decoys_file):
        if not p.exists():
            raise SystemExit(f"missing {p} in extracted {TARGET} archive")

    def read_ism(path: Path) -> list[str]:
        out = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            # DUD-E .ism = SMILES then a mol2 blob.
            out.append(line.split()[0])
        return out

    return read_ism(actives_file), read_ism(decoys_file)


def roc_auc(labels: list[int], scores: list[float]) -> float:
    """AUC via the rank-sum identity, where a HIGHER score is better.

    Vina affinities are negative (more negative = better binder), so callers
    must pass ``-affinity``. Getting this backwards inverts every active and
    reports AUC < 0.5 — which looks like a docking bug but is a sign error.
    """
    pairs = sorted(zip(scores, labels))
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum = sum(r for r, (_, lab) in zip(ranks, pairs) if lab == 1)
    return (rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def bootstrap_auc_ci(
    labels: list[int], scores: list[float], iters: int = BOOTSTRAP_ITERS, seed: int = 0
) -> tuple[float, float]:
    """Percentile 95% CI for AUC, resampling pairs with replacement."""
    rng = random.Random(seed)
    n = len(labels)
    aucs = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        a = roc_auc([labels[i] for i in idx], [scores[i] for i in idx])
        if a == a:  # skip NaN (a resample can be all one class)
            aucs.append(a)
    aucs.sort()
    return aucs[int(0.025 * len(aucs))], aucs[int(0.975 * len(aucs))]


def enrichment_factor(labels: list[int], scores: list[float], k: int) -> tuple[float, float, int]:
    """EF@k = (hits_k / k) / (n_actives / n_total). Higher score = ranks first.

    Also returns the maximum EF achievable at this prevalence — a perfect
    ranking would put all actives in the top k. Reported so EF@k is read
    against what it could possibly be, not against 1.0.
    """
    n_actives = sum(labels)
    n_total = len(labels)
    order = sorted(range(n_total), key=lambda i: -scores[i])  # higher score = better
    top = order[:k]
    hits = sum(labels[i] for i in top)
    ef = (hits / k) / (n_actives / n_total) if n_actives else float("nan")
    ef_max = (min(k, n_actives) / k) / (n_actives / n_total) if n_actives else float("nan")
    return ef, ef_max, hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-actives", type=int, default=25)
    ap.add_argument("--n-decoys", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--exhaustiveness", type=int, default=8)
    args = ap.parse_args()

    actives_all, decoys_all = fetch_dataset()
    # Seeded sample: the head of the file is one chemotype, which would make a
    # seeded pass meaningless.
    rng = random.Random(args.seed)
    rng.shuffle(actives_all)
    rng.shuffle(decoys_all)
    actives = actives_all[: args.n_actives]
    decoys = decoys_all[: args.n_decoys]
    print(
        f"sample: {len(actives)} actives + {len(decoys)} decoys "
        f"({len(actives_all)}/{len(decoys_all)} available), seed={args.seed}"
    )

    _, center = inspect_receptor(PDB_ID)
    receptor = prepare_receptor(PDB_ID, center)
    print(f"receptor: {receptor.name} (via get_receptor for {PDB_ID}) box={center}")

    labels: list[int] = []
    scores: list[float] = []
    failures = 0
    t0 = time.time()
    for label, group in ((1, actives), (0, decoys)):
        for i, smi in enumerate(group, 1):
            pdbqt = prep_ligand(smi)
            if pdbqt is None:
                failures += 1
                print(f"  [{'A' if label else 'D'}{i:03d}] prep failed: {smi[:50]}")
                continue
            affinity, _ = dock(pdbqt, receptor, center, exhaustiveness=args.exhaustiveness)
            if affinity is None:
                failures += 1
                print(f"  [{'A' if label else 'D'}{i:03d}] dock failed")
                continue
            labels.append(label)
            # Negate: Vina reports "more negative is better", while AUC/EF rank
            # "higher is better". Without this every active looks worse than
            # every decoy and AUC lands below 0.5.
            scores.append(-affinity)
            print(f"  [{'A' if label else 'D'}{i:03d}] {affinity:7.2f}  {smi[:50]}")

    dt = time.time() - t0
    n = len(labels)
    print(f"\ndocked {n} molecules in {dt:.0f}s ({dt / max(n, 1):.1f}s each), {failures} failures")
    if not labels or sum(labels) == 0 or sum(labels) == n:
        print("not enough actives or decoys to score — refusing to report a gate")
        return 2

    auc = roc_auc(labels, scores)
    lo, hi = bootstrap_auc_ci(labels, scores)
    print(f"\n=== DUD-E {TARGET} docking smoke test (not a benchmark) ===")
    print(f"n = {n}  actives = {sum(labels)}  decoys = {n - sum(labels)}")
    print(f"ROC AUC = {auc:.3f}   bootstrap 95% CI [{lo:.3f}, {hi:.3f}]   gate = {AUC_GATE}")
    for k in (1, 5, 10):
        ef, ef_max, hits = enrichment_factor(labels, scores, k)
        print(f"EF@{k:<2d} = {ef:.2f}   (max possible at this prevalence: {ef_max:.2f}, hits {hits}/{k})")

    if auc >= AUC_GATE:
        print(f"\nPASS: AUC {auc:.3f} >= {AUC_GATE}")
        return 0
    print(
        f"\nFAIL: AUC {auc:.3f} < {AUC_GATE}. This is a signal to investigate, "
        "not proof of a bug — check the bounding box, then receptor prep, then "
        "protonation. Do not lower the threshold to make this pass."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
