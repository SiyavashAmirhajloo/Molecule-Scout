from functools import lru_cache

from pydantic import BaseModel
from rdkit import Chem
from rdkit.Chem import QED, Descriptors, Lipinski
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
from rdkit.Contrib.SA_Score import sascorer


class LipinskiBreakdown(BaseModel):
    molecular_weight: float
    logp: float
    h_bond_donors: int
    h_bond_acceptors: int
    violations: int
    passes: bool


class PainsBreakdown(BaseModel):
    matches: int
    passes: bool


class PropertyBreakdown(BaseModel):
    qed: float
    sa_score: float
    lipinski: LipinskiBreakdown
    pains: PainsBreakdown


@lru_cache
def _pains_catalog() -> FilterCatalog:
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    return FilterCatalog(params)


def compute_properties(mol: Chem.Mol) -> PropertyBreakdown:
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    pains_matches = len(_pains_catalog().GetMatches(mol))
    return PropertyBreakdown(
        qed=round(QED.qed(mol), 4),
        sa_score=round(sascorer.calculateScore(mol), 2),
        lipinski=LipinskiBreakdown(
            molecular_weight=round(mw, 2),
            logp=round(logp, 2),
            h_bond_donors=hbd,
            h_bond_acceptors=hba,
            violations=violations,
            passes=violations <= 1,
        ),
        pains=PainsBreakdown(matches=pains_matches, passes=pains_matches == 0),
    )
