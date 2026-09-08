# open-python-skills

Python backend development expertise for FastAPI, security, database, caching, and best practices

## Available Skills

Skills are installed in `.shared/` directory. Each skill has a SKILL.md with instructions.

### 1. python-backend
Searchable knowledge base for Python backend development.
See @.shared/python-backend/SKILL.md

```bash
python3 .shared/python-backend/scripts/knowledge_db.py "query"
python3 .shared/python-backend/scripts/knowledge_db.py --get <entry-id>
```

### 2. commit-message
Analyze git changes and generate commit messages.
See @.shared/commit-message/SKILL.md

```bash
python3 .shared/commit-message/scripts/analyze_changes.py --batch
python3 .shared/commit-message/scripts/analyze_changes.py --analyze
```

### 3. excalidraw-ai
Generate diagrams from text.
See @.shared/excalidraw-ai/SKILL.md

```bash
python3 .shared/excalidraw-ai/scripts/excalidraw_generator.py "description"
```

### 4. ty-skills
Python type checking with ty.
See @.shared/ty-skills/SKILL.md

## Commands

- `/kb-search` - Search python-backend knowledge base
- `/kb-get` - Get full entry by ID
- `/commit-batch` - Suggest batch commits for current changes
- `/commit-analyze` - Analyze git changes
- `/excalidraw` - Generate diagram
- `/ty-check` - Python type checking help
