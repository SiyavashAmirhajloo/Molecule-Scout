"""SDF export — RDKit writes SDF natively; no new dependency."""

from app.chem.embeddings import parse_smiles


def report_sdf(payload: dict) -> bytes:
    """Ranked candidates with their scores and rationale as SDF properties."""
    import io

    from rdkit.Chem import SDWriter

    buf = io.StringIO()
    writer = SDWriter(buf)
    for c in payload.get("candidates", []):
        mol = parse_smiles(c.get("smiles") or "")
        if mol is None:
            continue
        mol.SetProp("_Name", f"rank_{c.get('rank')}")
        if c.get("smiles"):
            mol.SetProp("smiles", c["smiles"])
        for key in ("rank_score", "affinity", "qed", "novelty", "rationale_source"):
            value = c.get(key)
            if value is not None:
                mol.SetProp(key, str(value))
        if c.get("rationale"):
            mol.SetProp("rationale", c["rationale"])
        mol.SetProp("formula_version", payload.get("formula_version", ""))
        mol.SetProp("disclaimer", payload.get("disclaimer", ""))
        writer.write(mol)
    writer.close()
    return buf.getvalue().encode("utf-8")
