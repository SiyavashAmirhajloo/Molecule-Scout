from fastapi import HTTPException
from rdkit import Chem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chem.embeddings import canonical_smiles, get_embedder, parse_smiles
from app.models.molecule import KnownMolecule


async def retrieve(
    session: AsyncSession, seed_mol: Chem.Mol, limit: int
) -> list[tuple[KnownMolecule, float]]:
    rows = (await session.execute(select(KnownMolecule))).scalars().all()
    scores = get_embedder().similarities(seed_mol, [m.fingerprint for m in rows])
    # ponytail: brute-force scan over ~3.4k rows, pgvector ordering if corpus grows
    return sorted(zip(rows, scores), key=lambda pair: pair[1], reverse=True)[:limit]


async def resolve_seed(
    session: AsyncSession, smiles: str | None, name: str | None
) -> tuple[Chem.Mol, str, str] | None:
    if smiles:
        mol = parse_smiles(smiles)
        if mol is None:
            raise HTTPException(422, "Invalid SMILES")
        return mol, canonical_smiles(mol), "smiles"
    if name:
        row = (
            await session.execute(
                select(KnownMolecule).where(KnownMolecule.name.ilike(name)).limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(422, f"Unknown compound name: {name!r}")
        mol = parse_smiles(row.canonical_smiles)
        assert mol is not None  # stored SMILES were RDKit-validated at ingest
        return mol, row.canonical_smiles, "name"
    return None


def citation(m: KnownMolecule) -> dict:
    return {
        "database": "ChEMBL",
        "entry_id": m.chembl_id,
        "url": f"https://www.ebi.ac.uk/chembl/explore/compound/{m.chembl_id}",
    }
