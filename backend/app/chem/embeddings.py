from functools import lru_cache
from typing import Protocol

from rdkit import Chem, RDLogger
from rdkit.Chem import DataStructs
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator

RDLogger.DisableLog("rdApp.error")  # invalid SMILES are routine input (422), not crashes


class MoleculeEmbedder(Protocol):
    dim: int

    def embed_mol(self, mol: Chem.Mol) -> list[float]: ...
    def embed_smiles(self, smiles: str) -> list[float] | None: ...
    def similarities(self, mol: Chem.Mol, stored: list[list[float]]) -> list[float]: ...


def parse_smiles(smiles: str) -> Chem.Mol | None:
    return Chem.MolFromSmiles(smiles)


def canonical_smiles(mol: Chem.Mol) -> str:
    return Chem.MolToSmiles(mol)


class MorganFingerprintEmbedder:
    def __init__(self, radius: int = 2, n_bits: int = 2048) -> None:
        self._gen = GetMorganGenerator(radius=radius, fpSize=n_bits)
        self._n_bits = n_bits

    @property
    def dim(self) -> int:
        return self._n_bits

    def embed_mol(self, mol: Chem.Mol) -> list[float]:
        fp = self._gen.GetFingerprint(mol)
        return [1.0 if fp.GetBit(i) else 0.0 for i in range(self._n_bits)]

    def embed_smiles(self, smiles: str) -> list[float] | None:
        mol = parse_smiles(smiles)
        return self.embed_mol(mol) if mol is not None else None

    def similarities(self, mol: Chem.Mol, stored: list[list[float]]) -> list[float]:
        query = self._gen.GetFingerprint(mol)
        return list(DataStructs.BulkTanimotoSimilarity(query, [_to_bv(v) for v in stored]))


def _to_bv(vec: list[float]) -> DataStructs.ExplicitBitVect:
    bv = DataStructs.ExplicitBitVect(len(vec))
    bv.SetBitsFromList([i for i, v in enumerate(vec) if v > 0.5])
    return bv


def tanimoto(a: list[float], b: list[float]) -> float:
    return DataStructs.TanimotoSimilarity(_to_bv(a), _to_bv(b))


@lru_cache
def get_embedder() -> MoleculeEmbedder:
    return MorganFingerprintEmbedder()
