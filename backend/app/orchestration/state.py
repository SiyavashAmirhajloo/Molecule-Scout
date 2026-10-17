"""Pipeline state schema and Coordinator route map.

The graph state is a plain dict (LangGraph's native state type). This
module defines the route table and the trace helper. State keys are
documented here so every node agrees on the schema.

State keys:
  request_type      str — new_project | regenerate | redock | full_rerun
  project_id        int
  pdb_id            str | None
  seed_smiles       str | None
  seed_name         str | None
  seed_resolved     str | None — canonical SMILES after resolution
  limit             int — retrieval hit count
  gen_n, gen_noise_steps, gen_seed — generation parameters
  candidate_smiles  list[str] | None — explicit candidates (redock bypasses gate)
  orchestrate       bool — True for /run (link jobs), False for per-stage endpoints
  run_id            int | None — PipelineRun id (set by API layer)
  route, stages     set by coordinator
  current_stage     str
  terminal_reason   str | None — why the run ended early (e.g. no survivors)
  retrieve_results  list[dict], retrieve_done: bool
  generate_job_id, generate_status, generate_results, generate_metrics,
    conditioning, generate_done: bool
  property_passed    list[str], property_rejected: list[dict], property_done: bool
  dock_job_id, dock_status, dock_results, dock_formula,
    dock_formula_version, receptor_info, dock_done: bool
  trace             list[dict]
  error             str | None
  stop_after        str | None — per-stage endpoint early-exit signal
"""

REQUIRED_STAGES: dict[str, list[str]] = {
    "new_project": ["retrieve", "generate", "property_filter", "dock"],
    "full_rerun": ["retrieve", "generate", "property_filter", "dock"],
    "regenerate": ["generate", "property_filter", "dock"],
    "redock": ["property_filter", "dock"],
}

TERMINAL_STATUSES = ("success", "failure")
ACTIVE_STATUSES = ("pending", "running", "waiting")


def trace(state: dict, node: str, event: str, detail: str | None) -> None:
    """Append a trace event to the run state. Persisted and returned by the API."""
    from datetime import UTC, datetime

    state.setdefault("trace", []).append(
        {
            "node": node,
            "event": event,
            "at": datetime.now(UTC).isoformat(),
            "detail": detail,
        }
    )
