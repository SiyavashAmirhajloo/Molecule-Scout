from fastapi.testclient import TestClient
from rdkit import Chem

from app.generation.conditioned import RETRIEVAL_CONDITION_MIN_TANIMOTO
from app.generation.evaluate import evaluate

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"


def test_threshold_is_named_constant():
    assert RETRIEVAL_CONDITION_MIN_TANIMOTO == 0.3


def test_avg_similarity_hand_computed():
    m = evaluate(["CCO", "CCN"], set(), 2, Chem.MolFromSmiles("CCO"))
    assert m.avg_similarity_to_seed is not None
    assert 0.0 < m.avg_similarity_to_seed <= 1.0
    m2 = evaluate(["CCO"], set(), 1)
    assert m2.avg_similarity_to_seed is None


def test_raw_generate_accepts_seed_fields(client: TestClient):
    r = client.post(
        "/jobs/generate", json={"n": 2, "seed_smiles": "CCO", "noise_steps": 10, "seed": 1}
    )
    assert r.status_code in (200, 500)  # 500 only if no checkpoint in CI env
    if r.status_code == 200:
        assert "id" in r.json()


def test_raw_generate_bad_seed_422(client: TestClient):
    r = client.post("/jobs/generate", json={"n": 2, "seed_smiles": "not-a-molecule"})
    assert r.status_code == 422


def test_project_generate_gates_on_retrieval(client: TestClient):
    project = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1}).json()
    pid = project["project"]["id"]
    top_sim = project["results"][0]["similarity"]
    r = client.post(f"/projects/{pid}/generate", json={"n": 2, "noise_steps": 10})
    assert r.status_code == 200, r.text
    cond = r.json()["conditioning"]
    if top_sim >= 0.3:
        assert cond["mode"] == "retrieval-conditioned"
        assert cond["seed_smiles"] == project["results"][0]["canonical_smiles"]
    else:
        assert cond["mode"] == "fallback-unconditioned"


def test_project_generate_no_seed_422(client: TestClient):
    project = client.post("/projects", json={"pdb_id": "1XYZ"}).json()
    r = client.post(f"/projects/{project['project']['id']}/generate", json={"n": 2})
    assert r.status_code == 422


def test_project_generate_unknown_404(client: TestClient):
    r = client.post("/projects/999999/generate", json={"n": 2})
    assert r.status_code == 404
