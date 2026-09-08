# Technology Stack

These choices are mandatory unless there is a compelling technical
reason to deviate. This project shares its backend/orchestration
philosophy with LexBook-AI but adds a cheminformatics stack and a
vision stack, plus a background job queue that LexBook-AI didn't need.

## Backend

- Python 3.13+
- FastAPI
- AsyncIO
- SQLAlchemy
- Alembic
- Pydantic v2
- Uvicorn
- **Celery + Redis** — mandatory here (unlike LexBook-AI, where it was
  optional). Structure extraction, diffusion sampling, and docking are
  all slow (seconds to minutes each); these must run as background
  jobs with status polling, not inline in a request/response cycle.

## AI Orchestration Framework

- LangGraph (primary orchestration across all agents)
- LangChain (only where it adds clear value, e.g. document loaders)
- Langfuse for tracing agent decisions and job pipelines

## Database

- PostgreSQL
- pgvector (for molecule and text embeddings)
- Redis (Celery broker/result backend, plus job-status caching)
- Object storage (local disk volume for MVP; S3-compatible — e.g.
  MinIO — once deployed) for uploaded PDFs/patents, generated
  structure files, and docking outputs

## LLM Providers (Report Agent, extraction assistance)

Same provider-agnostic abstraction layer approach as LexBook-AI:

- Gemini (free tier), Groq, OpenRouter (free models) initially
- Ollama, OpenAI, Anthropic as later options

## Cheminformatics Stack

This is the layer LexBook-AI didn't need — treat it as a first-class
part of the architecture, not a library you casually `pip install`.

- **RDKit** — the core cheminformatics library: molecule parsing
  (SMILES/SDF/Mol), fingerprint generation, QED, synthetic
  accessibility (SA) score, Lipinski's Rule of Five, PAINS filtering,
  2D structure rendering
- **Open Babel** — file format conversion between cheminformatics
  formats (SDF, PDB, PDBQT, MOL2) as needed for docking tools
- **Molecule embedding abstraction layer** (mirrors LexBook-AI's
  embedding abstraction, but for molecules instead of text):
  - Morgan/ECFP fingerprints (via RDKit) as the default, cheap,
    dependency-light option
  - A learned graph embedding (e.g. a pretrained ChemBERTa or MolCLR
    checkpoint) as a swappable, higher-quality alternative
- **Reference molecule databases**: PubChem and ChEMBL (both provide
  bulk downloadable subsets suitable for a local knowledge base
  without needing to scrape either service)

## Generative Model Layer (Diffusion)

Build an abstraction layer here too — don't hardcode one diffusion
architecture, since this is the piece most likely to need swapping
as better open implementations appear.

- **Primary backbone**: an equivariant diffusion model for molecules
  operating over 3D atomic coordinates and atom types (EDM-style —
  e.g. the open-source "e3_diffusion_for_molecules" implementation),
  OR a 2D molecular graph diffusion model (DiGress-style) if 3D
  conditioning proves too heavy for the target compute budget — pick
  one as the v1 default and document the tradeoff, don't half-build
  both
- **Retrieval-augmented conditioning**: implement the RetMol-style
  mechanism described in `docs/architecture.md` — retrieved molecule
  embeddings are projected into the model's conditioning space and
  injected during the denoising process (via cross-attention if the
  backbone architecture supports it, or via classifier-free-guidance-
  style conditioning vectors if a lighter-touch integration is needed)
- **Training data**: QM9 or a filtered, size-capped subset of ZINC —
  both public, both small enough to train/fine-tune on a single
  consumer or cloud GPU rather than requiring an industrial compute
  budget
- Future/optional backbone: a pocket-conditioned 3D generator
  (DiffSBDD/TargetDiff-style) for target-structure-aware generation —
  see `docs/roadmap.md`'s Future Versions

## Vision Stack (Structure Extraction from Literature)

- **Document layout / diagram localization**: a document layout model
  (e.g. a fine-tuned YOLO or an existing layout-detection model such
  as those trained on DocLayNet/PubLayNet) to find bounding boxes
  around chemical structure diagrams on a scanned/PDF page — treat
  this the same way you'd treat any object-detection task from your
  existing CV background
- **Structure recognition (image → SMILES)**: DECIMER or MolScribe —
  both are open-source, purpose-built models for converting a cropped
  structure-diagram image into a SMILES string, with a confidence
  score
- **OCR (supporting role)**: Tesseract or EasyOCR, for reading
  captions/labels near a structure diagram (e.g. compound numbering
  like "Compound 3a") to help match extracted structures back to the
  surrounding text
- **Validation**: every extracted SMILES is round-tripped through
  RDKit — if RDKit can't parse it, or the parsed molecule is
  chemically implausible, the extraction is flagged low-confidence
  rather than silently trusted

## Docking

- **AutoDock Vina** — open-source, the default docking engine
- **Open Babel / MGLTools** — for receptor/ligand file preparation
  (PDB → PDBQT conversion, adding hydrogens, assigning charges)
- Future/optional alternate backend: **DiffDock** — a diffusion-based
  docking pose predictor, notable because it makes this product's
  second legitimate use of diffusion models (pose generation, not
  just molecule generation) — see `docs/roadmap.md`'s Future Versions

## Frontend

- Next.js (React + TypeScript)
- TailwindCSS
- shadcn/ui
- Framer Motion
- **3Dmol.js or NGL Viewer** — for interactive 3D visualization of
  candidate molecules and protein-ligand docking poses (this is the
  domain-specific addition beyond LexBook-AI's frontend stack)
- **RDKit.js** — for fast client-side 2D structure rendering in list/
  comparison views, without a round trip to the backend for every
  thumbnail

## Authentication

- JWT
- OAuth (Google)
- Guest mode (useful for demoing without setup friction)

## Deployment

- Docker
- Docker Compose (including Celery worker(s), Redis, and — where the
  target environment has one — a GPU-enabled worker container for
  diffusion sampling)
- GitHub Actions
- Nginx
- Note: diffusion sampling and model fine-tuning genuinely benefit
  from GPU access. Design the worker layer so it runs correctly (if
  slowly) on CPU for local development and demoing, but document a
  clear path to a GPU-backed worker for anything beyond small demo
  batches.

## Testing

- Pytest
- Playwright
- A dedicated test suite for the cheminformatics layer: known-molecule
  round-trip tests (SMILES → RDKit → fingerprint → back), a fixed set
  of "golden" structure-diagram images with known-correct SMILES to
  regression-test the vision pipeline against

## Development Tooling

- VS Code
- Git / GitHub
- Postman

## Local vs. Cloud

Same three-mode philosophy as LexBook-AI, adapted for this project's
heavier compute needs:

`Local Mode (CPU, small demo batches, structured-data retrieval only)
→ Cloud Mode (GPU worker for generation/docking, full pipeline)
→ Enterprise Mode (multi-project, multi-user, dedicated GPU pool)`
