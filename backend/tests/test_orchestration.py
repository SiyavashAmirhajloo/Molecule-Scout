"""V7 orchestration tests: coordinator routing, property gate, re-entry,
job failure, double-resume race, and the full new_project run.

Eager-mode semantics (celery task_always_eager=True): .delay() runs the task
synchronously and returns an EagerResult with NO .link/.link_error support.
So in tests the graph pauses at a slow stage (status=waiting) and the test
drives resume_run() explicitly — exactly what the Celery .link callback does
in production.

Patch discipline: tests patch the module-level seams in app.orchestration.graph
(retrieve) and the task objects (generate_molecules.delay) — the bindings the
nodes actually call at call time. A compiled LangGraph holds node references
from build time, so patching graph_mod.generate_node would NOT intercept the
compiled graph; patching the task the node calls would. Likewise, patching
app.agents.retrieval.retrieve would miss the local import inside the node
and let a regression false-pass.
"""

import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.workers.celery_app import celery

celery.conf.update(
    task_always_eager=True,
    task_store_eager_result=True,
    result_backend="cache+memory://",
)

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
# C32 alkane: parses fine but blows past MW/logP/SA gates — a valid
# candidate that only an explicit bypass can carry through property_filter.
GATE_FAILING = "C" * 32


def _seed_run(client, pid, route, state):
    """Insert a PipelineRun row; injects the new id into state_json."""
    from sqlalchemy import text

    from app.db import SessionLocal
    from app.models.pipeline import PipelineRun

    async def _work():
        async with SessionLocal() as s:
            run = PipelineRun(
                project_id=pid,
                route=route,
                status=state.get("status", "running"),
                current_stage=state.get("current_stage", "queued"),
                job_id=state.get("job_id"),
                state_json=json.dumps(state),
            )
            s.add(run)
            await s.flush()
            state["run_id"] = run.id
            await s.execute(
                text("UPDATE pipeline_runs SET state_json=:s WHERE id=:id"),
                {"s": json.dumps(state), "id": run.id},
            )
            await s.commit()
            return run.id

    import asyncio

    return asyncio.run(_work())


def _get_run(client, pid, run_id):
    return client.get(f"/projects/{pid}/run/{run_id}").json()


def _make_project(client, pdb_id=None):
    body = {"seed_smiles": ASPIRIN, "limit": 1}
    if pdb_id:
        body["pdb_id"] = pdb_id
    return client.post("/projects", json=body).json()


# ── coordinator routing ──────────────────────────────────────────────


def test_route_table_covers_all_request_types():
    from app.orchestration.state import REQUIRED_STAGES

    assert set(REQUIRED_STAGES) == {"new_project", "regenerate", "redock", "full_rerun"}
    assert REQUIRED_STAGES["new_project"] == [
        "retrieve",
        "generate",
        "property_filter",
        "dock",
    ]
    assert "retrieve" not in REQUIRED_STAGES["regenerate"]
    assert "retrieve" not in REQUIRED_STAGES["redock"]
    assert "generate" not in REQUIRED_STAGES["redock"]


def test_coordinator_node_sets_stages():
    from app.orchestration.graph import coordinator

    out = coordinator({"request_type": "regenerate", "project_id": 1})
    assert out["route"] == "regenerate"
    assert out["stages"] == ["generate", "property_filter", "dock"]
    assert out["trace"][-1]["node"] == "coordinator"


# ── property gate ────────────────────────────────────────────────────


def test_property_filter_rejects_and_records_reasons():
    from app.orchestration.graph import property_filter_node

    out = property_filter_node(
        {
            "stages": ["property_filter", "dock"],
            "generate_results": [
                {"smiles": ASPIRIN},
                {"smiles": "not-a-molecule"},
            ],
        }
    )
    assert ASPIRIN in out["property_passed"]
    assert out["property_rejected"] == [
        {"smiles": "not-a-molecule", "gate_reason": "invalid_smiles"}
    ]
    assert out["property_done"] is True


def test_property_filter_zero_survivors_is_terminal_not_error():
    from app.orchestration.graph import property_filter_node

    out = property_filter_node(
        {
            "stages": ["property_filter", "dock"],
            "generate_results": [{"smiles": "not-a-molecule"}],
        }
    )
    assert out["status"] == "success"
    assert out["terminal_reason"] == "no_candidates_passed_property_filter"
    assert "error" not in out


def test_property_filter_gates_reject_drug_unlike_molecule():
    from app.orchestration.graph import property_filter_node

    out = property_filter_node(
        {
            "stages": ["property_filter", "dock"],
            "generate_results": [{"smiles": GATE_FAILING}],
        }
    )
    assert out["property_passed"] == []
    assert out["property_rejected"][0]["gate_reason"] in {"QED", "SA", "Lipinski"}


def test_property_filter_explicit_smiles_bypasses_gate():
    from app.orchestration.graph import property_filter_node

    out = property_filter_node(
        {
            "stages": ["property_filter", "dock"],
            "candidate_smiles": [GATE_FAILING],
        }
    )
    assert out["property_passed"] == [GATE_FAILING]
    assert out["property_rejected"] == []


def test_gate_constants_are_named_and_disclosed():
    from app.orchestration import gates

    assert gates.PROPERTY_GATE_QED_MIN == 0.25
    assert gates.PROPERTY_GATE_SA_MAX == 6.0
    assert gates.PROPERTY_GATE_LIPINSKI_VIOLATIONS_MAX == 1
    assert gates.PROPERTY_GATE_PAINS_FREE is True


# ── re-entry: regenerate must not call retrieval ─────────────────────


def test_regenerate_does_not_call_retrieval(client: TestClient, monkeypatch):
    """Patch the module-level seam the node calls. The spy raises if touched,
    so a regression that re-runs retrieval cannot false-pass."""
    from app.orchestration import graph as graph_mod
    from app.workers import tasks

    project = _make_project(client)
    pid = project["project"]["id"]

    spy = MagicMock(side_effect=AssertionError("retrieval must not run"))
    monkeypatch.setattr(graph_mod, "retrieve", spy)
    monkeypatch.setattr(tasks.generate_molecules, "delay", MagicMock())

    _seed_run(
        client,
        pid,
        "new_project",
        {
            "status": "success",
            "current_stage": "done",
            "retrieve_results": project["results"],
            "retrieve_done": True,
            "seed_resolved": ASPIRIN,
            "conditioning": {"mode": "retrieval-conditioned", "seed_smiles": ASPIRIN},
        },
    )

    r = client.post(f"/projects/{pid}/run", json={"route": "regenerate", "n": 2})
    assert r.status_code == 200, r.text
    spy.assert_not_called()
    body = r.json()
    # Eager mode pauses at generate (waiting); no link callback in eager.
    assert body["status"] == "waiting"
    assert body["current_stage"] == "generate"


# ── redock reuses candidates ─────────────────────────────────────────


def test_redock_reuses_candidates_without_generation(client: TestClient, monkeypatch):
    from app.workers import tasks

    project = _make_project(client, pdb_id="1M17")
    pid = project["project"]["id"]

    gen_delay = MagicMock(side_effect=AssertionError("generate job must not run"))
    dock_delay = MagicMock(return_value=MagicMock(id="dock-job-1"))
    monkeypatch.setattr(tasks.generate_molecules, "delay", gen_delay)
    monkeypatch.setattr(tasks.dock_molecules, "delay", dock_delay)
    monkeypatch.setattr(
        "app.docking.inspect_receptor", lambda p: (None, (0.0, 0.0, 0.0))
    )

    _seed_run(
        client,
        pid,
        "new_project",
        {
            "status": "success",
            "current_stage": "done",
            "retrieve_results": project["results"],
            "retrieve_done": True,
            "generate_results": [{"smiles": ASPIRIN, "properties": {}}],
            "generate_done": True,
            "conditioning": {"mode": "retrieval-conditioned"},
        },
    )

    r = client.post(f"/projects/{pid}/run", json={"route": "redock"})
    assert r.status_code == 200, r.text
    gen_delay.assert_not_called()
    # Docking DID run from the reused candidates.
    assert dock_delay.call_count == 1
    assert ASPIRIN in dock_delay.call_args.args[2]


# ── job failure ──────────────────────────────────────────────────────


def test_failed_job_ends_in_failure(client: TestClient):
    project = _make_project(client)
    pid = project["project"]["id"]

    run_id = _seed_run(
        client,
        pid,
        "regenerate",
        {
            "request_type": "regenerate",
            "project_id": pid,
            "stages": ["generate", "property_filter", "dock"],
            "current_stage": "generate",
            "generate_job_id": "gen-job-1",
            "active_job_id": "gen-job-1",
            "status": "waiting",
            "orchestrate": True,
            "trace": [],
            "conditioning": {"mode": "retrieval-conditioned", "seed_smiles": ASPIRIN},
            "gen_n": 2,
            "gen_noise_steps": 100,
            "gen_seed": None,
            "pdb_id": None,
            "seed_smiles": ASPIRIN,
            "seed_resolved": ASPIRIN,
            "limit": 10,
            "candidate_smiles": None,
        },
    )

    from app.orchestration.graph import resume_run

    owned = resume_run(run_id, {"failed": True, "error": "vina exploded"}, "gen-job-1")
    assert owned is True

    body = _get_run(client, pid, run_id)
    assert body["status"] == "failure"
    assert "vina exploded" in body["state"]["error"]
    assert any(e["event"] == "job_failed" for e in body["trace"])


# ── double-resume race ───────────────────────────────────────────────


def test_double_resume_submits_next_job_exactly_once(client: TestClient, monkeypatch):
    """Two resume_run calls for one job: the CAS lets exactly one win, so the
    next stage's job is submitted once."""
    from app.workers import tasks

    project = _make_project(client, pdb_id="1M17")
    pid = project["project"]["id"]

    dock_calls = []

    def counting_dock_delay(*args, **kwargs):
        dock_calls.append(args)
        return MagicMock(id="dock-job-1")

    monkeypatch.setattr(tasks.dock_molecules, "delay", counting_dock_delay)
    monkeypatch.setattr(
        "app.docking.inspect_receptor", lambda p: (None, (0.0, 0.0, 0.0))
    )

    run_id = _seed_run(
        client,
        pid,
        "regenerate",
        {
            "request_type": "regenerate",
            "project_id": pid,
            "stages": ["generate", "property_filter", "dock"],
            "current_stage": "generate",
            "generate_job_id": "job-123",
            "active_job_id": "job-123",
            "status": "waiting",
            "orchestrate": True,
            "trace": [],
            "conditioning": {"mode": "retrieval-conditioned", "seed_smiles": ASPIRIN},
            "gen_n": 2,
            "gen_noise_steps": 100,
            "gen_seed": None,
            "pdb_id": "1M17",
            "seed_smiles": ASPIRIN,
            "seed_resolved": ASPIRIN,
            "limit": 10,
            "candidate_smiles": None,
        },
    )

    from app.orchestration.graph import resume_run

    job_result = {
        "candidates": [{"smiles": ASPIRIN, "properties": {}}],
        "metrics": {"validity": 1.0},
        "conditioning": {"mode": "retrieval-conditioned"},
    }
    first = resume_run(run_id, {"failed": False, "result": job_result}, "job-123")
    second = resume_run(run_id, {"failed": False, "result": job_result}, "job-123")

    assert first is True
    assert second is False
    assert len(dock_calls) == 1, f"expected 1 dock submission, got {len(dock_calls)}"


# ── full new_project run ─────────────────────────────────────────────


def test_full_new_project_run_end_to_end(client: TestClient, monkeypatch):
    """retrieve -> generate -> property_filter -> dock -> done, with the test
    driving resume_run() between stages — the eager-mode analogue of the
    production .link callbacks."""
    from app.workers import tasks

    project = _make_project(client, pdb_id="1M17")
    pid = project["project"]["id"]

    class _Job:
        def __init__(self, id):
            self.id = id

    gen_delay = MagicMock(return_value=_Job("gen-job-1"))
    dock_delay = MagicMock(return_value=_Job("dock-job-1"))
    monkeypatch.setattr(tasks.generate_molecules, "delay", gen_delay)
    monkeypatch.setattr(tasks.dock_molecules, "delay", dock_delay)
    monkeypatch.setattr(
        "app.docking.inspect_receptor", lambda p: (None, (0.0, 0.0, 0.0))
    )

    r = client.post(f"/projects/{pid}/run", json={"route": "new_project", "n": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    # Paused at generate: job submitted, waiting for the resume callback.
    assert body["status"] == "waiting"
    assert body["current_stage"] == "generate"
    run_id = body["run_id"]

    # Resume generate (what .link does in production).
    from app.orchestration.graph import resume_run

    owned = resume_run(
        run_id,
        {
            "failed": False,
            "result": {
                "candidates": [
                    {"smiles": ASPIRIN, "properties": {"qed": 0.55}},
                    {"smiles": "CCN", "properties": {"qed": 0.3}},
                ],
                "metrics": {"validity": 1.0},
                "conditioning": {"mode": "retrieval-conditioned", "seed_smiles": ASPIRIN},
            },
        },
        "gen-job-1",
    )
    assert owned is True
    body = _get_run(client, pid, run_id)
    assert body["status"] == "waiting"
    assert body["current_stage"] == "dock"
    assert dock_delay.call_count == 1

    # Resume dock.
    ranked = [
        {
            "smiles": s,
            "affinity": -7.5,
            "qed": 0.55,
            "novelty": 0.0,
            "rank_score": 0.78,
            "id": i + 1,
            "properties": {},
        }
        for i, s in enumerate([ASPIRIN, "CCN"])
    ]
    owned = resume_run(
        run_id,
        {
            "failed": False,
            "result": {
                "ranked": ranked,
                "formula": "rank_score = 0.5 * norm_affinity + 0.3 * QED + 0.2 * novelty",
                "formula_version": "v6-1",
                "receptor": {"pdb_id": "1M17", "center": [0.0, 0.0, 0.0]},
            },
        },
        "dock-job-1",
    )
    assert owned is True

    body = _get_run(client, pid, run_id)
    assert body["status"] == "success", body
    nodes = {e["node"] for e in body["trace"]}
    assert {
        "coordinator",
        "retrieve",
        "generate",
        "safety_screen",
        "property_filter",
        "dock",
        "done",
    } <= nodes
    assert len(body["state"]["dock_results"]) == 2
    assert body["state"]["dock_results"][0]["affinity"] == -7.5


# ── 409 on concurrent run ────────────────────────────────────────────


def test_concurrent_run_returns_409(client: TestClient):
    project = _make_project(client)
    pid = project["project"]["id"]

    _seed_run(client, pid, "new_project", {"status": "running"})

    r = client.post(f"/projects/{pid}/run", json={"route": "regenerate"})
    assert r.status_code == 409
