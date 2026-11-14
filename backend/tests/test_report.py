"""V8 Report Agent & Research Notebook tests.

Covers the previously-untested LLM success path (mocked httpx 200), the
per-candidate fallback, the enforced verification sentence, the zero-survivor
report (V7 routing regression), the candidate cap, exports, shortlist and
history.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.workers.celery_app import celery

celery.conf.update(
    task_always_eager=True,
    task_store_eager_result=True,
    result_backend="cache+memory://",
)

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
IBUPROFEN = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"


def _docked(smiles: str, score: float = 0.8, affinity: float = -7.5) -> dict:
    return {
        "id": None,
        "smiles": smiles,
        "affinity": affinity,
        "qed": 0.55,
        "novelty": 0.1,
        "rank_score": score,
        "properties": {},
    }


def _state(**overrides) -> dict:
    state = {
        "project_id": 1,
        "run_id": 1,
        "conditioning": {
            "mode": "retrieval-conditioned",
            "seed_smiles": ASPIRIN,
            "similarity": 1.0,
        },
        "dock_results": [_docked(ASPIRIN, 0.86), _docked(IBUPROFEN, 0.66)],
        "dock_formula": "rank_score = 0.5 * norm_affinity + 0.3 * QED + 0.2 * novelty",
        "dock_formula_version": "v6-1",
        "terminal_reason": None,
    }
    state.update(overrides)
    return state


# ── report payload ───────────────────────────────────────────────────


def test_template_provider_grounds_in_real_numbers():
    from app.report.agent import build_report

    payload = build_report(1, 1, _state())
    assert payload["candidates"], "expected rationales"
    first = payload["candidates"][0]
    assert first["rationale_source"] == "template-fallback"
    assert "7.50" in first["rationale"]  # affinity actually quoted
    assert "requires human/wet-lab verification" in first["rationale"]
    assert payload["formula"] and payload["formula_version"] == "v6-1"
    assert "not validated drug candidates" in payload["disclaimer"]


def test_llm_success_path_is_parsed_and_attributed():
    """The one path that actually calls out: a mocked httpx 200 must be parsed
    and rationale_source must report the model."""
    from app import llm as llm_mod

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "choices": [{"message": {"content": "This candidate binds well. Requires human/wet-lab verification."}}]
    }

    provider = llm_mod.OpenAICompatibleProvider("https://example.test/v1", "k", "test-model")
    with patch("httpx.post", return_value=fake_resp) as post:
        out = provider.complete("system", "facts")
    assert out.startswith("This candidate binds well")
    assert post.call_count == 1
    assert provider.name == "llm:test-model"

    # And the agent records it.
    from app.report import agent as agent_mod

    with patch.object(agent_mod, "get_provider", return_value=provider), patch(
        "httpx.post", return_value=fake_resp
    ):
        payload = agent_mod.build_report(1, 1, _state())
    assert payload["candidates"][0]["rationale_source"] == "llm:test-model"
    assert payload["model"] == "llm:test-model"


def test_llm_failure_falls_back_per_candidate():
    from app.llm import LLMError
    from app.report import agent as agent_mod

    class FailingProvider:
        name = "llm:broken"

        def complete(self, system, prompt):
            raise LLMError("timeout")

    with patch.object(agent_mod, "get_provider", return_value=FailingProvider()):
        payload = agent_mod.build_report(1, 1, _state())
    assert payload["candidates"]
    assert all(c["rationale_source"] == "template-fallback" for c in payload["candidates"])
    assert all("requires human/wet-lab verification" in c["rationale"] for c in payload["candidates"])


def test_missing_verification_sentence_is_appended_by_code():
    from app.report import agent as agent_mod

    class TerseProvider:
        name = "llm:terse"

        def complete(self, system, prompt):
            return "Binds well."

    with patch.object(agent_mod, "get_provider", return_value=TerseProvider()):
        payload = agent_mod.build_report(1, 1, _state())
    assert "requires human/wet-lab verification" in payload["candidates"][0]["rationale"]


def test_zero_survivor_report_is_explicit():
    from app.report.agent import build_report

    payload = build_report(
        1, 1, _state(dock_results=[], terminal_reason="no_candidates_passed_property_filter")
    )
    assert payload["candidates"] == []
    assert payload["terminal_reason"] == "no_candidates_passed_property_filter"
    assert "No candidates survived property filtering" in payload["summary"]
    assert payload["disclaimer"]


def test_candidate_cap():
    from app.report.agent import MAX_REPORT_CANDIDATES, build_report

    many = [_docked(ASPIRIN, 1.0 - i / 100) for i in range(50)]
    payload = build_report(1, 1, _state(dock_results=many))
    assert len(payload["candidates"]) == MAX_REPORT_CANDIDATES


# ── graph: zero-survivor routing regression ──────────────────────────


def test_zero_survivor_routes_property_filter_to_report_not_keyerror():
    """V7's map had no "done" key, so a zero-survivor run raised KeyError.
    V8 routes property_filter -> report -> done."""
    from app.orchestration.graph import _after_property_filter, _after_report

    assert _after_property_filter({"property_passed": []}) == "report"
    assert _after_report({"report_done": True}) == "done"


def test_report_node_skipped_when_not_in_route():
    from app.orchestration.graph import report_node

    out = report_node({"stages": ["dock"], "trace": []})
    assert out["trace"][-1]["event"] == "skip"


# ── API: report + exports ────────────────────────────────────────────


def _make_project_with_report(client: TestClient) -> int:
    from app import db
    from app.models.pipeline import PipelineRun
    from app.models.report import Report
    from app.report.agent import build_report

    project = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1}).json()
    pid = project["project"]["id"]

    import asyncio

    async def _seed():
        async with db.SessionLocal() as s:
            run = PipelineRun(
                project_id=pid, route="new_project", status="success",
                current_stage="done", state_json=json.dumps({}),
            )
            s.add(run)
            await s.flush()
            payload = build_report(pid, run.id, _state(project_id=pid, run_id=run.id))
            s.add(
                Report(
                    project_id=pid,
                    pipeline_run_id=run.id,
                    payload_json=json.dumps(payload),
                    model=payload["model"],
                )
            )
            await s.commit()

    asyncio.run(_seed())
    return pid


def test_get_report_404_then_200(client: TestClient):
    project = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1}).json()
    pid = project["project"]["id"]
    assert client.get(f"/projects/{pid}/report").status_code == 404
    pid = _make_project_with_report(client)
    r = client.get(f"/projects/{pid}/report")
    assert r.status_code == 200
    assert r.json()["payload"]["candidates"]


def test_export_sdf(client: TestClient):
    pid = _make_project_with_report(client)
    r = client.get(f"/projects/{pid}/report/export.sdf")
    assert r.status_code == 200
    body = r.content.decode()
    assert ASPIRIN in body
    assert "requires human/wet-lab verification" in body
    assert "attachment" in r.headers["content-disposition"]


def test_export_pdf(client: TestClient):
    pytest.importorskip("reportlab")
    pid = _make_project_with_report(client)
    r = client.get(f"/projects/{pid}/report/export.pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


# ── shortlist ────────────────────────────────────────────────────────


def test_shortlist_add_list_duplicate_delete(client: TestClient):
    project = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1}).json()
    pid = project["project"]["id"]
    r = client.post(f"/projects/{pid}/shortlist", json={"smiles": ASPIRIN})
    assert r.status_code == 201, r.text
    item_id = r.json()["id"]
    # duplicate -> 409
    assert client.post(f"/projects/{pid}/shortlist", json={"smiles": ASPIRIN}).status_code == 409
    listed = client.get(f"/projects/{pid}/shortlist").json()
    assert [i["candidate_smiles"] for i in listed] == [ASPIRIN]
    assert client.delete(f"/projects/{pid}/shortlist/{item_id}").status_code == 204
    assert client.get(f"/projects/{pid}/shortlist").json() == []


def test_shortlist_unknown_project_404(client: TestClient):
    assert client.post("/projects/999999/shortlist", json={"smiles": ASPIRIN}).status_code == 404


# ── history ──────────────────────────────────────────────────────────


def test_history_shows_prior_runs_and_shortlist_count(client: TestClient):
    from app import db
    from app.models.pipeline import PipelineRun

    project = client.post("/projects", json={"seed_smiles": ASPIRIN, "limit": 1}).json()
    pid = project["project"]["id"]
    client.post(f"/projects/{pid}/shortlist", json={"smiles": ASPIRIN})

    import asyncio

    async def _seed():
        async with db.SessionLocal() as s:
            s.add(
                PipelineRun(
                    project_id=pid, route="new_project", status="success",
                    current_stage="done",
                    state_json=json.dumps(
                        {"generate_results": [{"smiles": ASPIRIN}] * 3,
                         "dock_results": [_docked(ASPIRIN)] * 2}
                    ),
                )
            )
            await s.commit()

    asyncio.run(_seed())
    h = client.get(f"/projects/{pid}/history").json()
    assert h["has_history"] is True
    assert len(h["runs"]) >= 1
    assert h["runs"][0]["candidate_count"] == 3
    assert h["runs"][0]["ranked_count"] == 2
    assert h["shortlist_count"] == 1
