---
description: Python type checking with ty - scan, create TODO list, fix systematically
argument-hint: [path or question]
---

Fix type errors in: $ARGUMENTS

## Workflow

1. **Scan**: Run `ty check .` or `ty check <path>` to identify all errors
2. **Plan**: Create a structured TODO list:
   - Group errors by file
   - Prioritize: imports → type annotations → complex patterns
   - Note the error code (e.g., `unresolved-import`, `invalid-argument-type`)
3. **Fix**: For each TODO item:
   - Read the relevant reference doc for that error type
   - Apply the fix
   - Mark TODO as complete
4. **Verify**: Run `ty check` again to confirm all errors are resolved

## Skill Documentation
- @.shared/ty-skills/SKILL.md

## References
- @.shared/ty-skills/references/typing_cheatsheet.md
- @.shared/ty-skills/references/ty_rules_reference.md
- @.shared/ty-skills/references/migration_guide.md
- @.shared/ty-skills/references/advanced_patterns.md
- @.shared/ty-skills/references/common_errors.md
