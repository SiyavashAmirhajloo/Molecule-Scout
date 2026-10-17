"""LangGraph workflow: coordinator -> retrieve -> generate -> safety_screen
-> property_filter -> dock -> done.

Nodes wrap the existing V1-V6 agent functions; no logic rewrite. Slow stages
(generate, dock) submit the existing Celery tasks. A full-orchestration run
(POST /projects/{id}/run) links resume_pipeline so the graph resumes when
the job lands. Per-stage endpoints (the existing UI) submit without a link
and poll the job themselves, exactly as in V1-V6.

Eager mode (tests, and `celery -A ... eager`): the job and its resume
callback run synchronously inside task.delay(). The submitting node
therefore reloads the run's state from the DB after submitting, so the outer
traversal continues from the resumed state instead of a stale copy that
would route past the completed stage.

safety_screen is an explicit pass-through slot for the V10 Safety Agent
(docs/architecture.md puts it between generation and property filtering):
V10 inserts screening logic there, with no re-plumb.
"""

import asyncio
import concurrent.futures
import json
import logging

from langgraph.graph import END, START, StateGraph

from app.orchestration.gates import (
    PROPERTY_GATE_LIPINSKI_VIOLATIONS_MAX,
    PROPERTY_GATE_PAINS_FREE,
    PROPERTY_GATE_QED_MIN,
    PROPERTY_GATE_SA_MAX,
)
from app.orchestration.state import REQUIRED_STAGES, trace

log = logging.getLogger(__name__)

ACTIVE_STATUSES = ("pending", "running", "waiting")


def _run_async(coro):
    """Drive a coroutine from sync graph code. One process-wide loop per
    process (see app/workers/tasks.py for the full rationale); hop a thread
    only when a loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


# ── module-level seams (the test surface) ────────────────────────────
# Retrieval and project lookups go through these names, not local imports,
# so a test can patch app.orchestration.graph.retrieve and observe calls.


def resolve_seed(seed_smiles: str | None, seed_name: str | None):
    """(canonical_smiles, error_detail). error_detail is set when the seed
    cannot be resolved (unknown name / invalid SMILES)."""
    from app import db
    from app.agents.retrieval import resolve_seed as agent_resolve_seed

    async def _work():
        async with db.SessionLocal() as s:
            return await agent_resolve_seed(s, seed_smiles, seed_name)

    try:
        resolved = _run_async(_work())
    except Exception as e:  # HTTPException(422) from resolve_seed
        return None, str(getattr(e, "detail", e))
    return (resolved[1] if resolved else None), None


def retrieve(seed_mol, limit: int):
    """[(KnownMolecule, similarity), ...] for the resolved seed."""
    from app import db
    from app.agents.retrieval import retrieve as agent_retrieve

    async def _work():
        async with db.SessionLocal() as s:
            return await agent_retrieve(s, seed_mol, limit)

    return _run_async(_work())


def _load_project(project_id: int):
    from sqlalchemy import select

    from app import db
    from app.models.project import Project

    async def _work():
        async with db.SessionLocal() as s:
            return (
                await s.execute(select(Project).where(Project.id == project_id))
            ).scalar_one_or_none()

    return _run_async(_work())


# ── run persistence ──────────────────────────────────────────────────


def save_run(run_id: int, state: dict, only_if_active: bool = True) -> None:
    """Persist state/status/stage/job_id. only_if_active never clobbers a
    terminal run with a stale late write."""
    from sqlalchemy import text

    from app import db

    guard = " AND status IN ('pending','running','waiting')" if only_if_active else ""

    async def _work() -> None:
        async with db.SessionLocal() as s:
            await s.execute(
                text(
                    "UPDATE pipeline_runs SET state_json=:s, status=:st, "
                    f"current_stage=:cs, job_id=:j WHERE id=:id{guard}"
                ),
                {
                    "s": json.dumps(state),
                    "st": state.get("status") or "running",
                    "cs": state.get("current_stage") or "",
                    "j": state.get("generate_job_id") or state.get("dock_job_id"),
                    "id": run_id,
                },
            )
            await s.commit()

    if run_id and state.get("orchestrate"):
        _run_async(_work())


def load_run_state(run_id: int) -> dict | None:
    from sqlalchemy import text

    from app import db

    async def _work():
        async with db.SessionLocal() as s:
            row = (
                await s.execute(
                    text("SELECT state_json FROM pipeline_runs WHERE id=:id"),
                    {"id": run_id},
                )
            ).mappings().one_or_none()
            return json.loads(row["state_json"]) if row else None

    return _run_async(_work())


def _set_job_id(run_id: int, job_id: str) -> None:
    from sqlalchemy import text

    from app import db

    async def _work() -> None:
        async with db.SessionLocal() as s:
            await s.execute(
                text(
                    "UPDATE pipeline_runs SET job_id=:j WHERE id=:id AND status='waiting'"
                ),
                {"j": job_id, "id": run_id},
            )
            await s.commit()

    _run_async(_work())


# ── job submission ───────────────────────────────────────────────────


def _submit_job(state: dict, task, job_key: str, *args) -> str | None:
    """Submit a Celery task and record its job id under job_key. Full-
    orchestration: mark waiting and persist BEFORE submitting — in eager mode
    the job runs inside .delay() and the resume CAS requires waiting.
    """
    if not (state.get("orchestrate") and state.get("run_id")):
        return task.delay(*args).id
    run_id = state["run_id"]
    state["status"] = "waiting"
    save_run(run_id, state)
    from app.workers.tasks import resume_pipeline

    result = task.delay(*args)
    # Eager mode (tests) returns EagerResult, which has no .link — the test
    # drives resume_run explicitly, the analogue of the production callback.
    raw_job_id = getattr(result, "id", None)
    if hasattr(result, "link") and isinstance(raw_job_id, str):
        # Pass the job id to the callback so its CAS can pin the exact job
        # this result belongs to — a stale resume for an older job then fails
        # the WHERE instead of resuming a run that has already moved on.
        result.link(resume_pipeline.s(run_id, raw_job_id))
        result.link_error(resume_pipeline.s(run_id, raw_job_id))
    if isinstance(raw_job_id, str):
        state[job_key] = raw_job_id
        state["active_job_id"] = raw_job_id
        _set_job_id(run_id, raw_job_id)
    # The job plus its resume callback may already have run inside .delay()
    # (eager). Adopt the row's state so the outer traversal doesn't walk
    # past a completed stage or duplicate work.
    resumed = load_run_state(run_id)
    if resumed:
        state.update(resumed)
        if isinstance(raw_job_id, str):
            state[job_key] = raw_job_id
            state["active_job_id"] = raw_job_id
    return raw_job_id if isinstance(raw_job_id, str) else None
    # Adopt the resumed state so the outer traversal doesn't walk past a
    # stage that just finished (eager) or duplicate work (production).
    resumed = load_run_state(run_id)
    if resumed:
        state.update(resumed)
    return result.id


# ── nodes ────────────────────────────────────────────────────────────


def coordinator(state: dict) -> dict:
    """Deterministic route table — not an LLM agent (disclosed in README)."""
    route = state["request_type"]
    stages = list(REQUIRED_STAGES[route])
    stop = state.get("stop_after")
    if stop in stages:
        stages = stages[: stages.index(stop) + 1]
    state["route"] = route
    state["stages"] = stages
    state["current_stage"] = "coordinator"
    trace(state, "coordinator", "exit", f"route={route} stages={','.join(stages)}")
    return state


def retrieve_node(state: dict) -> dict:
    if "retrieve" not in state["stages"] or state.get("retrieve_done"):
        trace(state, "retrieve", "skip", "not in route or already done")
        return state
    from app.agents.properties import compute_properties
    from app.chem.embeddings import parse_smiles

    state["current_stage"] = "retrieve"
    trace(state, "retrieve", "enter", None)
    seed_smiles, seed_name = state.get("seed_smiles"), state.get("seed_name")
    # One seed field accepts either form: an unparseable string is a name.
    if seed_smiles and parse_smiles(seed_smiles) is None:
        seed_name, seed_smiles = seed_smiles, None
    resolved, error = resolve_seed(seed_smiles, seed_name)
    if error:
        state["error"] = error
        trace(state, "retrieve", "error", error)
        return state
    if resolved is None:
        state["seed_resolved"] = None
        state["retrieve_results"] = []
        state["retrieve_done"] = True
        trace(state, "retrieve", "exit", "no seed resolved — empty retrieval")
        return state
    hits = retrieve(parse_smiles(resolved), state.get("limit", 10))
    results = [
        {
            "canonical_smiles": m.canonical_smiles,
            "chembl_id": m.chembl_id,
            "name": m.name,
            "similarity": round(sim, 4),
            "citation": {
                "database": "ChEMBL",
                "entry_id": m.chembl_id,
                "url": f"https://www.ebi.ac.uk/chembl/explore/compound/{m.chembl_id}",
            },
            "properties": compute_properties(parse_smiles(m.canonical_smiles)).model_dump(),
        }
        for m, sim in hits
    ]
    state["seed_resolved"] = resolved
    state["retrieve_results"] = results
    state["retrieve_done"] = True
    trace(state, "retrieve", "exit", f"{len(results)} hits")
    return state


def generate_node(state: dict) -> dict:
    if "generate" not in state["stages"] or state.get("generate_done"):
        trace(state, "generate", "skip", "not in route or already done")
        return state
    from app.generation.conditioned import RETRIEVAL_CONDITION_MIN_TANIMOTO

    state["current_stage"] = "generate"
    trace(state, "generate", "enter", None)
    project = _load_project(state["project_id"])
    if project is None or not project.seed_smiles:
        state["error"] = "Project has no seed molecule — add seed_smiles first"
        trace(state, "generate", "error", state["error"])
        return state
    # Re-entry: a prior run's conditioning is reused as-is. This is what makes
    # "regenerate" skip retrieval — the seed and the threshold decision are
    # already in state. A fresh run computes it from top-1 similarity.
    conditioning = dict(state.get("conditioning") or {})
    if conditioning.get("mode"):
        conditioning["noise_steps"] = state.get("gen_noise_steps", 100)
        seed_smiles = conditioning.get("seed_smiles")
        trace(state, "generate", "reuse", "reusing prior conditioning")
    else:
        hits = retrieve(parse_seed(project.seed_smiles), 1)
        top_sim = round(hits[0][1], 4) if hits else 0.0
        if top_sim >= RETRIEVAL_CONDITION_MIN_TANIMOTO:
            seed_smiles = hits[0][0].canonical_smiles
            conditioning = {
                "mode": "retrieval-conditioned",
                "seed_smiles": seed_smiles,
                "similarity": top_sim,
                "noise_steps": state.get("gen_noise_steps", 100),
            }
        else:
            seed_smiles = None
            conditioning = {
                "mode": "fallback-unconditioned",
                "reason": (
                    f"top retrieval similarity {top_sim} < "
                    f"{RETRIEVAL_CONDITION_MIN_TANIMOTO}"
                ),
                "noise_steps": state.get("gen_noise_steps", 100),
            }
    state["conditioning"] = conditioning
    from app.workers import tasks

    job_id = _submit_job(
        state,
        tasks.generate_molecules,
        "generate_job_id",
        state.get("gen_n", 20),
        None,
        None,
        state.get("gen_seed"),
        seed_smiles,
        state.get("gen_noise_steps", 100),
        conditioning,
    )
    state["generate_status"] = "queued"
    trace(state, "generate", "job_submitted", f"job={job_id} mode={conditioning['mode']}")
    return state


def parse_seed(smiles: str):
    from app.chem.embeddings import parse_smiles

    return parse_smiles(smiles)


def safety_screen(state: dict) -> dict:
    """V10 Safety Agent slot: a pass-through in V7, so V10 is a node
    insertion rather than a re-plumb. Every candidate passes until then."""
    trace(state, "safety_screen", "exit", "pass-through (V10 Safety Agent slot)")
    return state


def property_filter_node(state: dict) -> dict:
    """Property Agent gate in front of docking (the first expensive step).

    Explicit candidate_smiles from a redock request bypass the numeric
    thresholds — the caller chose those molecules. Zero survivors is an
    explicit terminal success, not a dock-stage error."""
    if "property_filter" not in state["stages"] or state.get("property_done"):
        trace(state, "property_filter", "skip", "not in route or already done")
        return state
    from app.agents.properties import compute_properties
    from app.chem.embeddings import parse_smiles

    state["current_stage"] = "property_filter"
    trace(state, "property_filter", "enter", None)
    explicit = state.get("candidate_smiles")
    candidates = list(explicit) if explicit else [
        c["smiles"] for c in state.get("generate_results", [])
    ]
    passed, rejected = [], []
    for smi in candidates:
        mol = parse_smiles(smi)
        if mol is None:
            rejected.append({"smiles": smi, "gate_reason": "invalid_smiles"})
            continue
        if explicit:
            passed.append(smi)
            continue
        props = compute_properties(mol)
        if PROPERTY_GATE_PAINS_FREE and not props.pains.passes:
            rejected.append({"smiles": smi, "gate_reason": "PAINS"})
        elif props.lipinski.violations > PROPERTY_GATE_LIPINSKI_VIOLATIONS_MAX:
            rejected.append({"smiles": smi, "gate_reason": "Lipinski"})
        elif props.qed < PROPERTY_GATE_QED_MIN:
            rejected.append({"smiles": smi, "gate_reason": "QED"})
        elif props.sa_score > PROPERTY_GATE_SA_MAX:
            rejected.append({"smiles": smi, "gate_reason": "SA"})
        else:
            passed.append(smi)
    state["property_passed"] = passed
    state["property_rejected"] = rejected
    state["property_done"] = True
    trace(
        state,
        "property_filter",
        "exit",
        f"passed={len(passed)} rejected={len(rejected)} bypass={bool(explicit)}",
    )
    if not passed:
        state["terminal_reason"] = "no_candidates_passed_property_filter"
        state["status"] = "success"
        trace(state, "property_filter", "terminal", state["terminal_reason"])
    return state


def dock_node(state: dict) -> dict:
    if "dock" not in state["stages"] or state.get("dock_done"):
        trace(state, "dock", "skip", "not in route or already done")
        return state
    from app.docking import ReceptorFetchError, UnknownPDBError, inspect_receptor

    state["current_stage"] = "dock"
    trace(state, "dock", "enter", None)
    if state.get("terminal_reason") == "no_candidates_passed_property_filter":
        trace(state, "dock", "skip", "no survivors from property_filter")
        return state
    project = _load_project(state["project_id"])
    if project is None or not project.pdb_id:
        state["error"] = "Project has no target — set pdb_id first"
        trace(state, "dock", "error", state["error"])
        return state
    candidates = state.get("property_passed") or []
    if not candidates:
        state["error"] = "No candidates passed the property filter"
        trace(state, "dock", "error", state["error"])
        return state
    try:
        inspect_receptor(project.pdb_id)
    except (UnknownPDBError, ReceptorFetchError, ValueError) as e:
        state["error"] = str(e)
        trace(state, "dock", "error", state["error"])
        return state
    from app.workers import tasks

    job_id = _submit_job(
        state, tasks.dock_molecules, "dock_job_id", state["project_id"], project.pdb_id, candidates
    )
    state["dock_status"] = "queued"
    trace(state, "dock", "job_submitted", f"job={job_id} n={len(candidates)}")
    return state


def done_node(state: dict) -> dict:
    state["current_stage"] = "done"
    if state.get("error"):
        state["status"] = "failure"
        trace(state, "done", "failure", state["error"])
    elif state.get("status") == "waiting":
        # A background job is still in flight; the run is not finished.
        trace(state, "done", "waiting", "background job in flight")
        return state
    else:
        state["status"] = "success"
        trace(state, "done", "success", state.get("terminal_reason"))
    return state


def _after_property_filter(state: dict) -> str:
    """Zero survivors still routes through done: the gate's outcome is the
    terminal state, so the trace gets a proper done event rather than a
    silent drop to END. Docking is skipped — no dock-stage error for an
    outcome the gate decided."""
    return "dock" if state.get("property_passed") else "done"


def _after_generate(state: dict) -> str:
    """Pause the traversal when the generation job was submitted rather than
    completed. Downstream nodes must not run on a stage's absence: without
    this, property_filter would see zero candidates and mark the run a
    successful terminal state while the job is still in flight. The run
    resumes via resume_run, which re-enters the graph at START with
    generate_done set."""
    return "safety_screen" if state.get("generate_done") else END


def _after_dock(state: dict) -> str:
    return "done" if state.get("dock_done") else END


def build_graph():
    g = StateGraph(dict)
    g.add_node("coordinator", coordinator)
    g.add_node("retrieve", retrieve_node)
    g.add_node("generate", generate_node)
    g.add_node("safety_screen", safety_screen)
    g.add_node("property_filter", property_filter_node)
    g.add_node("dock", dock_node)
    g.add_node("done", done_node)
    g.add_edge(START, "coordinator")
    g.add_edge("coordinator", "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_conditional_edges(
        "generate", _after_generate, {"safety_screen": "safety_screen", END: END}
    )
    g.add_edge("safety_screen", "property_filter")
    g.add_conditional_edges(
        "property_filter", _after_property_filter, {"dock": "dock", END: END}
    )
    g.add_conditional_edges("dock", _after_dock, {"done": "done", END: END})
    g.add_edge("done", END)
    return g.compile()


graph = build_graph()


# ── resume ───────────────────────────────────────────────────────────


def resume_run(run_id: int, job_payload: dict | None, job_id: str | None = None) -> bool:
    """Claim a waiting run (atomic CAS), inject the job result, re-invoke.

    The CAS is the double-resume guard: the Celery .link callback and the
    GET poll can both fire for one job, and only the first to flip
    waiting -> running proceeds, so the next stage's job is submitted once.
    job_id pins the exact job this result belongs to; a resume for a
    different job than the run is currently waiting on is rejected.

    Returns True if this call owned the resume.
    """
    from sqlalchemy import text

    from app import db

    async def _claim():
        async with db.SessionLocal() as s:
            row = (
                await s.execute(
                    text("SELECT * FROM pipeline_runs WHERE id=:id"), {"id": run_id}
                )
            ).mappings().one_or_none()
            if row is None:
                return None
            state = json.loads(row["state_json"])
            # Reject a resume carrying a job the run is no longer waiting on:
            # after the generate stage resumed, the run waits on the DOCK job,
            # so a second (stale) generate callback must not match it.
            expected = (
                state.get("active_job_id")
                or (state.get("dock_job_id") if state.get("generate_done") else None)
                or state.get("generate_job_id")
            )
            if expected is not None and job_id != expected:
                return None
            # Atomic claim: only one caller flips waiting -> running, so the
            # next stage's job is submitted exactly once.
            cas = await s.execute(
                text(
                    "UPDATE pipeline_runs SET status='running' "
                    "WHERE id=:id AND status='waiting'"
                ),
                {"id": run_id},
            )
            return (state, row["current_stage"]) if cas.rowcount else None

    claimed = _run_async(_claim())
    if claimed is None:
        return False
    state, stage = claimed
    if not job_payload or job_payload.get("failed"):
        state["error"] = (job_payload or {}).get("error") or "background job failed"
        state["status"] = "failure"
        trace(state, stage, "job_failed", state["error"])
        save_run(run_id, state, only_if_active=False)
        return True
    _inject_result(state, stage, job_payload.get("result"))
    state["status"] = "running"
    save_run(run_id, state)
    # LangGraph copies the input dict; adopt the returned state.
    state = graph.invoke(state)
    state["orchestrate"] = True
    state["run_id"] = run_id
    save_run(run_id, state, only_if_active=False)
    return True


def _inject_result(state: dict, stage: str, result: dict | None) -> None:
    result = result or {}
    if stage == "generate":
        state["generate_results"] = result.get("candidates", [])
        state["generate_metrics"] = result.get("metrics", {})
        state["conditioning"] = result.get("conditioning") or state.get("conditioning", {})
        state["generate_done"] = True
        state["generate_status"] = "success"
        trace(state, "generate", "job_resumed", f"{len(state['generate_results'])} candidates")
    elif stage == "dock":
        state["dock_results"] = result.get("ranked", [])
        state["dock_formula"] = result.get("formula", "")
        state["dock_formula_version"] = result.get("formula_version", "")
        state["receptor_info"] = result.get("receptor", {})
        state["dock_done"] = True
        state["dock_status"] = "success"
        trace(state, "dock", "job_resumed", f"{len(state['dock_results'])} ranked")
