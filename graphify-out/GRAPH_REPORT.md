# Graph Report - Molecule-Scout  (2026-09-29)

## Corpus Check
- 192 files · ~69,549 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 6, .excalidrawlib 5, .ini 1)

## Summary
- 467 nodes · 804 edges · 27 communities (17 shown, 10 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21

## God Nodes (most connected - your core abstractions)
1. `parse_smiles()` - 26 edges
2. `get_embedder()` - 18 edges
3. `compilerOptions` - 16 edges
4. `KnownMolecule` - 15 edges
5. `compute_properties()` - 14 edges
6. `evaluate()` - 14 edges
7. `dock_molecules()` - 14 edges
8. `GitAnalyzer` - 12 edges
9. `create_project()` - 12 edges
10. `create_app()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `MoleculeTable Shared Comparison Table` --conceptually_related_to--> `V6 Docking & Composite Ranking`  [INFERRED]
  README.md → docs/roadmap.md
- `Elevator Pitch and Honest Framing` --rationale_for--> `Docking & Composite Ranking`  [INFERRED]
  CLAUDE.md → docs/architecture.md
- `Things Never to Cut` --rationale_for--> `V6 Docking & Composite Ranking`  [EXTRACTED]
  CLAUDE.md → docs/roadmap.md
- `V5 Status (current HEAD)` --references--> `V6 Docking & Composite Ranking`  [EXTRACTED]
  README.md → docs/roadmap.md
- `pdb_id Stored-String-Only Limitation` --rationale_for--> `V2 Project Intake & Retrieval`  [EXTRACTED]
  README.md → docs/roadmap.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Retrieval-to-Report Loop Agents** — docs_architecture_retrieval_agent, docs_architecture_generation_agent, docs_architecture_property_agent, docs_architecture_docking_agent, docs_architecture_report_agent [EXTRACTED 1.00]
- **V6 Deliverable Set** — docs_techstack_autodock_vina, docs_techstack_openbabel_mgltools, docs_architecture_rank_score_formula, docs_techstack_3dmol_ncl_viewer, docs_architecture_dud_e_sanity_check, docs_requirements_docking_result_entity [EXTRACTED 1.00]
- **Post-V6 Version Chain** — docs_roadmap_v7_multi_agent_orchestration, docs_roadmap_v8_report_agent, docs_roadmap_v9_vision_agent, docs_roadmap_v10_hardening [INFERRED 0.85]

## Communities (27 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (44): Elevator Pitch and Honest Framing, Tooling & Skill Routing, Coordinator Agent, Docking Agent, Docking & Composite Ranking, Dual-Use Safety Design, DUD-E Docking Sanity Check, Evaluation Agent (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (28): Bundle Analyzer Automated tool for senior frontend tasks, ComponentGenerator, main(), Main class for component generator functionality, Component Generator Automated tool for senior frontend tasks, Execute the main functionality, Validate the target path exists and is accessible, Perform the main analysis or operation (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (28): asyncio, canonical_smiles(), get_embedder(), MoleculeEmbedder, MorganFingerprintEmbedder, parse_smiles(), Mol, Protocol (+20 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (27): alembic_config, Settings, get_session(), AsyncSession, upgrade_schema(), create_app(), lifespan(), test_health_shape() (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (30): compute_properties(), LipinskiBreakdown, _pains_catalog(), PainsBreakdown, PropertyBreakdown, BaseModel, Mol, citation() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (14): alembic, DockingResult, Base, KnownMolecule, Project, client(), setup(), datetime (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (25): dock(), find_cocrystal_ligand(), get_receptor(), ligand_centroid(), prep_ligand(), Path, rank_batch(), V6 docking seam: ligand prep (RDKit + Meeko) + Vina subprocess dock + rank.… (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (28): dependencies, next, react, react-dom, devDependencies, autoprefixer, postcss, tailwindcss (+20 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (11): FileChange, GitAnalyzer, Path, Detect commit type based on files., Detect scope based on file paths., Generate commit description., Group changes into logical commits., Print analysis of changes. (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (17): evaluate(), GenerationMetrics, BaseModel, Mol, TestClient, test_avg_similarity_hand_computed(), test_project_generate_gates_on_retrieval(), test_project_generate_no_seed_422() (+9 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (20): Generation Agent, Property Agent, Property Filtering Gate, RetMol-Style Retrieval-Augmented Diffusion, Retrieval Agent, Fallback on Weak Retrieval, V0 Project Foundation, V1 Molecule Knowledge Base (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (15): denoise_from(), forward_noise(), generate_seeded(), Seed-graph init: start reverse diffusion from a noised retrieved molecule. The…, seed_graph(), checkpoint_id(), checkpoint_path(), GraphDiTBackend (+7 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (12): cellValue(), MoleculeRow, MoleculeTable(), Properties, SortKey, GeneratedCandidate, GenerationResult, Health (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.21
Nodes (7): BundleAnalyzer, main(), Main class for bundle analyzer functionality, Execute the main functionality, Validate the target path exists and is accessible, Perform the main analysis or operation, Generate and display the report

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (9): enqueue_generate(), enqueue_test_job(), GenerateRequest, get_job(), BaseModel, get, post, TestJobRequest (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.22
Nodes (9): AsyncSession, BaseModel, get, similar(), SimilarHit, description, ge, le (+1 more)

## Knowledge Gaps
- **68 isolated node(s):** `Properties`, `SortKey`, `metadata`, `Health`, `Hit` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 195 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_smiles()` connect `Community 2` to `Community 4`, `Community 6`, `Community 9`, `Community 11`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `GitAnalyzer` connect `Community 8` to `Community 1`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `BundleAnalyzer` connect `Community 14` to `Community 1`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `KnownMolecule` (e.g. with `citation()` and `resolve_seed()`) actually correct?**
  _`KnownMolecule` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Properties`, `SortKey`, `metadata` to the rest of the system?**
  _68 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05919661733615222 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06423034330011074 - nodes in this community are weakly interconnected._