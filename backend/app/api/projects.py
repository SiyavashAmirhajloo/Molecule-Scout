from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.properties import PropertyBreakdown, compute_properties
from app.agents.retrieval import citation, resolve_seed, retrieve
from app.chem.embeddings import parse_smiles
from app.db import get_session
from app.models.project import Project

router = APIRouter()


class ProjectCreate(BaseModel):
    pdb_id: str | None = None
    seed_smiles: str | None = None
    seed_name: str | None = None
    limit: int = 10


class RetrievalHit(BaseModel):
    canonical_smiles: str
    chembl_id: str | None
    name: str | None
    similarity: float
    citation: dict
    properties: PropertyBreakdown


class ProjectOut(BaseModel):
    id: int
    pdb_id: str | None
    seed_smiles: str | None
    seed_source: str | None
    created_at: datetime


class ProjectResponse(BaseModel):
    project: ProjectOut
    seed_resolved: str | None
    results: list[RetrievalHit]
    message: str | None = None


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: ProjectCreate, session: AsyncSession = Depends(get_session)
) -> ProjectResponse:
    if not body.pdb_id and not body.seed_smiles and not body.seed_name:
        raise HTTPException(422, "Provide pdb_id and/or a seed molecule (seed_smiles or seed_name)")
    if body.seed_smiles and body.seed_name:
        raise HTTPException(422, "Provide seed_smiles or seed_name, not both")
    resolved = await resolve_seed(session, body.seed_smiles, body.seed_name)
    project = Project(
        pdb_id=body.pdb_id,
        seed_smiles=resolved[1] if resolved else None,
        seed_source=resolved[2] if resolved else None,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    if resolved is None:
        return ProjectResponse(
            project=ProjectOut.model_validate(project, from_attributes=True),
            seed_resolved=None,
            results=[],
            message=f"No compounds associated with target {body.pdb_id} yet — "
            "add a seed molecule to retrieve similar known compounds.",
        )
    hits = await retrieve(session, resolved[0], body.limit)
    results = []
    for m, s in hits:
        mol = parse_smiles(m.canonical_smiles)
        assert mol is not None  # stored SMILES were RDKit-validated at ingest
        results.append(
            RetrievalHit(
                canonical_smiles=m.canonical_smiles,
                chembl_id=m.chembl_id,
                name=m.name,
                similarity=round(s, 4),
                citation=citation(m),
                properties=compute_properties(mol),
            )
        )
    return ProjectResponse(
        project=ProjectOut.model_validate(project, from_attributes=True),
        seed_resolved=resolved[1],
        results=results,
    )
