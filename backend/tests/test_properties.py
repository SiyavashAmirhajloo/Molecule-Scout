from rdkit import Chem

from app.agents.properties import compute_properties

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
BIG_FATTY_ACID = "C" * 100 + "(=O)O"


def test_aspirin_breakdown():
    props = compute_properties(Chem.MolFromSmiles(ASPIRIN))
    assert props.qed == 0.5501
    assert props.sa_score == 1.58
    assert props.lipinski.violations == 0
    assert props.lipinski.passes is True
    assert props.lipinski.molecular_weight == 180.16
    assert props.pains.passes is True


def test_lipinski_violator_fails():
    props = compute_properties(Chem.MolFromSmiles(BIG_FATTY_ACID))
    assert props.lipinski.violations >= 2
    assert props.lipinski.passes is False
