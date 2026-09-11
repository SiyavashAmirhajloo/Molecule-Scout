from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.retrieval import retrieve
from app.chem.embeddings import parse_smiles
from app.db import get_session

router = APIRouter()


class SimilarHit(BaseModel):
    canonical_smiles: str
    chembl_id: str | None
    name: str | None
    similarity: float


@router.get("/similar", response_model=list[SimilarHit])
async def similar(
    smiles: Annotated[str, Query(description="SMILES to search for")],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    session: AsyncSession = Depends(get_session),
) -> list[SimilarHit]:
    mol = parse_smiles(smiles)
    if mol is None:
        raise HTTPException(422, "Invalid SMILES")
    ranked = await retrieve(session, mol, limit)
    return [
        SimilarHit(
            canonical_smiles=m.canonical_smiles,
            chembl_id=m.chembl_id,
            name=m.name,
            similarity=round(s, 4),
        )
        for m, s in ranked
    ]
