We are starting **Version 9 — Vision Agent: Literature Structure
Extraction**, as scoped in `docs/roadmap.md`. Versions 0–8 (the full
core product: knowledge base, retrieval, filtering, retrieval-
augmented generation, docking, orchestration, reporting, memory) are
done and working end-to-end on structured data — review existing code
before proceeding. Re-read the "Vision Pipeline: Structure Extraction
from Literature" section in `docs/architecture.md` closely.

This is the differentiating feature, deliberately sequenced last among
the core versions because it's the highest-risk, most research-
adjacent piece. The product already works without it — treat this as
additive, and don't let it destabilize what's already working.

## Goal

Let the system read molecular structures out of images embedded in
uploaded scientific papers/patents, feeding them into the same
knowledge base that Version 1 built from PubChem/ChEMBL.

## Scope for this version only

- PDF ingestion + page rasterization, run as a Celery background job
- Diagram localization: a document-layout/object-detection model that
  proposes bounding boxes for structure diagrams distinct from
  figures, tables, and body text — this is the same category of
  problem as prior object-detection work, applied to a new domain
- Structure recognition: DECIMER or MolScribe on each cropped diagram,
  producing a candidate SMILES string with a confidence score
- Validation: round-trip every candidate SMILES through RDKit; parse
  failures or chemically implausible output get flagged low-confidence
  rather than trusted
- OCR-based context linking (Tesseract/EasyOCR) to associate nearby
  compound identifiers/activity data with each extracted structure
- Deduplication against the existing knowledge base by canonical
  SMILES/InChIKey before insertion
- Build the "golden set" of structure-diagram images with known-
  correct SMILES described in `docs/tech-stack.md`, and report
  extraction accuracy against it — this is the version's real success
  metric, not just "it runs"
- Frontend: literature browser (ingested sources, extraction status)
  and a review UI specifically for low-confidence extractions, since
  those will need human confirmation before entering the knowledge
  base

## Ground rules

- Do not let a low accuracy on the golden set block shipping this
  version — report the honest number, make low-confidence extractions
  clearly flagged and excluded from automatic use in retrieval/
  generation conditioning until confirmed, and note it as a known
  limitation. An honest 70% with a working review workflow is a far
  better outcome here than an inflated claim.
- No production hardening/safety agent yet — Version 10.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, show me a real extraction run on an actual paper or
  patent PDF, the golden-set accuracy numbers, and the low-confidence
  review UI in action.
- Summarize what was built, the honest accuracy numbers, and what
  you'd improve first if given more time on this specific piece.
