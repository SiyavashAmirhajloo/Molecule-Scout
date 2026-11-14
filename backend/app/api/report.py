"""V8: report, exports, shortlist, and project history."""

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

router = APIRouter()


class ReportOut(BaseModel):
    payload: dict


class ShortlistCreate(BaseModel):
    docking_result_id: int | None = None
    smiles: str | None = None
    note: str | None = None


class ShortlistItemOut(BaseModel):
    id: int
    project_id: int
    docking_result_id: int | None
    candidate_smiles: str
    note: str | None


async def _latest_report(session: AsyncSession, project_id: int):
    from app.models.report import Report

    return (
        await session.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


@router.get("/{project_id}/report", response_model=ReportOut)
async def get_report(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    row = await _latest_report(session, project_id)
    if row is None:
        raise HTTPException(404, "No report yet — run the pipeline first")
    return {"payload": json.loads(row.payload_json)}


@router.get("/{project_id}/report/export.sdf")
async def export_sdf(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> Response:
    from app.report.sdf import report_sdf

    row = await _latest_report(session, project_id)
    if row is None:
        raise HTTPException(404, "No report yet — run the pipeline first")
    data = report_sdf(json.loads(row.payload_json))
    return Response(
        content=data,
        media_type="chemical/x-mdl-sdfile",
        headers={
            "Content-Disposition": f'attachment; filename="molecule-scout-project-{project_id}.sdf"'
        },
    )


@router.get("/{project_id}/report/export.pdf")
async def export_pdf(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> Response:
    from app.report.pdf import report_pdf

    row = await _latest_report(session, project_id)
    if row is None:
        raise HTTPException(404, "No report yet — run the pipeline first")
    data = report_pdf(json.loads(row.payload_json), project_id)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="molecule-scout-project-{project_id}.pdf"'
        },
    )


@router.get("/{project_id}/history")
async def get_history(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    from app.report.memory import project_history

    history = await project_history(session, project_id)
    if history is None:
        raise HTTPException(404, "Project not found")
    return history


@router.get("/{project_id}/shortlist", response_model=list[ShortlistItemOut])
async def list_shortlist(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    from app.models.shortlist import ShortlistItem

    rows = (
        await session.execute(
            select(ShortlistItem)
            .where(ShortlistItem.project_id == project_id)
            .order_by(ShortlistItem.id)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "docking_result_id": r.docking_result_id,
            "candidate_smiles": r.candidate_smiles,
            "note": r.note,
        }
        for r in rows
    ]


@router.post("/{project_id}/shortlist", response_model=ShortlistItemOut, status_code=201)
async def add_shortlist(
    project_id: int,
    body: ShortlistCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.models.docking import DockingResult
    from app.models.project import Project
    from app.models.shortlist import ShortlistItem

    if body.docking_result_id is None and not body.smiles:
        raise HTTPException(422, "Provide docking_result_id or smiles")
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(404, "Project not found")
    smiles = body.smiles
    if body.docking_result_id is not None:
        docking = (
            await session.execute(
                select(DockingResult).where(
                    DockingResult.id == body.docking_result_id,
                    DockingResult.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if docking is None:
            raise HTTPException(404, "Docking result not found for this project")
        smiles = docking.candidate_smiles
    # Fast duplicate check; the unique constraint is the real guard.
    existing = (
        await session.execute(
            select(ShortlistItem).where(
                ShortlistItem.project_id == project_id,
                ShortlistItem.candidate_smiles == smiles,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "Candidate already on the shortlist")
    item = ShortlistItem(
        project_id=project_id,
        docking_result_id=body.docking_result_id,
        candidate_smiles=smiles,
        note=body.note,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return {
        "id": item.id,
        "project_id": item.project_id,
        "docking_result_id": item.docking_result_id,
        "candidate_smiles": item.candidate_smiles,
        "note": item.note,
    }


@router.delete("/{project_id}/shortlist/{item_id}", status_code=204)
async def remove_shortlist(
    project_id: int, item_id: int, session: AsyncSession = Depends(get_session)
) -> Response:
    from app.models.shortlist import ShortlistItem

    item = (
        await session.execute(
            select(ShortlistItem).where(
                ShortlistItem.id == item_id, ShortlistItem.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "Shortlist item not found")
    await session.delete(item)
    await session.commit()
    return Response(status_code=204)
