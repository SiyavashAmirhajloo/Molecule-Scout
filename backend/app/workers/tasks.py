from app.workers.celery_app import celery


@celery.task(name="add")
def add(a: int, b: int) -> int:
    return a + b


@celery.task(name="generate_molecules", bind=True)
def generate_molecules(
    self,
    n: int = 10,
    mw_range: tuple[float, float] | None = None,
    logp_range: tuple[float, float] | None = None,
    seed: int | None = None,
) -> dict:
    import asyncio

    from sqlalchemy import select

    from app.agents.properties import compute_properties
    from app.chem.embeddings import parse_smiles
    from app.db import SessionLocal
    from app.generation.evaluate import evaluate
    from app.generation.graphdit import GraphDiTBackend, checkpoint_id
    from app.models.molecule import KnownMolecule

    async def corpus() -> set[str]:
        async with SessionLocal() as session:
            rows = (await session.execute(select(KnownMolecule.canonical_smiles))).scalars()
            return set(rows.all())

    backend = GraphDiTBackend()
    smiles = backend.generate(n, mw_range, logp_range, seed)
    metrics = evaluate(smiles, asyncio.run(corpus()), n)
    candidates = []
    for s in smiles:
        mol = parse_smiles(s)
        if mol is None:
            continue
        candidates.append({"smiles": s, "properties": compute_properties(mol).model_dump()})
    return {
        "candidates": candidates,
        "metrics": metrics.model_dump(),
        "checkpoint": f"graphdit-qm9/{checkpoint_id()}",
        "seed": seed,
    }
