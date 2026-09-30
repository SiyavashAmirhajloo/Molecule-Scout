Molecule Scout — Claude Code configuration
==========================================

This file tells Claude Code which skills, commands, and tools to use inside this repository. The product workflow itself is defined in the root `CLAUDE.md` and the `docs/` folder; nothing here changes it.
Where skills live in this repository
------------------------------------

| Location            | What it contains                                                                  |
| ------------------- | --------------------------------------------------------------------------------- |
| `.claude/skills/`   | Design, UI, brand, and slide skills.                                              |
| `.agents/skills/`   | Frontend, React, web-standards, and SQLAlchemy/Alembic review skills.             |
| `.shared/`          | Python backend knowledge base, type checking, commit-message, and diagram skills. |
| `.claude/commands/` | Slash commands that wrap the `.shared/` skills.                                   |

Each skill has its own `SKILL.md` with frontmatter. Read that file before using the skill; the lists below are an index, not a substitute.
Project Skills (`.shared/`)
---------------------------

### 1. python-backend

Searchable knowledge base for Python backend development: FastAPI, security, database operations, caching, and best practices.See @.shared/python-backend/SKILL.md

Read `SKILL.md` and its `references/` directory directly. The `/kb-search` and `/kb-get` commands reference `.shared/python-backend/scripts/knowledge_db.py`, which does not exist on disk as of 2026-09-23 — restore that script or drop those commands.

### 2. commit-message

Analyze git changes and generate Conventional Commits; supports batch-commit splitting.See @.shared/commit-message/SKILL.md
    python3 .shared/commit-message/scripts/analyze_changes.py --batch
    python3 .shared/commit-message/scripts/analyze_changes.py --analyze

### 3. excalidraw-ai

Generate architecture diagrams, flowcharts, and data-flow visuals as Excalidraw JSON directly — no generator script required.See @.shared/excalidraw-ai/SKILL.md

Note: the `/excalidraw` command references `.shared/excalidraw-ai/scripts/excalidraw_generator.py`, which does not exist on disk as of 2026-09-23. Follow `SKILL.md` (JSON-direct method) instead.

### 4. ty-skills

Python type checking with `ty`, the fast Rust-based type checker from Astral.See @.shared/ty-skills/SKILL.md
    ty check .
    ty check <path>
Project Skills (`.claude/skills/`)
----------------------------------

| Skill           | Use it for                                                                          |
| --------------- | ----------------------------------------------------------------------------------- |
| `design-system` | Design tokens, component specs, and slide-system conventions.                       |
| `design`        | Logo, icon, banner, and CIP (creative-intelligence-prompt) style guidance.          |
| `brand`         | Brand guidelines, color-palette management, asset organization, consistency checks. |
| `ui-styling`    | Tailwind/CSS styling and canvas design-system conventions.                          |
| `ui-ux-pro-max` | Stack-specific UI/UX patterns: charts, motion, landing pages, React performance.    |
| `slides`        | Slide-deck authoring with slide background/chart/copy logic.                        |
| `banner-design` | Banner sizing and styles.                                                           |

Project Skills (`.agents/skills/`)
----------------------------------

| Skill                                                  | Use it for                                                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `frontend-design`                                      | Distinctive, non-templated visual design for new or reworked UI. Read before writing any UI.                       |
| `senior-frontend`                                      | Next.js/React performance, component scaffolding, bundle analysis.                                                 |
| `vercel-react-best-practices`                          | React correctness rules (effects, dependency arrays, async patterns). Read before changing hooks or data fetching. |
| `web-design-guidelines`                                | Web accessibility and interaction guidelines.                                                                      |
| `sqlalchemy-alembic-expert-best-practices-code-review` | Reviewing schema changes, migrations, indexes, and constraints.                                                    |

Commands
--------

* `/kb-search <query>` - Search python-backend knowledge base (broken: missing `knowledge_db.py`, see note above)
* `/kb-get <entry-id>` - Get full entry by ID (broken: same missing script)
* `/commit-batch` - Suggest batch commits for current changes
* `/commit-analyze` - Analyze git changes
* `/excalidraw <description>` - Generate diagram (broken: missing `excalidraw_generator.py`; use `.shared/excalidraw-ai/SKILL.md` directly)
* `/ty-check [path]` - Python type checking help

Host-Provided Tools and Connectors
----------------------------------

These come from the host environment rather than this repository. Use them when the task calls for it:

| Tool                                                            | Use it for                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `mcp__exa__web_search_exa`                                      | Web/literature search for the retrieval corpus and reference sourcing.                |
| `mcp__colab-mcp__*`                                             | GPU execution in Colab for diffusion training and vision experiments.                 |
| `mcp__workspace__bash`                                          | Isolated Linux sandbox; this repo mounts at `/sessions/<session>/mnt/Molecule-Scout`. |
| `mcp__workspace__web_fetch`                                     | Fetch a specific URL.                                                                 |
| `mcp__plugins__list_plugins`                                    | Show installed plugins.                                                               |
| `mcp__plugins__search_plugins`                                  | Search the plugin catalog by task intent.                                             |
| `mcp__plugins__suggest_plugin_install`                          | Render an install card for matched plugins.                                           |
| `mcp__skills__list_skills`                                      | Render the installed slash-menu skills widget.                                        |
| `mcp__skills__suggest_skills`                                   | Suggest standalone skills for a recurring workflow.                                   |
| `mcp__cowork__request_cowork_directory`                         | Request access to a folder outside the current mount.                                 |
| `mcp__cowork__present_files`                                    | Present finished files to the user.                                                   |
| `mcp__cowork__create_artifact` / `mcp__cowork__update_artifact` | Persisted HTML views.                                                                 |
| `mcp__cowork__save_skill`                                       | Save a reusable skill to the user's account.                                          |
| `mcp__scheduled-tasks__*`                                       | Recurring and one-time scheduled tasks.                                               |
| `Read` / `Edit` / `Write` / `Glob` / `grep`                     | File access and search.                                                               |
| `Bash`                                                          | Shell commands. Use `.venv\Scripts\python` on Windows or `python3` on POSIX.          |
| `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet`            | Track multi-step work.                                                                |
| `Agent`                                                         | Delegate open-ended exploration; include full context in the prompt.                  |
| `WebSearch`                                                     | Current or post-cutoff information.                                                   |

Session Skills (not repo-specific)
----------------------------------

These load via the `Skill` tool by name, independent of the repository:

| Skill                                 | Use it for                                                |
| ------------------------------------- | --------------------------------------------------------- |
| `anthropic-skills:docx`               | Creating, reading, or editing Word documents.             |
| `anthropic-skills:pdf`                | PDF creation, merging, splitting, OCR, forms, encryption. |
| `anthropic-skills:pdf-reading`        | Extracting text, tables, or images from existing PDFs.    |
| `anthropic-skills:xlsx`               | Spreadsheet work as the primary input or output.          |
| `anthropic-skills:pptx`               | PowerPoint creation, editing, or reading.                 |
| `anthropic-skills:frontend-design`    | Intentional visual design guidance for new UI.            |
| `anthropic-skills:schedule`           | Creating or updating scheduled tasks.                     |
| `anthropic-skills:setup-claude`       | Guided plugin/skill/tool setup.                           |
| `anthropic-skills:consolidate-memory` | Reflective pass over memory files.                        |
| `anthropic-skills:explain-usage`      | Token usage breakdown with a chart.                       |
| `init`                                | Initializing a new `CLAUDE.md`.                           |
| `security-review`                     | Security review of pending changes.                       |

Plugins
-------

No plugins were installed at last audit (2026-09-23). Check `mcp__plugins__list_plugins` before assuming; when a plugin is installed, audit its bundled skills and connectors and update both `CLAUDE.md` files.
Maintenance
-----------

On-disk `SKILL.md` files and plugin manifests win over these tables when they conflict. Re-audit and update this file when the user asks for a skills audit, "refresh skills", "refresh config", "update config", "update CLAUDE.md", or after installing/removing a skill or plugin.
