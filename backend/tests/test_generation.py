from fastapi.testclient import TestClient

from app.generation.evaluate import evaluate


class FakeBackend:
    name = "fake"

    def __init__(self, smiles: list[str]) -> None:
        self._smiles = smiles
        self.seen: dict = {}

    def generate(self, n, mw_range=None, logp_range=None, seed=None):
        self.seen = {"n": n, "mw_range": mw_range, "logp_range": logp_range, "seed": seed}
        return self._smiles[:n]


def test_metrics_hand_computed():
    m = evaluate(["CCO", "CCO", "CCN", "not-a-mol", "c1ccccc1"], {"CCO"}, 5)
    assert (m.n_valid, m.validity, m.uniqueness, m.novelty) == (4, 0.8, 0.75, 0.6667)
    assert 0.0 < m.diversity <= 1.0


def test_metrics_empty():
    m = evaluate([], set(), 0)
    assert (m.validity, m.uniqueness, m.novelty, m.diversity) == (0.0, 0.0, 0.0, 0.0)


def test_backend_contract():
    backend = FakeBackend(["CCO", "CCN"])
    assert backend.generate(2, (100, 300), (-1, 3), seed=7) == ["CCO", "CCN"]
    assert backend.seen == {"n": 2, "mw_range": (100, 300), "logp_range": (-1, 3), "seed": 7}


def test_generate_bad_range_422(client: TestClient):
    r = client.post("/jobs/generate", json={"n": 5, "mw_min": 500, "mw_max": 100})
    assert r.status_code == 422
