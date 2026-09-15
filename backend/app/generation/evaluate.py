from pydantic import BaseModel
from rdkit import Chem

from app.chem.embeddings import canonical_smiles, get_embedder, parse_smiles, tanimoto


class GenerationMetrics(BaseModel):
    n_requested: int
    n_valid: int
    validity: float
    uniqueness: float
    novelty: float
    diversity: float
    avg_similarity_to_seed: float | None = None


def evaluate(
    smiles: list[str],
    corpus: set[str],
    n_requested: int,
    seed_mol: Chem.Mol | None = None,
) -> GenerationMetrics:
    mols = [parse_smiles(s) for s in smiles]
    valid = [canonical_smiles(m) for m in mols if m is not None]
    n_valid = len(valid)
    uniq = set(valid)
    embedder = get_embedder()
    fps = [embedder.embed_smiles(s) for s in list(uniq)[:200]]
    pairs = [
        tanimoto(fps[i], fps[j]) for i in range(len(fps)) for j in range(i + 1, len(fps))
    ]
    avg_sim = None
    if seed_mol is not None and uniq:
        sims = embedder.similarities(seed_mol, [embedder.embed_smiles(s) for s in uniq])
        avg_sim = round(sum(sims) / len(sims), 4)
    return GenerationMetrics(
        n_requested=n_requested,
        n_valid=n_valid,
        validity=round(n_valid / n_requested, 4) if n_requested else 0.0,
        uniqueness=round(len(uniq) / n_valid, 4) if n_valid else 0.0,
        novelty=round(sum(1 for s in uniq if s not in corpus) / len(uniq), 4) if uniq else 0.0,
        diversity=round(1 - sum(pairs) / len(pairs), 4) if pairs else 0.0,
        avg_similarity_to_seed=avg_sim,
    )
