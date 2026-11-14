"""Report Agent: assemble a grounded, per-candidate rationale report.

One LLM call per candidate (docs/architecture.md's speed profile), capped at
MAX_REPORT_CANDIDATES by rank, run on a bounded thread pool. Any provider
failure falls back to the deterministic template for that candidate only —
one bad call never fails the report.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.llm import LLM_MAX_WORKERS, LLMError, get_provider
from app.report.prompts import (
    DISCLAIMER,
    SYSTEM_PROMPT,
    VERIFICATION_PHRASE,
    candidate_facts,
    template_rationale,
)

MAX_REPORT_CANDIDATES = 20


def _rationale(provider, cand: dict, rank: int, total: int, conditioning: dict) -> dict:
    facts = candidate_facts(cand, rank, total, conditioning)
    template = template_rationale(cand, rank, total, conditioning)
    text, source = template, "template-fallback"
    if provider.name != "template-fallback":
        try:
            text = provider.complete(SYSTEM_PROMPT, facts)
            source = provider.name
        except LLMError:
            text, source = template, "template-fallback"
    # Enforce the responsible-use sentence in code — never trust the model.
    if VERIFICATION_PHRASE not in text:
        text = f"{text.rstrip()} This result requires human/wet-lab verification and is a triage aid, not a final answer."
    return {
        "smiles": cand.get("smiles"),
        "rank": rank,
        "rank_score": cand.get("rank_score"),
        "affinity": cand.get("affinity"),
        "qed": cand.get("qed"),
        "novelty": cand.get("novelty"),
        "rationale": text,
        "rationale_source": source,
        "verification_note": VERIFICATION_PHRASE,
    }


def build_report(project_id: int, run_id: int, state: dict) -> dict:
    conditioning = state.get("conditioning") or {}
    docked = list(state.get("dock_results") or [])
    docked.sort(key=lambda c: -(c.get("rank_score") or 0.0))
    provider = get_provider()

    if not docked:
        return {
            "project_id": project_id,
            "pipeline_run_id": run_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "model": provider.name,
            "terminal_reason": state.get("terminal_reason")
            or "no_candidates_passed_property_filter",
            "summary": "No candidates survived property filtering — no rationale was generated.",
            "formula": state.get("dock_formula", ""),
            "formula_version": state.get("dock_formula_version", ""),
            "conditioning_summary": conditioning,
            "disclaimer": DISCLAIMER,
            "candidates": [],
        }

    capped = docked[:MAX_REPORT_CANDIDATES]
    total = len(capped)
    with ThreadPoolExecutor(max_workers=LLM_MAX_WORKERS) as pool:
        candidates = list(
            pool.map(
                lambda pair: _rationale(provider, pair[1], pair[0], total, conditioning),
                enumerate(capped, start=1),
            )
        )
    return {
        "project_id": project_id,
        "pipeline_run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "model": provider.name,
        "formula": state.get("dock_formula", ""),
        "formula_version": state.get("dock_formula_version", ""),
        "conditioning_summary": conditioning,
        "disclaimer": DISCLAIMER,
        "candidates": candidates,
    }


def payload_to_json(payload: dict) -> str:
    return json.dumps(payload)
