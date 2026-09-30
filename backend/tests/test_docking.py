from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.docking import (
    FORMULA_VERSION,
    MAX_LIGAND_HEAVY_ATOMS,
    UnknownPDBError,
    _validate_pdb_id,
    find_cocrystal_ligand,
    ligand_centroid,
    parse_affinity,
    prep_ligand,
    rank_batch,
)


def _hetatm(serial: int, resname: str, x: float, element: str = "C") -> str:
    return (
        f"HETATM{serial:5d}  C   {resname} A{serial:4d}    "
        f"{x:8.3f}{10.0:8.3f}{20.0:8.3f}  1.00 20.00          {element:>2s}"
    )


def _pdb(*hetatm_lines: str) -> str:
    atom = (
        "ATOM      1  N   MET A   1      40.000  10.000  60.000"
        "  1.00 20.00           N"
    )
    return "\n".join([atom, *hetatm_lines]) + "\n"


AQ4 = _pdb(*[_hetatm(i, "AQ4", 22.0 + i) for i in range(29)], _hetatm(90, "HOH", 99.0, "O"))


def test_centroid_and_cocrystal_pick():
    center = ligand_centroid(AQ4, "AQ4")
    assert center is not None
    hit = find_cocrystal_ligand(AQ4)
    assert hit is not None and hit[0] == "AQ4" and hit[1] == center


def test_cocrystal_threshold_and_exclusions():
    # 1M17/AQ4 (erlotinib) clears the heavy-atom bar comfortably.
    assert find_cocrystal_ligand(AQ4) is not None
    # A lone sulfate/zinc is not a ligand -> 422, not a confident dock.
    additives = _pdb(_hetatm(1, "SO4", 10.0, "S"), _hetatm(2, "ZN", 11.0, "ZN"))
    assert find_cocrystal_ligand(additives) is None
    # MSE is a modified residue: 9 heavy atoms, passes the count check, so it
    # must be excluded by name.
    mse = _pdb(*[_hetatm(i, "MSE", 20.0 + i) for i in range(9)])
    assert find_cocrystal_ligand(mse) is None
    # Too small to be a real ligand.
    small = _pdb(*[_hetatm(i, "XYZ", 20.0 + i) for i in range(5)])
    assert find_cocrystal_ligand(small) is None
    # Water alone is nothing.
    assert find_cocrystal_ligand(_pdb(_hetatm(1, "HOH", 5.0, "O"))) is None


def test_cocrystal_picks_largest_not_first():
    # "First" would be arbitrary in a multi-ligand structure.
    both = _pdb(
        *[_hetatm(i, "SML", 20.0 + i) for i in range(8)],
        *[_hetatm(50 + i, "BIG", 40.0 + i) for i in range(20)],
    )
    hit = find_cocrystal_ligand(both)
    assert hit is not None and hit[0] == "BIG"


def test_pdb_id_validation_blocks_traversal():
    for bad in ("../x", "../../etc/passwd", "1M1", "1M177", "xM17", "", "1M17;rm"):
        with pytest.raises(ValueError):
            _validate_pdb_id(bad)
    assert _validate_pdb_id("1m17") == "1M17"
    assert _validate_pdb_id(" 1M17 ") == "1M17"


def test_oversized_ligand_excluded_not_docked():
    assert prep_ligand("C" * (MAX_LIGAND_HEAVY_ATOMS + 1)) is None


def test_multifragment_ligand_keeps_parent_and_never_raises():
    """Salts/dotted SMILES are multi-fragment; Meeko rejects those outright.
    We strip to the parent, and no molecule may raise out of prep_ligand."""
    asprin_salt = "CC(=O)Oc1ccccc1C(=O)O.Cl"
    assert prep_ligand(asprin_salt) is not None
    assert prep_ligand("CCO.CCN") is not None
    for bad in ("not-a-molecule", "C" * (MAX_LIGAND_HEAVY_ATOMS + 1), "[Nope]"):
        assert prep_ligand(bad) is None


def test_unknown_pdb_error_is_distinct():
    assert issubclass(UnknownPDBError, ValueError)


def test_rank_math_hand_computed():
    rows = [
        {"smiles": "a", "affinity": -9.0, "qed": 0.6, "novelty": 0.5},
        {"smiles": "b", "affinity": -7.0, "qed": 0.9, "novelty": 0.9},
        {"smiles": "c", "affinity": None, "qed": None, "novelty": None},
    ]
    out = rank_batch(rows)
    # hi=-7, lo=-9, span=2: a norm=1.0 -> 0.5+0.18+0.10=0.78; b norm=0.0 -> 0+0.27+0.18=0.45
    assert [r["smiles"] for r in out] == ["a", "b", "c"]
    assert out[0]["norm_affinity"] == 1.0
    assert out[0]["rank_score"] == 0.78
    assert out[1]["rank_score"] == 0.45
    assert out[2]["rank_score"] is None
    assert all(r["formula_version"] == FORMULA_VERSION for r in out)


def test_rank_all_equal_affinities():
    rows = [
        {"smiles": "a", "affinity": -8.0, "qed": 0.5, "novelty": 0.5},
        {"smiles": "b", "affinity": -8.0, "qed": 0.7, "novelty": 0.1},
    ]
    out = rank_batch(rows)
    assert all(r["norm_affinity"] == 1.0 for r in out)
    assert out[0]["rank_score"] == round(0.5 + 0.3 * 0.5 + 0.2 * 0.5, 4)
    assert out[0]["smiles"] == "a"


def test_parse_affinity_from_real_fixture():
    fixture = Path(__file__).parent / "fixtures" / "vina_out_sample.pdbqt"
    if not fixture.exists():
        pytest.skip("fixture not generated yet")
    assert parse_affinity(fixture.read_text()) is not None


def test_parse_affinity_degenerate_inputs():
    assert parse_affinity("") is None
    assert parse_affinity("MODEL 1\nATOM 1 C\nENDMDL\n") is None
    assert parse_affinity("REMARK VINA RESULT:\n") is None
    assert parse_affinity("REMARK VINA RESULT:  nonsense  0.0  0.0\n") is None


def test_dock_with_fake_runner_needs_no_binary():
    from app.docking import dock

    fixture = Path(__file__).parent / "fixtures" / "vina_out_sample.pdbqt"

    def fake_ok(cmd: list[str]) -> tuple[int, str, str]:
        Path(cmd[cmd.index("--out") + 1]).write_text(
            "REMARK VINA RESULT:    -7.4      0.000      0.000\n"
        )
        return 0, "ok", ""

    def fake_nonzero(cmd: list[str]) -> tuple[int, str, str]:
        return 1, "", "Error: could not parse input"

    affinity, pose = dock("FAKE", "fake.pdbqt", (0.0, 0.0, 0.0), runner=fake_ok)
    assert affinity == -7.4 and pose is not None

    # A non-zero exit must be distinguishable from a normal empty run.
    assert dock("FAKE", "fake.pdbqt", (0.0, 0.0, 0.0), runner=fake_nonzero) == (None, None)

    if fixture.exists():
        def fake_fixture(cmd: list[str]) -> tuple[int, str, str]:
            Path(cmd[cmd.index("--out") + 1]).write_text(fixture.read_text())
            return 0, "", ""

        aff, _ = dock("FAKE", "fake.pdbqt", (0.0, 0.0, 0.0), runner=fake_fixture)
        assert aff is not None and aff < 0


def test_dock_no_pdb_id_422(client: TestClient):
    project = client.post("/projects", json={"seed_smiles": "CCO"}).json()
    r = client.post(
        f"/projects/{project['project']['id']}/dock",
        json={"candidate_smiles": ["CCO"]},
    )
    assert r.status_code == 422


def test_dock_bad_smiles_422(client: TestClient):
    project = client.post(
        "/projects", json={"pdb_id": "1M17", "seed_smiles": "CCO"}
    ).json()
    r = client.post(
        f"/projects/{project['project']['id']}/dock",
        json={"candidate_smiles": ["not-a-molecule"]},
    )
    assert r.status_code == 422


def test_dock_unknown_project_404(client: TestClient):
    r = client.post("/projects/999999/dock", json={"candidate_smiles": ["CCO"]})
    assert r.status_code == 404


def test_dock_batch_capped_422(client: TestClient):
    project = client.post(
        "/projects", json={"pdb_id": "1M17", "seed_smiles": "CCO"}
    ).json()
    r = client.post(
        f"/projects/{project['project']['id']}/dock",
        json={"candidate_smiles": ["CCO"] * 51},
    )
    assert r.status_code == 422


def test_create_project_rejects_bad_pdb_id(client: TestClient):
    r = client.post("/projects", json={"pdb_id": "../../x", "seed_smiles": "CCO"})
    assert r.status_code == 422


def test_dock_unknown_pdb_422_and_unreachable_502(client: TestClient, monkeypatch):
    project = client.post(
        "/projects", json={"pdb_id": "9ZZZ", "seed_smiles": "CCO"}
    ).json()
    pid = project["project"]["id"]

    from app import docking

    def raise_404(pdb_id, dest):
        raise docking.UnknownPDBError(f"unknown PDB ID {pdb_id}")

    monkeypatch.setattr(docking, "_fetch_pdb", raise_404)
    r = client.post(f"/projects/{pid}/dock", json={"candidate_smiles": ["CCO"]})
    assert r.status_code == 422

    def raise_fetch(pdb_id, dest):
        raise docking.ReceptorFetchError("connection refused")

    monkeypatch.setattr(docking, "_fetch_pdb", raise_fetch)
    r = client.post(f"/projects/{pid}/dock", json={"candidate_smiles": ["CCO"]})
    assert r.status_code == 502


def test_fetch_pdb_wraps_network_failure(monkeypatch, tmp_path):
    """A raw network error must never escape _fetch_pdb as a 500."""
    import urllib.error

    from app import docking

    def urlopen(url, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with pytest.raises(docking.ReceptorFetchError):
        docking._fetch_pdb("1M17", tmp_path / "1M17.pdb")


def test_fetch_pdb_wraps_missing_structure(monkeypatch, tmp_path):
    import urllib.error

    from app import docking

    def urlopen(url, timeout=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with pytest.raises(docking.UnknownPDBError):
        docking._fetch_pdb("9ZZZ", tmp_path / "9ZZZ.pdb")


def test_docking_detail_404_for_unknown_result(client: TestClient):
    r = client.get("/projects/1/docking/999999")
    assert r.status_code == 404


def test_dock_job_payload_ids_and_properties(client: TestClient, monkeypatch):
    """The ranked rows must carry persisted ids (the pose viewer fetches by id)
    and the real property breakdown — never a placeholder."""
    import asyncio

    from app import docking
    from app.db import SessionLocal
    from app.models.docking import DockingResult
    from app.workers import tasks

    project = client.post(
        "/projects", json={"pdb_id": "1M17", "seed_smiles": "CCO"}
    ).json()
    pid = project["project"]["id"]

    # Stub the expensive parts: receptor prep and the Vina subprocess.
    monkeypatch.setattr(docking, "inspect_receptor", lambda p: (None, (0.0, 0.0, 0.0)))
    monkeypatch.setattr(docking, "prepare_receptor", lambda p, c: None)
    monkeypatch.setattr(docking, "dock", lambda *a, **k: (-7.5, "REMARK VINA RESULT:  -7.5  0  0\n"))

    result = tasks.dock_molecules.run(pid, "1M17", ["CCO", "CCN"])

    ranked = result["ranked"]
    assert len(ranked) == 2
    assert all(r["id"] is not None for r in ranked)
    assert ranked[0]["affinity"] == -7.5
    assert "properties" in ranked[0]
    assert ranked[0]["properties"]["qed"] > 0
    assert result["formula"] == docking.FORMULA
    assert result["formula_version"] == docking.FORMULA_VERSION
    # Affinities equal -> norm 1.0 for both, QED decides the order.
    assert all(r["norm_affinity"] == 1.0 for r in ranked)
    # Pose text must be persisted, not left in the payload.
    assert "pose" not in ranked[0]

    async def check_rows():
        async with SessionLocal() as s:
            rows = (await s.execute(
                select(DockingResult).where(DockingResult.project_id == pid)
            )).scalars().all()
            return rows

    rows = asyncio.run(check_rows())
    assert len(rows) == 2
    assert all(r.pose_pdbqt for r in rows)
    assert {r.id for r in rows} == {r["id"] for r in ranked}
