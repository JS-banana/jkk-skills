# Review Rubric

Use this file to review an existing or proposed AGENTS.md/CLAUDE.md-style
context file. Score only what is relevant to the target tool and repository.

## Critical Failures

Any critical failure should block a "good" rating until fixed:

- Commands are invented, stale, or contradict local manifests/CI.
- File contains secrets, credentials, tokens, or private endpoints that should
  not be committed.
- Rules permit destructive operations without confirmation.
- Instructions conflict without explicit priority.
- The file exceeds tool size limits or likely truncates important guidance.
- The file claims external research numbers without a local evidence source.

## Scorecard

Total: 100 points

| Dimension | Points | Checks |
| --- | ---: | --- |
| Source Truth | 20 | Commands and paths trace to local files; assumptions are labeled; stale claims removed. |
| Signal Density | 20 | Mostly non-inferable rules; little duplicated README content; root file stays lean. |
| Actionability | 20 | Rules are concrete, executable, and paired with commands, files, or examples. |
| Scope and Precedence | 15 | Global vs repo vs nested guidance is clear; multi-tool files do not drift. |
| Safety Boundaries | 15 | Always / Ask First / Never boundaries cover dependencies, deletion, secrets, DB/schema, git, generated files. |
| Verification | 10 | Completion checks and fallback reporting are explicit and realistic. |

Grade:

- S: 90-100, usable as-is.
- A: 80-89, minor edits.
- B: 70-79, usable but missing important precision.
- C: 60-69, needs focused rewrite.
- D: 40-59, likely harmful or noisy.
- F: under 40, replace from source truth.

## Review Procedure

1. Inventory files:
   - Root and nested context files.
   - Tool-specific instruction files.
   - Manifests and CI used to verify commands.

2. Verify claims:
   - Run or inspect scripts for every listed command.
   - Check package manager and language versions.
   - Confirm referenced paths exist.
   - Check whether protected directories are actually generated/vendor/build
     outputs.

3. Mark each issue:
   - Severity: critical / high / medium / low.
   - Category: stale, vague, redundant, missing, overbroad, conflict, unsafe.
   - Fix: delete, narrow, replace with command, move to nested file, or link.

4. Recommend shape:
   - Keep root if guidance applies repo-wide.
   - Split nested files if rules apply only to a package/service.
   - Consolidate parallel files if content is mostly shared.
   - Keep adapters if product-specific syntax is needed.

5. Report:
   - Findings first, ordered by severity.
   - Then score and short rationale.
   - Then proposed patch or rewritten file.

## Common Fix Patterns

Vague to actionable:

```md
Bad:
- Be careful with database migrations.

Good:
- Ask before editing an already-applied migration. For new migrations, run
  `alembic check` and `pytest tests/db` before finishing.
```

Redundant to pointer:

```md
Bad:
- [50 lines of release process copied from docs/release.md]

Good:
- Before release tasks, read `docs/release.md`; it is the canonical checklist.
```

Negative-only to alternative:

```md
Bad:
- Do not edit generated clients manually.

Good:
- Do not edit `src/generated/client/*` manually. Update the schema and run
  `pnpm generate:client`.
```

Overbroad to scoped:

```md
Bad:
- Always run the full test suite.

Good:
- Run the smallest relevant test first. Run `pnpm test` before finishing
  changes that touch shared packages or public APIs.
```

Conflict to priority:

```md
Bad:
- Ship quickly.
- Do not finish until all tests pass.

Good:
- Priority 1: preserve correctness and run required checks.
- Priority 2: keep the change small.
- Priority 3: optimize for speed.
```
