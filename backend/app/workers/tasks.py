from app.workers.celery_app import celery

_task_loop = None
_task_loop_lock = __import__("threading").Lock()


def _run_async(coro):
    """Run an async DB call from a sync Celery task, on ONE process-wide loop.

    Two constraints, both learned the hard way:
    - ``asyncio.run()`` raises when a loop is already running (Celery eager
      mode, or a task invoked from inside FastAPI).
    - A *fresh* loop per call breaks SQLAlchemy: the engine's pooled
      connections belong to the first loop, and reusing them from another
      raises "attached to a different loop".

    So: one loop per process, created lazily, run on a single dedicated thread.
    """
    import asyncio
    import concurrent.futures

    global _task_loop
    with _task_loop_lock:
        if _task_loop is None:
            _task_loop = asyncio.new_event_loop()
        loop = _task_loop

    def _submit():
        return loop.run_until_complete(coro)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _submit()  # no loop in this thread: run it right here
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_submit).result()


@celery.task(name="add")
def add(a: int, b: int) -> int:
    return a + b


@celery.task(name="dock_molecules", bind=True)
def dock_molecules(
    self,
    project_id: int,
    pdb_id: str,
    smiles_list: list[str],
    seed: int | None = None,
) -> dict:
    import logging

    from sqlalchemy import select

    from app.agents.properties import compute_properties
    from app.chem.embeddings import get_embedder, parse_smiles, tanimoto
    from app.db import engine
    from app.docking import (
        FORMULA,
        FORMULA_VERSION,
        dock,
        inspect_receptor,
        prep_ligand,
        prepare_receptor,
        rank_batch,
    )
    from app.models.docking import DockingResult
    from app.models.molecule import KnownMolecule

    log = logging.getLogger(__name__)

    async def corpus_fps() -> list[list[float]]:
        async with engine.connect() as conn:
            rows = (await conn.execute(select(KnownMolecule.fingerprint))).scalars()
            return list(rows.all())

    fps = _run_async(corpus_fps())
    embedder = get_embedder()

    _, center = inspect_receptor(pdb_id)
    receptor_pdbqt = prepare_receptor(pdb_id, center)
    scored = []
    for smi in smiles_list:
        mol = parse_smiles(smi)
        if mol is None:
            continue
        props = compute_properties(mol)
        pdbqt = prep_ligand(smi)
        if pdbqt is None:
            log.warning("ligand prep failed, excluded: %s", smi)
            scored.append(
                {"smiles": smi, "affinity": None, "pose": None,
                 "qed": props.qed, "novelty": None,
                 "properties": props.model_dump()}
            )
            continue
        affinity, pose = dock(pdbqt, receptor_pdbqt, center)
        if affinity is None:
            log.warning("vina dock failed, excluded: %s", smi)
        fp = embedder.embed_mol(mol)
        sims = [tanimoto(fp, c) for c in fps] if fps else [0.0]
        scored.append(
            {"smiles": smi, "affinity": affinity, "pose": pose,
             "qed": props.qed, "novelty": round(1 - max(sims), 4),
             "properties": props.model_dump()}
        )
    ranked = rank_batch(scored)

    async def persist() -> list[int]:
        from app.db import SessionLocal

        ids = []
        async with SessionLocal() as session:
            for s in ranked:
                row = DockingResult(
                    project_id=project_id,
                    candidate_smiles=s["smiles"],
                    affinity=s["affinity"],
                    qed=s["qed"],
                    novelty=s["novelty"],
                    rank_score=s["rank_score"],
                    formula_version=FORMULA_VERSION,
                    pose_pdbqt=s["pose"],
                    receptor_pdb_id=pdb_id.upper(),
                    box_center_x=center[0],
                    box_center_y=center[1],
                    box_center_z=center[2],
                )
                session.add(row)
                await session.flush()
                ids.append(row.id)
            await session.commit()
        return ids

    row_ids = _run_async(persist())
    for s, rid in zip(ranked, row_ids):
        s["id"] = rid
        del s["pose"]
    return {
        "ranked": ranked,
        "formula": FORMULA,
        "formula_version": FORMULA_VERSION,
        "receptor": {"pdb_id": pdb_id.upper(), "center": list(center)},
    }


@celery.task(name="generate_molecules", bind=True)
def generate_molecules(
    self,
    n: int = 10,
    mw_range: tuple[float, float] | None = None,
    logp_range: tuple[float, float] | None = None,
    seed: int | None = None,
    seed_smiles: str | None = None,
    noise_steps: int = 100,
    conditioning: dict | None = None,
) -> dict:
    from sqlalchemy import select

    from app.agents.properties import compute_properties
    from app.chem.embeddings import parse_smiles
    from app.generation.evaluate import evaluate
    from app.generation.graphdit import GraphDiTBackend, checkpoint_id
    from app.models.molecule import KnownMolecule

    async def corpus() -> set[str]:
        from app.db import engine

        async with engine.connect() as conn:
            rows = (await conn.execute(select(KnownMolecule.canonical_smiles))).scalars()
            return set(rows.all())

    backend = GraphDiTBackend()
    smiles = backend.generate(n, mw_range, logp_range, seed, seed_smiles, noise_steps)
    seed_mol = parse_smiles(seed_smiles) if seed_smiles else None
    metrics = evaluate(smiles, _run_async(corpus()), n, seed_mol)
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
        "conditioning": conditioning or {"mode": "unconditioned"},
    }
