# Examples

Use these as reusable shapes, not templates to copy blindly.

## Before / After Rewrite

Before — every line fails the deletion test:

```md
# CLAUDE.md

This project is a web application built with modern technologies. The codebase
is organized as follows:
- src/ — source code
- tests/ — tests
- docs/ — documentation

Please write clean, maintainable code and follow best practices. Be careful
when modifying database-related code. Always make sure the code works before
committing. We use React for the frontend.
```

After — every surviving line names a command, file, or boundary the agent
cannot infer:

```md
# CLAUDE.md

## Stack
- React 19 / Vite 6 / pnpm 9 / PostgreSQL 16.

## Commands
- Test one file: `pnpm vitest run path/to/file.test.ts`
- Before finishing: `pnpm lint && pnpm typecheck && pnpm test`

## Non-Obvious Patterns
- DB access only through `src/db/queries.ts`; raw SQL elsewhere fails review.

## Boundaries
### Ask First
- Edit already-applied migrations in `migrations/`.
```

Why: the directory listing is discoverable, "best practices" and "be careful"
change no behavior, and "make sure the code works" became a concrete command.

## Minimal Root AGENTS.md

```md
# AGENTS.md

## Stack
- Node 22 / pnpm 10 / TypeScript strict / PostgreSQL 16.

## Commands
- Install: `pnpm install`
- Dev: `pnpm dev`
- Build: `pnpm build`
- Test all: `pnpm test`
- Test one: `pnpm vitest run path/to/file.test.ts`
- Typecheck: `pnpm typecheck`
- Lint: `pnpm lint`

## Non-Obvious Patterns
- API helpers return `ApiResult`; do not wrap them in try/catch unless the
  function explicitly throws.
- `src/generated/*` is generated. Change schemas and run `pnpm generate`.

## Boundaries
### Always
- Read files and run focused tests.
- Update tests when behavior changes.

### Ask First
- Add dependencies.
- Change database schemas or migrations.
- Delete files.

### Never
- Commit secrets or `.env` files.
- Modify `dist/`, `vendor/`, or generated files by hand.

## Verification
- Run the smallest relevant check before finishing.
- If a check cannot run, report the command and reason.
```

## Reference Map Section

```md
## Reference Map
- Read `docs/testing.md` before changing test helpers or CI.
- Read `docs/architecture.md` before changing cross-service contracts.
- Read `docs/release.md` only for release tasks.
```

## Nested Package Context

```md
# apps/web/AGENTS.md

## Web App Rules
- Use `pnpm --filter web test` for focused web tests.
- Run Playwright only when UI behavior, routing, or accessibility changes.
- Do not edit generated route files directly; run `pnpm --filter web routes`.
```

## Multi-Tool Adapter

Use when `AGENTS.md` is canonical but another tool expects a specific file.
Default for Claude Code — a one-line import adapter that inlines the canonical
file at load time, so only AGENTS.md is ever maintained:

```md
This repository uses AGENTS.md as the canonical agent context file; this file
only adapts it for Claude Code.

@AGENTS.md
```

Add Claude-specific content only when it really exists:

```md
@AGENTS.md

## Claude-Specific Notes
- [Only product-specific behavior here, e.g. skill or hook interactions.]
```

## Review Finding Format

```md
Findings
- High: `pnpm test` is listed, but `package.json` only defines `test:unit`.
  Replace with `pnpm test:unit` and add the single-test command from Vitest.
- Medium: "Be careful with migrations" is not actionable. Replace with the
  migration command and ask-first boundary.
- Low: The directory tree duplicates README content. Delete it or replace with
  a link to `README.md`.

Score: 74/100 (B)
Main risk: commands and boundaries are useful, but stale command names and
vague migration guidance will still cause mistakes.
```
