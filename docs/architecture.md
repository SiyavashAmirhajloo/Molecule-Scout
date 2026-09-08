# Architecture

## Approach

Molecule Scout is a multi-agent system orchestrated through LangGraph,
where each agent wraps a distinct, independently testable capability.
Slow agents (Vision, Generation, Docking) run as Celery background
jobs; the graph tracks job state and resumes orchestration once results
land, rather than blocking a request thread.

## Agents

| Agent | Responsibility | Speed |
|---|---|---|
| Coordinator | Routes an incoming request (new project, new target, regenerate candidates, re-run docking, etc.) to the right agent(s) | fast |
| Vision Agent | Locates structure diagrams in ingested literature/patents, converts each to SMILES with a confidence score | slow (background job) |
| Retrieval Agent | Embeds and indexes known molecules; given a target/seed, retrieves the most relevant known compounds with citations | fast |
| Generation Agent | Runs the retrieval-conditioned diffusion model to propose novel candidates | slow (background job) |
| Property Agent | Filters candidates using RDKit-based drug-likeness/safety heuristics | fast |
| Docking Agent | Docks surviving candidates against the target protein, computes a composite rank score | slow (background job) |
| Report Agent | Writes a plain-English rationale per candidate and assembles the final shareable report | fast (single LLM call per candidate) |
| Memory Agent | Persists project/target history, past candidate sets, and saved shortlists across sessions | fast |
| Evaluation Agent | Logs generation/retrieval/docking quality metrics for the project's own dashboard (not a research paper — a sanity-check layer) | fast |
| Safety Agent | Runs the dual-use screening pass described below on every generated candidate before it reaches the user | fast |

## LangGraph Workflow — Core Stages

```
intake (target + seed) 
   → literature ingestion [Vision Agent, background]
   → knowledge base indexing [Retrieval Agent]
   → retrieval [Retrieval Agent]
   → conditioned generation [Generation Agent, background]
   → safety screening [Safety Agent]
   → property filtering [Property Agent]
   → docking & ranking [Docking Agent, background]
   → report assembly [Report Agent]
   → memory write [Memory Agent]
```

The Coordinator can also re-enter this graph partway through — e.g.
"regenerate candidates with a tighter QED threshold" re-runs from the
conditioned-generation step without re-doing literature ingestion.

## Retrieval-Augmented Generation, for a Diffusion Model

This is the technical core of the project, and the direct analogue of
LLM-RAG applied to a diffusion model instead — grounded in the
published RetMol approach (NVIDIA) and the broader retrieval-augmented
diffusion literature (RDM, Re-Imagen, kNN-Diffusion) from the image
domain.

1. **Embed the retrieval corpus.** Every known molecule (from
   PubChem/ChEMBL and from the Vision Agent's extractions) is embedded
   via the molecule embedding abstraction layer (Morgan/ECFP
   fingerprints by default; a learned graph embedding as a swappable
   upgrade).
2. **Retrieve.** Given the project's target/seed, run a nearest-
   neighbor search (pgvector) to find the most structurally/
   functionally similar known compounds. This is a hybrid search in
   spirit: fingerprint similarity as the primary signal, with an
   optional secondary signal from any associated text (e.g. an
   abstract mentioning the compound's known activity), if available.
3. **Condition the diffusion model.** Project the retrieved
   molecules' embeddings into the diffusion model's conditioning
   space. Inject them during the denoising process:
   - If the backbone architecture exposes cross-attention (as EDM-
     style and DiGress-style implementations can be adapted to),
     inject the retrieved embeddings as cross-attention context at
     each denoising step, the same way a retrieved passage is injected
     into an LLM's context window.
   - If a lighter-touch integration is used instead, condition via a
     guidance vector (a classifier-free-guidance-style approach),
     nudging the sampling trajectory toward the retrieved molecules'
     region of chemical space without requiring an architecture change.
4. **Fallback when retrieval is weak.** If no sufficiently similar
   known compounds exist (e.g. a genuinely novel target), fall back to
   plain property-conditioned generation (target ranges for
   molecular weight, logP, QED) rather than forcing a conditioning
   signal from irrelevant retrieved molecules — and say so explicitly
   in the report ("no close literature analogs found; candidates
   generated from property targets only").

## Vision Pipeline: Structure Extraction from Literature

1. **Page ingestion.** Uploaded PDFs (or fetched open-access papers/
   patents) are rasterized page-by-page.
2. **Diagram localization.** A document-layout/object-detection model
   proposes bounding boxes for likely structure diagrams, distinct
   from figures, tables, and body text.
3. **Structure recognition.** Each cropped diagram is passed through
   DECIMER or MolScribe to produce a candidate SMILES string and a
   model confidence score.
4. **Validation.** The candidate SMILES is parsed with RDKit. Parse
   failure or chemically implausible output (e.g. impossible valence)
   demotes the extraction to low-confidence; it is stored but excluded
   from retrieval/generation conditioning unless a human confirms it.
5. **Context linking (OCR).** Nearby text (via Tesseract/EasyOCR) is
   scanned for compound identifiers (e.g. "Compound 3a", "IC50 = ...")
   to attach any available activity/annotation data to the extracted
   structure.
6. **Deduplication.** The extracted molecule is checked against the
   existing knowledge base (by canonical SMILES / InChIKey) before
   being added, so the same compound appearing in multiple papers
   doesn't fragment into duplicate retrieval entries.

## Property Filtering

Applied to every generated candidate before it proceeds to docking
(docking is the most expensive step — filter hard before it):

- **QED** (Quantitative Estimate of Drug-likeness)
- **SA score** (synthetic accessibility — how hard the molecule would
  actually be to synthesize)
- **Lipinski's Rule of Five** (molecular weight, logP, H-bond
  donors/acceptors)
- **PAINS filtering** (Pan-Assay Interference Compounds — structural
  patterns known to cause false positives in assays)

Each filter's pass/fail and raw value is stored and shown per
candidate — never collapsed into a single opaque "good/bad" flag.

## Docking & Composite Ranking

- Candidates surviving the Property Agent are docked against the
  target protein structure via AutoDock Vina.
- A composite rank score combines docking affinity, drug-likeness, and
  novelty (distance from the nearest retrieved known compound) —
  **the exact formula must be disclosed in the report and the UI**,
  following the same transparency principle used for LexBook-AI's
  readiness estimates. Example starting formula (tune empirically,
  document any change):
  `rank_score = 0.5 * normalized_docking_affinity + 0.3 * QED + 0.2 * novelty`
- Optional future backend: DiffDock, a diffusion-based pose predictor,
  as an alternate to Vina — see `docs/roadmap.md`.

## Evaluation Methodology

Use the field's actual benchmarks, not ad hoc judgment:

- **Validity** — fraction of generated molecules that are chemically
  valid (parseable, sensible valence)
- **Uniqueness** — fraction of valid generations that are distinct
  from each other
- **Novelty** — fraction of valid generations not present in the
  training/retrieval corpus
- **Internal diversity** — average pairwise Tanimoto distance among
  generated candidates (guards against mode collapse)
- **Benchmark suites**: MOSES and/or GuacaMol for standardized
  reporting of the above, so results are comparable to published work
- **Retrieval precision** — for a held-out set of known
  target/compound pairs, does the Retrieval Agent surface the true
  known actives near the top?
- **Docking sanity check** — where a benchmark target with known
  actives/decoys exists (e.g. a DUD-E target), confirm known actives
  score better than decoys as a sanity check on the docking setup

## Memory

- **Project memory** — target(s), seed molecule(s), and the full
  history of candidate sets generated for this project
- **Shortlist memory** — compounds the user explicitly saved/starred
- **Extraction memory** — literature sources already ingested, so
  re-visiting a project doesn't re-run vision extraction on the same
  PDF

## Observability

- Langfuse tracing across the LangGraph workflow, including background
  job stages (a trace should show the full path from "user submitted
  a target" through to "report delivered," even though the middle
  steps ran asynchronously)
- Structured logs per agent decision (which candidates were filtered
  and why, which docking runs failed and why)
- Job-level metrics: queue depth, average generation/docking latency,
  failure rate per job type

## Responsible Use & Dual-Use Safety Design

De novo molecular generation tools carry a real, acknowledged dual-use
risk: the same generative and property-prediction techniques used to
find promising drug candidates can, in principle, be pointed at
harmful ends (there is published research literature specifically
about this risk with generative chemistry models). Molecule Scout's
design includes concrete mitigations, not just a disclaimer:

- **Structural screening pass (Safety Agent).** Every generated
  candidate is checked against known toxic-scaffold and controlled-
  substance structural-analog libraries before it is shown to the
  user. A match blocks the candidate from the report rather than
  merely flagging it.
- **No toxicity-maximizing workflow.** The product only ever exposes
  generation conditioned toward *therapeutic* property targets (drug-
  likeness, binding affinity to a disclosed therapeutic target). There
  is no supported path to condition generation toward maximizing
  toxicity, lethality, or any property associated with chemical
  weapons — this is a hard product boundary, not a configurable
  option.
- **Logging and rate limiting.** All generation requests are logged
  with the requesting project/target, and generation throughput is
  rate-limited per user — both standard practice for any tool that can
  produce novel chemical structures at scale.
- **Human-in-the-loop framing.** The product's output is explicitly
  framed as a triage/prioritization aid for a human researcher, never
  as an autonomous "build this" instruction — the Report Agent's
  output emphasizes uncertainty and next-step verification (e.g.
  "requires wet-lab validation"), never a confident final answer.

This section should be treated as load-bearing, not boilerplate — it
belongs in the actual product design and the README, not just in this
doc.
