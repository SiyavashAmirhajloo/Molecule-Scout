import hashlib
import os

CHECKPOINT_ENV = "GENERATOR_CHECKPOINT"
DEFAULT_CHECKPOINT = "models/graphdit-qm9.pt"


def checkpoint_path() -> str:
    return os.environ.get(CHECKPOINT_ENV, DEFAULT_CHECKPOINT)


def checkpoint_id(path: str = "") -> str:
    path = path or checkpoint_path()
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        return "missing"


class GraphDiTBackend:
    name = "graphdit-qm9"

    def __init__(self) -> None:
        from torch_molecule.generator.graph_dit.modeling_graph_dit import (
            GraphDITMolecularGenerator,
        )

        self._model = GraphDITMolecularGenerator(device="cpu")
        self._model.load_from_local(checkpoint_path())

    def generate(
        self,
        n: int,
        mw_range: tuple[float, float] | None = None,
        logp_range: tuple[float, float] | None = None,
        seed: int | None = None,
        seed_smiles: str | None = None,
        noise_steps: int = 100,
    ) -> list[str]:
        import random

        import numpy as np
        import torch

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
        if seed_smiles:
            from app.generation.conditioned import generate_seeded

            raw = generate_seeded(self._model, seed_smiles, n, noise_steps, seed)
        else:
            raw = self._model.generate(batch_size=n)
        smiles = [s for s in raw if s]
        if mw_range or logp_range:
            from rdkit import Chem
            from rdkit.Chem import Descriptors

            kept = []
            for s in smiles:
                mol = Chem.MolFromSmiles(s)
                if mol is None:
                    continue
                mw, logp = Descriptors.MolWt(mol), Descriptors.MolLogP(mol)
                if mw_range and not mw_range[0] <= mw <= mw_range[1]:
                    continue
                if logp_range and not logp_range[0] <= logp <= logp_range[1]:
                    continue
                kept.append(s)
            return kept
        return smiles
