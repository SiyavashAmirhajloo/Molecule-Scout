"""Memory Agent read model.

No new store: project history is read from rows V7/V8 already persist
(pipeline_runs, reports, shortlist_items, docking_results). A dedicated memory
table would duplicate what already exists.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineRun
from app.models.project import Project
from app.models.report import Report
from app.models.shortlist import ShortlistItem


async def project_history(session: AsyncSession, project_id: int) -> dict | None:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        return None
    runs = (
        await session.execute(
            select(PipelineRun)
            .where(PipelineRun.project_id == project_id)
            .order_by(PipelineRun.id.desc())
        )
    ).scalars().all()
    run_summaries = []
    for r in runs:
        counts = _state_counts(r.state_json)
        run_summaries.append(
            {
                "id": r.id,
                "route": r.route,
                "status": r.status,
                "current_stage": r.current_stage,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "candidate_count": counts["candidates"],
                "ranked_count": counts["ranked"],
            }
        )
    latest = (
        await session.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    shortlist_count = (
        await session.execute(
            select(func.count(ShortlistItem.id)).where(
                ShortlistItem.project_id == project_id
            )
        )
    ).scalar_one()
    return {
        "project": {
            "id": project.id,
            "pdb_id": project.pdb_id,
            "seed_smiles": project.seed_smiles,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        },
        "runs": run_summaries,
        "latest_report_run_id": latest.pipeline_run_id if latest else None,
        "shortlist_count": shortlist_count,
        "has_history": bool(run_summaries),
    }


def _state_counts(state_json: str) -> dict[str, int]:
    import json

    try:
        s = json.loads(state_json or "{}")
    except (TypeError, ValueError):
        return {"candidates": 0, "ranked": 0}
    return {
        "candidates": len(s.get("generate_results") or []),
        "ranked": len(s.get("dock_results") or []),
    }
