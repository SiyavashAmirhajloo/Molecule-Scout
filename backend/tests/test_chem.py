from app.chem.embeddings import (
    canonical_smiles,
    get_embedder,
    parse_smiles,
    tanimoto,
)

CAFFEINE = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
IBUPROFEN = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"


def test_round_trip_canonical():
    assert canonical_smiles(parse_smiles(ASPIRIN)) == ASPIRIN


def test_fingerprint_stable_and_sized():
    embedder = get_embedder()
    assert embedder.dim == 2048
    fp1 = embedder.embed_smiles(CAFFEINE)
    fp2 = embedder.embed_smiles(CAFFEINE)
    assert fp1 == fp2
    assert sum(fp1) > 0


def test_self_similarity_is_one():
    embedder = get_embedder()
    mol = parse_smiles(IBUPROFEN)
    assert embedder.similarities(mol, [embedder.embed_mol(mol)])[0] == 1.0
    assert tanimoto(embedder.embed_smiles(CAFFEINE), embedder.embed_smiles(CAFFEINE)) == 1.0


def test_invalid_smiles_returns_none():
    assert parse_smiles("not-a-molecule") is None
    assert get_embedder().embed_smiles("not-a-molecule") is None


def test_similar_drugs_differ():
    fp = get_embedder().embed_smiles
    assert 0.0 < tanimoto(fp(ASPIRIN), fp(IBUPROFEN)) < 1.0
