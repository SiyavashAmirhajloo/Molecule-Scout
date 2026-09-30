"""E2E verification against the LIVE Docker stack (api on :8000)."""

import json
import time
import urllib.error
import urllib.request

API = "http://localhost:8000"
ERLOTINIB = "COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC"
GEFITINIB = "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1"
ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"


def post(path, body):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def get(path):
    try:
        with urllib.request.urlopen(API + path, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def main():
    print("=== health ===")
    s, h = get("/health")
    print(f"  {s} {h}")

    print("\n=== create project (1M17 + erlotinib seed) ===")
    s, p = post("/projects", {"pdb_id": "1M17", "seed_smiles": ERLOTINIB, "limit": 3})
    print(f"  {s} project={p['project']['id']} hits={len(p['results'])}")
    pid = p["project"]["id"]

    print("\n=== dock 3 real molecules ===")
    s, j = post(f"/projects/{pid}/dock",
                {"candidate_smiles": [GEFITINIB, ERLOTINIB, ASPIRIN]})
    print(f"  enqueue {s} job={j.get('id','')[:8]}")
    job = j["id"]

    for _ in range(120):
        s, st = get(f"/jobs/{job}")
        if st["status"] in ("success", "failure"):
            break
        time.sleep(2)
    print(f"  job status: {st['status']}")
    if st["status"] == "failure":
        print(f"  ERROR: {st.get('error')}")
        return 1

    res = st["result"]
    print(f"  formula: {res['formula']}")
    print(f"  version: {res['formula_version']}")
    print(f"  receptor: {res['receptor']['pdb_id']}")
    for r in res["ranked"]:
        print(f"    score={r['rank_score']} aff={r['affinity']} "
              f"qed={r['qed']} nov={r['novelty']} {r['smiles'][:40]}")

    print("\n=== fetch pose by result id ===")
    best = res["ranked"][0]
    s, d = get(f"/projects/{pid}/docking/{best['id']}")
    print(f"  {s} aff={d.get('affinity')} pose_bytes={len(d.get('pose_pdbqt') or '')}")
    print(f"  VINA RESULT present: {'REMARK VINA RESULT' in (d.get('pose_pdbqt') or '')}")

    print("\n=== error mapping ===")
    s, _ = post("/projects", {"pdb_id": "../../x", "seed_smiles": "CCO"})
    print(f"  traversal pdb_id -> {s} (expect 422)")
    s, _ = post(f"/projects/{pid}/dock", {"candidate_smiles": ["CCO"] * 51})
    print(f"  oversized batch -> {s} (expect 422)")
    s, _ = get(f"/projects/{pid}/docking/999999")
    print(f"  unknown result id -> {s} (expect 404)")

    print("\n=== receptor cache (Docker volume) ===")
    import subprocess
    out = subprocess.run(
        ["docker", "compose", "exec", "-T", "worker",
         "ls", "-la", "/code/cache/receptors/"],
        capture_output=True, text=True, timeout=60,
    )
    print("  " + "\n  ".join(out.stdout.strip().splitlines()[-6:]))

    print("\nE2E OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
