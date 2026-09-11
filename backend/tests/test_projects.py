from fastapi.testclient import TestClient

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"


def test_create_by_smiles_self_hit(client: TestClient):
    r = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["project"]["seed_source"] == "smiles"
    assert body["seed_resolved"] == ASPIRIN
    top = body["results"][0]
    assert top["similarity"] == 1.0
    assert top["citation"]["database"] == "ChEMBL"
    assert top["citation"]["url"].endswith(top["citation"]["entry_id"])
    assert len(body["results"]) == 3


def test_create_by_name_resolves(client: TestClient):
    r = client.post("/projects", json={"seed_name": "aspirin"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["project"]["seed_source"] == "name"
    assert body["seed_resolved"] == ASPIRIN
    assert body["results"][0]["similarity"] == 1.0


def test_unknown_name_422(client: TestClient):
    r = client.post("/projects", json={"seed_name": "not-a-real-drug-xyz"})
    assert r.status_code == 422


def test_bad_smiles_422(client: TestClient):
    r = client.post("/projects", json={"seed_smiles": "not-a-molecule"})
    assert r.status_code == 422


def test_empty_body_422(client: TestClient):
    r = client.post("/projects", json={})
    assert r.status_code == 422


def test_both_seeds_422(client: TestClient):
    r = client.post("/projects", json={"seed_smiles": ASPIRIN, "seed_name": "ASPIRIN"})
    assert r.status_code == 422


def test_target_only_honest_empty(client: TestClient):
    r = client.post("/projects", json={"pdb_id": "1ABC"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["results"] == []
    assert "1ABC" in body["message"]


def test_project_ids_increment(client: TestClient):
    r1 = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1})
    r2 = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["project"]["id"] > r1.json()["project"]["id"]
