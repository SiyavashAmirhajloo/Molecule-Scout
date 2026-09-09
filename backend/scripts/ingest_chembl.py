"""Ingest ChEMBL approved drugs (max_phase=4) into known_molecules.

Slice: https://www.ebi.ac.uk/chembl/api/data/molecule.json?max_phase=4 (~4.2k
records, Sep 2026). RDKit-parsed, deduped on canonical SMILES.
Usage: docker compose exec api python scripts/ingest_chembl.py
"""

import asyncio
import sys
import urllib.request
from datetime import UTC, datetime

sys.path.insert(0, ".")

from sqlalchemy import select

from app.chem.embeddings import canonical_smiles, get_embedder, parse_smiles
from app.db import SessionLocal, upgrade_schema
from app.models.molecule import KnownMolecule

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
PAGE_SIZE = 500


def fetch_page(offset: int) -> dict:
    url = f"{BASE_URL}?max_phase=4&limit={PAGE_SIZE}&offset={offset}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        import json

        return json.load(resp)


async def main() -> None:
    await upgrade_schema()
    embedder = get_embedder()
    ingested = skipped_null = failed_parse = dupes = 0
    total = None
    offset = 0
    async with SessionLocal() as session:
        seen = set(
            (await session.execute(select(KnownMolecule.canonical_smiles))).scalars().all()
        )
        while True:
            page = await asyncio.to_thread(fetch_page, offset)
            total = total or page["page_meta"]["total_count"]
            molecules = page["molecules"]
            if not molecules:
                break
            for m in molecules:
                smiles = (m.get("molecule_structures") or {}).get("canonical_smiles")
                if not smiles:
                    skipped_null += 1
                    continue
                mol = parse_smiles(smiles)
                if mol is None:
                    failed_parse += 1
                    continue
                canon = canonical_smiles(mol)
                if canon in seen:
                    dupes += 1
                    continue
                seen.add(canon)
                session.add(
                    KnownMolecule(
                        canonical_smiles=canon,
                        chembl_id=m["molecule_chembl_id"],
                        name=m.get("pref_name"),
                        fingerprint=embedder.embed_mol(mol),
                    )
                )
                ingested += 1
            await session.commit()
            offset += len(molecules)
            print(f"progress: {offset}/{total} (ingested={ingested})", flush=True)
    print(
        f"done {datetime.now(UTC):%Y-%m-%d}: total={total} ingested={ingested} "
        f"skipped_null={skipped_null} failed_parse={failed_parse} dupes={dupes}"
    )


asyncio.run(main())
