# Graph Report - Molecule-Scout  (2026-10-01)

## Corpus Check
- 192 files · ~76,774 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 6, .excalidrawlib 5, .ini 1)

## Summary
- 1327 nodes · 1672 edges · 175 communities (83 shown, 92 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6d0433bb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- V6 Build Prompt: Docking & Composite Ranking
- ComponentGenerator
- parse_smiles
- main.py
- projects.py
- conftest.py
- tasks.py
- package.json
- analyze_changes.py
- evaluate
- RetMol-Style Retrieval-Augmented Diffusion
- conditioned.py
- compilerOptions
- MoleculeTable.tsx
- BundleAnalyzer
- jobs.py
- molecules.py
- GeneratorBackend
- layout.tsx
- next.config.mjs
- Docker Compose Service Topology
- next-env.d.ts
- Migration Guide: mypy/pyright → ty
- Advanced Type Patterns
- Common ty Errors and Solutions
- Error Rules (Critical)
- Python Typing Cheatsheet
- Senior Frontend
- excalidraw-ai
- FastAPI Best Practices
- Upstash Patterns
- Database Patterns
- Cursor Setup for ty
- VS Code Setup for ty
- Frontend Best Practices
- Nextjs Optimization Guide
- React Patterns
- Neovim Setup for ty
- dock_sanity.py
- test_docking.py
- 5. Re-render Optimization
- compute_properties
- 7. JavaScript Performance
- Quick Reference
- [id]/page.tsx
- MorganFingerprintEmbedder
- app/docking.py
- UnknownPDBError
- Quick Patterns
- alembic
- bundle_analyzer.py
- FrontendScaffolder
- 6. Rendering Performance
- test_projects.py
- commit-message
- 3. Server-Side Performance
- Sections
- dock
- fetch_vina.py
- ty-skills
- test_conditioned.py
- V9 Vision Agent Structure Extraction
- PoseViewer.tsx
- devDependencies
- Security Patterns
- Frontend Design
- 1. Eliminating Waterfalls
- 2. Bundle Size Optimization
- ingest_chembl.py
- LangGraph Core Stages Workflow
- Dual-Use Safety Design
- V1 Molecule Knowledge Base
- SQLAlchemy & Alembic Expert Best Practices
- React Best Practices
- V6 Docking & Composite Ranking
- React Best Practices
- 4. Client-Side Data Fetching
- 8. Advanced Patterns
- Web Interface Guidelines
- prep_ligand
- CLAUDE.md
- async-cheap-condition-before-await.md
- Prefer Statically Analyzable Paths
- server-hoist-static-io.md
- rank_batch
- test_cocrystal_picks_largest_not_first
- ty-check.md
- dependencies
- scripts
- test_dock_unknown_pdb_422_and_unreachable_502
- Property Filtering Gate
- advanced-effect-event-deps.md
- advanced-event-handler-refs.md
- advanced-init-once.md
- advanced-use-latest.md
- async-api-routes.md
- async-dependencies.md
- async-parallel.md
- async-suspense-boundaries.md
- bundle-barrel-imports.md
- bundle-conditional.md
- bundle-defer-third-party.md
- bundle-dynamic-imports.md
- bundle-preload.md
- client-event-listeners.md
- client-localstorage-schema.md
- client-passive-event-listeners.md
- client-swr-dedup.md
- js-batch-dom-css.md
- js-cache-function-results.md
- js-cache-property-access.md
- js-cache-storage.md
- js-combine-iterations.md
- js-early-exit.md
- js-flatmap-filter.md
- js-hoist-regexp.md
- js-index-maps.md
- js-length-check-first.md
- js-min-max-loop.md
- js-request-idle-callback.md
- js-set-map-lookups.md
- js-tosorted-immutable.md
- rendering-activity.md
- rendering-animate-svg-wrapper.md
- rendering-conditional-render.md
- rendering-content-visibility.md
- rendering-hoist-jsx.md
- rendering-hydration-no-flicker.md
- rendering-hydration-suppress-warning.md
- rendering-resource-hints.md
- rendering-script-defer-async.md
- rendering-svg-precision.md
- rendering-usetransition-loading.md
- rerender-defer-reads.md
- rerender-dependencies.md
- rerender-derived-state.md
- rerender-derived-state-no-effect.md
- rerender-functional-setstate.md
- rerender-lazy-state-init.md
- rerender-memo.md
- rerender-memo-with-default-value.md
- rerender-move-effect-to-event.md
- rerender-no-inline-components.md
- rerender-simple-expression-in-memo.md
- rerender-split-combined-hooks.md
- rerender-transitions.md
- rerender-use-deferred-value.md
- rerender-use-ref-transient-values.md
- server-after-nonblocking.md
- server-auth-actions.md
- server-cache-lru.md
- server-dedup-props.md
- server-parallel-fetching.md
- server-parallel-nested-fetching.md
- server-serialization.md
- _template.md

## God Nodes (most connected - your core abstractions)
1. `parse_smiles()` - 27 edges
2. `get_embedder()` - 18 edges
3. `Python Typing Cheatsheet` - 18 edges
4. `dock_molecules()` - 16 edges
5. `compilerOptions` - 16 edges
6. `5. Re-render Optimization` - 16 edges
7. `compute_properties()` - 15 edges
8. `KnownMolecule` - 15 edges
9. `7. JavaScript Performance` - 15 edges
10. `evaluate()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `MoleculeTable Shared Comparison Table` --conceptually_related_to--> `V6 Docking & Composite Ranking`  [INFERRED]
  README.md → docs/roadmap.md
- `Elevator Pitch and Honest Framing` --rationale_for--> `Docking & Composite Ranking`  [INFERRED]
  CLAUDE.md → docs/architecture.md
- `V6 Build Prompt: Docking & Composite Ranking` --cites--> `Asynchronous by Design`  [EXTRACTED]
  prompts/v6-docking-ranking.md → docs/requirements.md
- `V7 Build Prompt: Multi-Agent Orchestration` --cites--> `Observability and Langfuse Tracing`  [INFERRED]
  prompts/v7-multi-agent-orchestration.md → docs/architecture.md
- `Reproducibility Requirement` --conceptually_related_to--> `V5 Status (current HEAD)`  [INFERRED]
  docs/requirements.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Retrieval-to-Report Loop Agents** — docs_architecture_retrieval_agent, docs_architecture_generation_agent, docs_architecture_property_agent, docs_architecture_docking_agent, docs_architecture_report_agent [EXTRACTED 1.00]
- **V6 Deliverable Set** — docs_techstack_autodock_vina, docs_techstack_openbabel_mgltools, docs_architecture_rank_score_formula, docs_techstack_3dmol_ncl_viewer, docs_architecture_dud_e_sanity_check, docs_requirements_docking_result_entity [EXTRACTED 1.00]
- **Post-V6 Version Chain** — docs_roadmap_v7_multi_agent_orchestration, docs_roadmap_v8_report_agent, docs_roadmap_v9_vision_agent, docs_roadmap_v10_hardening [INFERRED 0.85]

## Communities (175 total, 92 thin omitted)

### Community 0 - "V6 Build Prompt: Docking & Composite Ranking"
Cohesion: 0.17
Nodes (15): Elevator Pitch and Honest Framing, Docking & Composite Ranking, DUD-E Docking Sanity Check, Evaluation Agent, Evaluation Methodology, Novelty = distance from nearest retrieved known compound, rank_score = 0.5*norm_affinity + 0.3*QED + 0.2*novelty, DockingResult Core Data Entity (+7 more)

### Community 1 - "ComponentGenerator"
Cohesion: 0.21
Nodes (7): ComponentGenerator, main(), Main class for component generator functionality, Execute the main functionality, Validate the target path exists and is accessible, Perform the main analysis or operation, Generate and display the report

### Community 2 - "parse_smiles"
Cohesion: 0.35
Nodes (11): canonical_smiles(), get_embedder(), parse_smiles(), tanimoto(), test_fingerprint_stable_and_sized(), test_invalid_smiles_returns_none(), test_round_trip_canonical(), test_self_similarity_is_one() (+3 more)

### Community 3 - "main.py"
Cohesion: 0.13
Nodes (14): Settings, create_app(), lifespan(), test_health_shape(), test_enqueue_and_poll_eager(), BaseSettings, celery, contextlib (+6 more)

### Community 4 - "projects.py"
Cohesion: 0.18
Nodes (27): citation(), AsyncSession, Mol, resolve_seed(), retrieve(), create_project(), dock_candidates(), docking_detail() (+19 more)

### Community 5 - "conftest.py"
Cohesion: 0.25
Nodes (11): DockingResult, Base, KnownMolecule, persist(), client(), setup(), datetime, DeclarativeBase (+3 more)

### Community 6 - "tasks.py"
Cohesion: 0.18
Nodes (11): prepare_receptor(), Meeko PDB -> PDBQT (cached). Returns the receptor PDBQT path., checkpoint_id(), checkpoint_path(), GraphDiTBackend, add(), dock_molecules(), generate_molecules() (+3 more)

### Community 7 - "package.json"
Cohesion: 0.17
Nodes (11): name, private, version, autoprefixer, postcss, react-dom, tailwindcss, @types/node (+3 more)

### Community 8 - "analyze_changes.py"
Cohesion: 0.09
Nodes (18): collections, dataclasses, fnmatch, CommitGroup, FileChange, GitAnalyzer, main(), Path (+10 more)

### Community 9 - "evaluate"
Cohesion: 0.18
Nodes (11): evaluate(), GenerationMetrics, BaseModel, Mol, test_avg_similarity_hand_computed(), FakeBackend, TestClient, test_backend_contract() (+3 more)

### Community 10 - "RetMol-Style Retrieval-Augmented Diffusion"
Cohesion: 0.24
Nodes (11): Generation Agent, RetMol-Style Retrieval-Augmented Diffusion, Retrieval Agent, Fallback on Weak Retrieval, V3 Property Filtering Pipeline, V4 Baseline Generative Agent, V5 Retrieval-Augmented Generation, Graph-DiT via torch-molecule (V4 backbone) (+3 more)

### Community 11 - "conditioned.py"
Cohesion: 0.24
Nodes (10): denoise_from(), forward_noise(), generate_seeded(), Seed-graph init: start reverse diffusion from a noised retrieved molecule. The…, seed_graph(), numpy, random, torch (+2 more)

### Community 12 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 13 - "MoleculeTable.tsx"
Cohesion: 0.25
Nodes (6): cellValue(), MoleculeRow, MoleculeTable(), Properties, RANK_FORMULA, SortKey

### Community 14 - "BundleAnalyzer"
Cohesion: 0.21
Nodes (7): BundleAnalyzer, main(), Main class for bundle analyzer functionality, Execute the main functionality, Validate the target path exists and is accessible, Perform the main analysis or operation, Generate and display the report

### Community 15 - "jobs.py"
Cohesion: 0.27
Nodes (8): enqueue_generate(), enqueue_test_job(), GenerateRequest, get_job(), BaseModel, TestJobRequest, celery_result, pydantic

### Community 16 - "molecules.py"
Cohesion: 0.18
Nodes (12): alembic_config, AsyncSession, BaseModel, similar(), SimilarHit, get_session(), AsyncSession, description (+4 more)

### Community 18 - "layout.tsx"
Cohesion: 0.20
Nodes (5): frontend_app_globals, metadata, Home(), next, react

### Community 27 - "Migration Guide: mypy/pyright → ty"
Cohesion: 0.06
Nodes (35): 1. Install ty, 1. Strictness Modes, 2. Plugin System, 2. Run Initial Check, 3. Create Configuration, 3. Custom Type Stubs, 4. Inline Type Comments, CI/CD Updates (+27 more)

### Community 28 - "Advanced Type Patterns"
Cohesion: 0.06
Nodes (32): Abstract Factory with Protocol, Advanced Type Patterns, Basic Intersection, Basic Protocol, Basic TypeGuard, Callback Protocol, Class Decorator, Context Manager Typing (+24 more)

### Community 29 - "Common ty Errors and Solutions"
Cohesion: 0.06
Nodes (32): 1. Use reveal_type, 2. Run with Full Output, 3. Check Specific Files, 4. Ignore Temporarily, Common ty Errors and Solutions, Debugging Tips, division-by-zero, Example 1: Conditional Assignment (+24 more)

### Community 30 - "Error Rules (Critical)"
Cohesion: 0.06
Nodes (32): Configuration, division-by-zero, Error Rules (Critical), File-Level Suppression, Gradual Adoption Strategy, incompatible-assignment, index-out-of-bounds, invalid-argument-type (+24 more)

### Community 31 - "Python Typing Cheatsheet"
Cohesion: 0.07
Nodes (27): Annotated, Async Types, Basic Types, Callable Types, Common Patterns, Container Types (Python 3.9+), Context Manager, Factory Function (+19 more)

### Community 32 - "Senior Frontend"
Cohesion: 0.07
Nodes (26): 1. Component Generator, 1. Setup and Configuration, 2. Bundle Analyzer, 2. Run Quality Checks, 3. Frontend Scaffolder, 3. Implement Best Practices, Best Practices Summary, Code Quality (+18 more)

### Community 33 - "excalidraw-ai"
Cohesion: 0.08
Nodes (25): Architecture Diagram Layout, Arrow, Arrow Properties, Color Palette Reference, Complete Example, Component-Based Colors (Recommended for Architecture Diagrams), Diamond, Element Properties Reference (+17 more)

### Community 34 - "FastAPI Best Practices"
Cohesion: 0.08
Nodes (25): API Design, Async Routes, Async Test Client from Day 0, Chain Dependencies, CPU Intensive Tasks, Custom Base Model, Decouple BaseSettings, Dependencies (+17 more)

### Community 35 - "Upstash Patterns"
Cohesion: 0.08
Nodes (23): Basic Setup, Batch Messages, Best Practices, FastAPI Caching, FastAPI Rate Limiting, FastAPI Session Management, Hash Operations, Key Expiration (TTL) (+15 more)

### Community 36 - "Database Patterns"
Cohesion: 0.09
Nodes (22): Alembic Migration Naming, Async Engine + Session, Bulk Insert, Bulk Operations, Bulk Update, Cascade Delete, Commit/Rollback Pattern, Constraint Naming (+14 more)

### Community 37 - "Cursor Setup for ty"
Cohesion: 0.09
Nodes (22): 1. ty Integration, 2. Install ty CLI, AI-Powered Fixes, Configuration, Conflicts with Other Type Checkers, Cursor Setup for ty, Explain Type Errors, Features (+14 more)

### Community 38 - "VS Code Setup for ty"
Cohesion: 0.09
Nodes (21): 1. Install ty Extension, 2. Install ty CLI, Code Actions, Configuration, Conflicts with Pylance, Diagnostics, Features, Find References (+13 more)

### Community 39 - "Frontend Best Practices"
Cohesion: 0.10
Nodes (20): Anti-Pattern 1, Anti-Pattern 2, Anti-Patterns to Avoid, Code Organization, Common Patterns, Conclusion, Frontend Best Practices, Further Reading (+12 more)

### Community 40 - "Nextjs Optimization Guide"
Cohesion: 0.10
Nodes (20): Anti-Pattern 1, Anti-Pattern 2, Anti-Patterns to Avoid, Code Organization, Common Patterns, Conclusion, Further Reading, Guidelines (+12 more)

### Community 41 - "React Patterns"
Cohesion: 0.10
Nodes (20): Anti-Pattern 1, Anti-Pattern 2, Anti-Patterns to Avoid, Code Organization, Common Patterns, Conclusion, Further Reading, Guidelines (+12 more)

### Community 42 - "Neovim Setup for ty"
Cohesion: 0.11
Nodes (18): 1. Install ty, 2. Configure Neovim, Basic Configuration, Conflicts with Other LSPs, Diagnostics Display, Disable Conflicting Servers, Installation, Integration with null-ls / none-ls (+10 more)

### Community 43 - "dock_sanity.py"
Cohesion: 0.16
Nodes (15): bootstrap_auc_ci(), enrichment_factor(), fetch_dataset(), main(), DUD-E EGFR docking smoke test. SMOKE TEST, NOT A BENCHMARK. It answers one…, Percentile 95% CI for AUC, resampling pairs with replacement., EF@k = (hits_k / k) / (n_actives / n_total). Higher score = ranks first. Also…, Return (actives, decoys) SMILES, downloading the tarball once. (+7 more)

### Community 44 - "test_docking.py"
Cohesion: 0.18
Nodes (15): parse_affinity(), First Vina result affinity, or None. Parsing this wrong silently corrupts every…, TestClient, The ranked rows must carry persisted ids (the pose viewer fetches by id) and…, test_create_project_rejects_bad_pdb_id(), test_dock_bad_smiles_422(), test_dock_batch_capped_422(), test_dock_job_payload_ids_and_properties() (+7 more)

### Community 45 - "5. Re-render Optimization"
Cohesion: 0.12
Nodes (16): 5.10 Subscribe to Derived State, 5.11 Use Functional setState Updates, 5.12 Use Lazy State Initialization, 5.13 Use Transitions for Non-Urgent Updates, 5.14 Use useDeferredValue for Expensive Derived Renders, 5.15 Use useRef for Transient Values, 5.1 Calculate Derived State During Rendering, 5.2 Defer State Reads to Usage Point (+8 more)

### Community 46 - "compute_properties"
Cohesion: 0.20
Nodes (14): compute_properties(), LipinskiBreakdown, _pains_catalog(), PainsBreakdown, PropertyBreakdown, BaseModel, Mol, test_aspirin_breakdown() (+6 more)

### Community 47 - "7. JavaScript Performance"
Cohesion: 0.13
Nodes (15): 7.10 Hoist RegExp Creation, 7.11 Use flatMap to Map and Filter in One Pass, 7.12 Use Loop for Min/Max Instead of Sort, 7.13 Use Set/Map for O(1) Lookups, 7.14 Use toSorted() Instead of sort() for Immutability, 7.1 Avoid Layout Thrashing, 7.2 Build Index Maps for Repeated Lookups, 7.3 Cache Property Access in Loops (+7 more)

### Community 48 - "Quick Reference"
Cohesion: 0.13
Nodes (14): 1. Eliminating Waterfalls (CRITICAL), 2. Bundle Size Optimization (CRITICAL), 3. Server-Side Performance (HIGH), 4. Client-Side Data Fetching (MEDIUM-HIGH), 5. Re-render Optimization (MEDIUM), 6. Rendering Performance (MEDIUM), 7. JavaScript Performance (LOW-MEDIUM), 8. Advanced Patterns (LOW) (+6 more)

### Community 49 - "[id]/page.tsx"
Cohesion: 0.14
Nodes (11): DockedRow, DockingDetail, DockingResult, GeneratedCandidate, GenerationResult, Project, ProjectPage(), ProjectResponse (+3 more)

### Community 50 - "MorganFingerprintEmbedder"
Cohesion: 0.18
Nodes (6): MoleculeEmbedder, MorganFingerprintEmbedder, Mol, Protocol, _to_bv(), ExplicitBitVect

### Community 51 - "app/docking.py"
Cohesion: 0.18
Nodes (13): find_cocrystal_ligand(), ligand_centroid(), _meeko_bin(), V6 docking seam: ligand prep (RDKit + Meeko) + Vina subprocess dock + rank.…, Largest credible co-crystal ligand + its centroid, else None (caller 422s).…, Resolve a Meeko console script. Returns a command list ready to pass to…, (returncode, stdout, stderr). Never raises — dock() decides what a failure…, _residue_heavy_atoms() (+5 more)

### Community 52 - "UnknownPDBError"
Cohesion: 0.16
Nodes (13): _fetch_pdb(), Well-formed PDB ID that RCSB does not have (404)., RCSB unreachable / network failure — upstream problem, not user input., Download pdb_id to dest atomically. Raises UnknownPDBError / ReceptorFetchError., ReceptorFetchError, UnknownPDBError, A raw network error must never escape _fetch_pdb as a 500., test_fetch_pdb_wraps_missing_structure() (+5 more)

### Community 53 - "Quick Patterns"
Cohesion: 0.14
Nodes (13): Async Routes, Core Principles, Dependency Injection, Project Structure, Pydantic Validation, python-backend, Quick Patterns, Rate Limiting (+5 more)

### Community 55 - "bundle_analyzer.py"
Cohesion: 0.29
Nodes (8): Bundle Analyzer Automated tool for senior frontend tasks, Component Generator Automated tool for senior frontend tasks, Frontend Scaffolder Automated tool for senior frontend tasks, argparse, json, pathlib, sys, typing

### Community 56 - "FrontendScaffolder"
Cohesion: 0.21
Nodes (7): FrontendScaffolder, main(), Main class for frontend scaffolder functionality, Execute the main functionality, Validate the target path exists and is accessible, Perform the main analysis or operation, Generate and display the report

### Community 57 - "6. Rendering Performance"
Cohesion: 0.17
Nodes (12): 6.10 Use React DOM Resource Hints, 6.11 Use useTransition Over Manual Loading States, 6.1 Animate SVG Wrapper Instead of SVG Element, 6.2 CSS content-visibility for Long Lists, 6.3 Hoist Static JSX Elements, 6.4 Optimize SVG Precision, 6.5 Prevent Hydration Mismatch Without Flickering, 6.6 Suppress Expected Hydration Mismatches (+4 more)

### Community 58 - "test_projects.py"
Cohesion: 0.29
Nodes (11): TestClient, One UI field accepts either form: a compound name sent as seed_smiles resolves…, test_bad_smiles_422(), test_both_seeds_422(), test_create_by_name_resolves(), test_create_by_smiles_self_hit(), test_empty_body_422(), test_project_ids_increment() (+3 more)

### Community 59 - "commit-message"
Cohesion: 0.17
Nodes (11): Batch Commit Workflow, Commands, commit-message, Commit Types, Context-Aware Commit Messages, Grouping Strategy, Input/Output Examples, Key Principles (+3 more)

### Community 60 - "3. Server-Side Performance"
Cohesion: 0.18
Nodes (10): 3.10 Use after() for Non-Blocking Operations, 3.1 Authenticate Server Actions Like API Routes, 3.2 Avoid Duplicate Serialization in RSC Props, 3.3 Avoid Shared Module State for Request Data, 3.4 Cross-Request LRU Caching, 3.5 Hoist Static I/O to Module Level, 3.6 Minimize Serialization at RSC Boundaries, 3.7 Parallel Data Fetching with Component Composition (+2 more)

### Community 61 - "Sections"
Cohesion: 0.20
Nodes (9): 1. Eliminating Waterfalls (async), 2. Bundle Size Optimization (bundle), 3. Server-Side Performance (server), 4. Client-Side Data Fetching (client), 5. Re-render Optimization (rerender), 6. Rendering Performance (rendering), 7. JavaScript Performance (js), 8. Advanced Patterns (advanced) (+1 more)

### Community 62 - "dock"
Cohesion: 0.22
Nodes (7): _default_vina_bin(), dock(), Path, Run Vina. Returns (affinity, pose PDBQT) or (None, None) on any failure., Vina is a subprocess binary, not a pip package. ``VINA_BIN`` wins when set…, test_dock_with_fake_runner_needs_no_binary(), VinaRunner

### Community 63 - "fetch_vina.py"
Cohesion: 0.27
Nodes (8): main(), platform_asset(), Path, Provision the AutoDock Vina binary (idempotent, checksum-verified). The pip…, sha256(), hashlib, os, platform

### Community 64 - "ty-skills"
Cohesion: 0.20
Nodes (9): Configuration, Intersection Types (ty Exclusive), Quick Start, Reference Documents, Resources, Rules Quick Reference, Suppression Comments, ty-skills (+1 more)

### Community 65 - "test_conditioned.py"
Cohesion: 0.39
Nodes (6): TestClient, test_project_generate_gates_on_retrieval(), test_project_generate_no_seed_422(), test_project_generate_unknown_404(), test_raw_generate_accepts_seed_fields(), test_raw_generate_bad_seed_422()

### Community 66 - "V9 Vision Agent Structure Extraction"
Cohesion: 0.25
Nodes (8): Safety Agent, Vision Agent, Vision Pipeline Structure Extraction, V10 Production Hardening & Safety, V9 Vision Agent Structure Extraction, Build in Versions, De-Risk the Hard Part Last, V10 Build Prompt, V9 Build Prompt: Vision Agent

### Community 67 - "PoseViewer.tsx"
Cohesion: 0.29
Nodes (7): ensureScript(), MolGlobal, MolViewer3D, PoseViewer(), Props, Window, PoseViewer

### Community 68 - "devDependencies"
Cohesion: 0.25
Nodes (8): devDependencies, autoprefixer, postcss, tailwindcss, @types/node, @types/react, @types/react-dom, typescript

### Community 69 - "Security Patterns"
Cohesion: 0.25
Nodes (7): API Key Auth via Header, CORS Configuration, FastAPI OAuth2 Bearer Dependency, Hide OpenAPI Docs by Default, JWT Create/Verify (python-jose), Password Hashing (passlib + bcrypt), Security Patterns

### Community 70 - "Frontend Design"
Cohesion: 0.29
Nodes (6): Design principles, Frontend Design, Ground your designs in the subject matter, More on writing in design, Process: plan, review against the brief, build, critique, Restraint and self-critique

### Community 71 - "1. Eliminating Waterfalls"
Cohesion: 0.29
Nodes (7): 1.1 Check Cheap Conditions Before Async Flags, 1.2 Defer Await Until Needed, 1.3 Dependency-Based Parallelization, 1.4 Prevent Waterfall Chains in API Routes, 1.5 Promise.all() for Independent Operations, 1.6 Strategic Suspense Boundaries, 1. Eliminating Waterfalls

### Community 72 - "2. Bundle Size Optimization"
Cohesion: 0.29
Nodes (7): 2.1 Avoid Barrel File Imports, 2.2 Conditional Module Loading, 2.3 Defer Non-Critical Third-Party Libraries, 2.4 Dynamic Imports for Heavy Components, 2.5 Prefer Statically Analyzable Paths, 2.6 Preload Based on User Intent, 2. Bundle Size Optimization

### Community 73 - "ingest_chembl.py"
Cohesion: 0.38
Nodes (5): asyncio, upgrade_schema(), fetch_page(), main(), Ingest ChEMBL approved drugs (max_phase=4) into known_molecules. Slice:…

### Community 74 - "LangGraph Core Stages Workflow"
Cohesion: 0.33
Nodes (7): Coordinator Agent, Docking Agent, LangGraph Core Stages Workflow, Observability and Langfuse Tracing, Asynchronous by Design, Celery + Redis Mandatory, V7 Build Prompt: Multi-Agent Orchestration

### Community 75 - "Dual-Use Safety Design"
Cohesion: 0.33
Nodes (7): Dual-Use Safety Design, Memory Agent, Report Agent, Safety Pass Cannot Be Disabled, V7 Multi-Agent Orchestration via LangGraph, V8 Report Agent & Research Notebook, V8 Build Prompt: Report Agent & Notebook

### Community 76 - "V1 Molecule Knowledge Base"
Cohesion: 0.33
Nodes (7): V0 Project Foundation, V1 Molecule Knowledge Base, V2 Project Intake & Retrieval, V1 Build Prompt, V2 Build Prompt, 3,417 ChEMBL Approved Drugs Corpus, pdb_id Stored-String-Only Limitation

### Community 77 - "SQLAlchemy & Alembic Expert Best Practices"
Cohesion: 0.33
Nodes (5): How to Use, Quick Reference, Rule Categories by Priority, SQLAlchemy & Alembic Expert Best Practices, When to Apply

### Community 78 - "React Best Practices"
Cohesion: 0.33
Nodes (5): Creating a New Rule, Getting Started, React Best Practices, Rule File Structure, Structure

### Community 79 - "V6 Docking & Composite Ranking"
Cohesion: 0.33
Nodes (6): Tooling & Skill Routing, Reproducibility Requirement, Things Never to Cut, V6 Docking & Composite Ranking, V5 Status (current HEAD), MoleculeTable Shared Comparison Table

### Community 80 - "React Best Practices"
Cohesion: 0.40
Nodes (4): Abstract, React Best Practices, References, Table of Contents

### Community 81 - "4. Client-Side Data Fetching"
Cohesion: 0.40
Nodes (5): 4.1 Deduplicate Global Event Listeners, 4.2 Use Passive Event Listeners for Scrolling Performance, 4.3 Use SWR for Automatic Deduplication, 4.4 Version and Minimize localStorage Data, 4. Client-Side Data Fetching

### Community 82 - "8. Advanced Patterns"
Cohesion: 0.40
Nodes (5): 8.1 Do Not Put Effect Events in Dependency Arrays, 8.2 Initialize App Once, Not Per Mount, 8.3 Store Event Handlers in Refs, 8.4 useEffectEvent for Stable Callback Refs, 8. Advanced Patterns

### Community 83 - "Web Interface Guidelines"
Cohesion: 0.40
Nodes (4): Guidelines Source, How It Works, Usage, Web Interface Guidelines

### Community 84 - "prep_ligand"
Cohesion: 0.40
Nodes (5): prep_ligand(), SMILES -> PDBQT string via RDKit ETKDG + Meeko. None if unpreppable. Returns…, Salts/dotted SMILES are multi-fragment; Meeko rejects those outright. We strip…, test_multifragment_ligand_keeps_parent_and_never_raises(), test_oversized_ligand_excluded_not_docked()

### Community 85 - "CLAUDE.md"
Cohesion: 0.40
Nodes (4): 1. python-backend, 2. commit-message, 3. excalidraw-ai, 4. ty-skills

### Community 87 - "Prefer Statically Analyzable Paths"
Cohesion: 0.50
Nodes (3): File-System Paths, Import Paths, Prefer Statically Analyzable Paths

### Community 89 - "rank_batch"
Cohesion: 0.50
Nodes (4): rank_batch(), Attach norm_affinity + rank_score in place. Failed (None affinity) sort last,…, test_rank_all_equal_affinities(), test_rank_math_hand_computed()

### Community 90 - "test_cocrystal_picks_largest_not_first"
Cohesion: 0.67
Nodes (4): _hetatm(), _pdb(), test_cocrystal_picks_largest_not_first(), test_cocrystal_threshold_and_exclusions()

### Community 91 - "ty-check.md"
Cohesion: 0.50
Nodes (3): References, Skill Documentation, Workflow

### Community 92 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, next, react, react-dom

### Community 93 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, start

### Community 95 - "Property Filtering Gate"
Cohesion: 0.67
Nodes (3): Property Agent, Property Filtering Gate, V3 Build Prompt

## Knowledge Gaps
- **596 isolated node(s):** `Properties`, `RANK_FORMULA`, `SortKey`, `Props`, `MolViewer3D` (+591 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 866 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **92 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_smiles()` connect `parse_smiles` to `projects.py`, `tasks.py`, `evaluate`, `ingest_chembl.py`, `conditioned.py`, `jobs.py`, `molecules.py`, `MorganFingerprintEmbedder`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `evaluate()` connect `evaluate` to `test_conditioned.py`, `parse_smiles`, `tasks.py`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `dock_molecules()` (e.g. with `DockingResult` and `KnownMolecule`) actually correct?**
  _`dock_molecules()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Properties`, `RANK_FORMULA`, `SortKey` to the rest of the system?**
  _596 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._
- **Should `analyze_changes.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09269162210338681 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._