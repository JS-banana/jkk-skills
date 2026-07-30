# Method

Use this file before creating, rewriting, consolidating, or deeply reviewing
agent context files.

## Goal

An agent context file is a compact operating manual for coding agents. It should
answer only what the agent cannot reliably infer from the repository:

- Which commands to run and in what scope.
- Which local conventions look surprising but are intentional.
- Which operations are always allowed, require confirmation, or are forbidden.
- Which checks prove a task is complete.
- Where deeper project docs live and when to read them.

It is not a README, architecture guide, changelog, onboarding manual, or style
guide for humans.

## Cost Model

Context files are loaded into every session. Each line has a recurring token
cost and competes with task context, so a rule earns its place only by
preventing a likely mistake or saving repeated discovery. This is the core
difference from human docs: a README is read once by a person who needs
persuasion and visual hierarchy; a context file is read every run by a machine
that needs facts it cannot infer.

Apply the deletion test line by line: if removing the line would not change how
the agent behaves, delete it.

## Language

Match the language of the repository's existing context files and team
communication. If the team works in Chinese, write the context file in Chinese;
commands, paths, and code identifiers stay verbatim. Do not mix languages
within one file without reason.

## Source Discovery

Read local source-of-truth files before writing:

- Existing `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `.cursorrules`,
  `.cursor/rules/*`, `.github/copilot-instructions.md`, `GEMINI.md`.
- Manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
  `pom.xml`, `build.gradle`, `Makefile`, `justfile`, `Taskfile.yml`.
- CI and verification: `.github/workflows/*`, test config, lint config,
  typecheck config, formatter config.
- Project docs that are already canonical: `README.md`, `CONTRIBUTING.md`,
  `docs/*`, ADRs, architecture notes.

Do not invent commands from ecosystem defaults when a local manifest or CI file
exists. If a command is likely but unverified, label it as an assumption.

## Decision Process

1. Define scope:
   - Global user guidance belongs in the user's global config.
   - Repository-wide guidance belongs in root `AGENTS.md`.
   - Package or service-specific guidance belongs in nested context files.
   - Tool-specific files are adapters unless the tool requires unique syntax.

2. Classify content:
   - Include: non-inferable commands, unusual tools, exact verification gates,
     dangerous operations, project-specific contracts, hard-won repeated agent
     mistakes.
   - Link: long testing guides, domain docs, schema docs, architecture notes,
     release playbooks.
   - Exclude: directory listings, generic style advice, prose copied from
     README, long architecture summaries, one-off bug notes.

3. Write the narrowest useful rule:
   - Bad: "Be careful with migrations."
   - Better: "Before editing migrations, run `alembic check`; ask before
     changing an already-applied migration."
   - Bad: "Use clean code."
   - Better: "Use `Result<T, ApiError>` from `src/core/result.ts`; do not throw
     from service-layer functions."

4. Prefer positive alternatives:
   - "Do not instantiate HTTP clients directly. Use `src/lib/apiClient.ts`."
   - "Do not run the full browser suite for CSS-only edits. Run
     `pnpm test:visual -- --changed`."

5. Keep the root short:
   - Target 80-180 lines for most repos.
   - Treat 300 lines as a warning.
   - If a section grows because it applies only to one package, move it into a
     nested context file or linked doc.

## Recommended Shape

Use headings only when there is real content.

```md
# AGENTS.md

## Stack
- Node 22 / pnpm 10 / React 19 / TypeScript strict.

## Commands
- Install: `pnpm install`
- Dev: `pnpm dev`
- Build: `pnpm build`
- Test all: `pnpm test`
- Test one: `pnpm vitest run path/to/file.test.ts`
- Typecheck: `pnpm typecheck`
- Lint: `pnpm lint`

## Non-Obvious Patterns
- `client.api` returns `ApiResult`; wrapping it in try/catch is incorrect.
- Generated files in `src/generated/` are source-controlled; update them with
  `pnpm generate`, not manual edits.

## Boundaries
### Always
- Read files and run single-test commands.
- Update tests when changing behavior.

### Ask First
- Add or remove dependencies.
- Change database schemas or migrations.
- Start services that bind external ports.

### Never
- Commit secrets or `.env` files.
- Modify `vendor/`, `dist/`, or generated snapshots by hand.

## Verification
- Before finishing code changes, run the smallest relevant check.
- If a required check cannot run, report the command and failure reason.

## Reference Map
- Read `docs/testing.md` before changing test infrastructure.
- Read `docs/architecture.md` before changing cross-service contracts.
```

## Multi-Tool Strategy

Default to one canonical source.

- Use `AGENTS.md` as the canonical cross-tool context when the repo supports
  multiple agents.
- For Claude Code, add a `CLAUDE.md` whose content is a one-line `@AGENTS.md`
  import: it inlines the canonical file at load time. A prose pointer like
  "read AGENTS.md first" is weaker — it costs an extra action and is not
  guaranteed to be followed. Note that Claude Code does not load `AGENTS.md`
  by itself, so an AGENTS.md-only repo silently loses Claude Code coverage.
- Use Cursor or Copilot-specific files only for product-specific scoping,
  frontmatter, or activation behavior.
- Avoid maintaining parallel copies with similar content.

When consolidating:

1. Compare all files for unique instructions.
2. Move shared instructions into `AGENTS.md`.
3. Keep tool-specific files as short adapters or scoped rule files.
4. Document which file is canonical.
5. Tell the user if restarting the agent session is required for discovery.

## Update Strategy

Update context after real evidence, not speculation.

Good triggers:

- The agent repeatedly makes the same mistake.
- A command, package manager, or verification gate changes.
- A finalized architecture decision changes how agents should work.
- A path-specific rule becomes stable enough to document.

Avoid:

- Adding a rule for a one-off bug.
- Encoding temporary workaround details.
- Full rewrites when a single stale command needs changing.

Use this update template:

```md
Problem observed:
- [exact mistake]

Root cause in context:
- Missing / vague / stale / overbroad rule.

Smallest durable edit:
- [new rule or deletion]

Verification:
- [file or command proving the edit is accurate]
```

## Platform Notes

Claude Code:

- Loads user-scope `~/.claude/CLAUDE.md` plus `CLAUDE.md` files found from the
  project root; nested `CLAUDE.md` files in subdirectories load when the agent
  works in that directory, and closer files take precedence.
- `@path/to/file.md` lines inside CLAUDE.md import other files at load time
  (max depth 5; imports inside code spans and code blocks are ignored). Prefer
  imports over one oversized file.
- Rule files under `.claude/rules/` (user or project scope) load as additional
  persistent instructions; use them for modular topic rules.
- `/init` bootstraps a CLAUDE.md draft; treat the output as a draft that still
  needs human pruning, per the auto-generation caution in `evidence.md`.
- Product behavior changes quickly; verify scope names and limits against
  current Claude Code docs before stating them to users.

Codex:

- Codex reads AGENTS guidance once per run/session.
- It layers global and project instructions, with closer files overriding
  broader files.
- `AGENTS.override.md` takes precedence over `AGENTS.md` at the same level.
- Combined project guidance may be truncated by configured byte limits.
- After editing context files, start a new session or command to verify loading.

General:

- Markdown headings are flexible; there is no universal required schema.
- Clear commands and boundaries matter more than section names.
- Instructions are guidance, not hard security controls. Use permissions,
  hooks, linters, CI, and sandboxing for enforceable constraints.
