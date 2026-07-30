---
name: write-agent-context
description: >
  Create, audit, and maintain agent context files such as AGENTS.md, CLAUDE.md,
  GEMINI.md, Cursor rules, Copilot instructions, and repo-level AI coding
  guidance. Use when the user asks to create, optimize, review, consolidate,
  split, or update persistent instructions for Codex, Claude Code, Cursor,
  GitHub Copilot, or other coding agents; when AGENTS.md/CLAUDE.md is too long,
  stale, vague, or causing repeated agent mistakes. Trigger on "帮我写
  CLAUDE.md", "优化 AGENTS.md", "上下文文件怎么写", "给仓库加 agent 规则", or
  /write-agent-context. Not for human-facing README or project docs — use
  write-readme for those.
---

# Write Agent Context

Create high-signal persistent context for coding agents.

The reader is a machine, not a person. Every line is re-read and paid for in
tokens on every session, so optimize for density of non-inferable facts: exact
commands, unusual decisions, boundaries, and verification gates the agent
cannot cheaply discover. Polish, marketing tone, and completeness for its own
sake are liabilities here — that is README territory (write-readme).
Apply the deletion test to every line: if removing it would not change agent
behavior, remove it.

## Load Rules

- For create, rewrite, consolidation, or deep review tasks, read
  `references/method.md` and `references/review-rubric.md` before drafting.
- For evidence-backed claims or research rationale, read
  `references/evidence.md`; do not rely on external websites unless the user
  asks to refresh sources.
- For examples, read `references/examples.md` only after choosing the target
  shape.
- For tiny edits under 10 lines, use this file only unless the task involves
  research claims or structural changes.

## Operating Principles

1. Treat existing project docs, package scripts, test config, CI files, and
   current AGENTS.md/CLAUDE.md files as source of truth.
2. Write durable operating instructions, not human-facing project docs.
3. Prefer pointers to canonical docs and scripts over copied summaries.
4. Keep root context short; use nested files when scope differs by directory.
5. Ask when policy or permission boundaries are ambiguous.
6. Remove stale, redundant, vague, and unenforceable rules.

## Workflow

### Create New Context

1. Inspect root docs, manifests, CI, test config, and existing agent files.
2. Identify non-inferable facts: custom commands, unusual toolchain choices,
   counterintuitive patterns, dangerous operations, and verification gates.
3. Draft a concise root file using the method reference; add nested files only
   when directory scope changes.
4. Cite the local files that informed commands and boundaries.
5. Run the review rubric and revise until no critical issue remains.

### Review Existing Context

1. Read the context file and local source files needed to verify its claims.
2. Score with `references/review-rubric.md`.
3. Separate findings into incorrect or stale, vague, redundant, overbroad, and
   missing high-value guidance.
4. Propose surgical edits; avoid full rewrites unless the file is structurally
   broken.
5. Apply edits only when requested or clearly implied by the task.

### Consolidate Multi-Tool Instructions

1. Pick one canonical source, usually `AGENTS.md` for cross-tool repositories.
2. Preserve separate tool files only for real syntax, scope, or product
   differences.
3. Prefer symlinks or short adapter files over parallel copies.
4. Document precedence and restart requirements for the target tool.

### Update After Repeated Agent Mistakes

1. Capture the exact mistake and why existing context failed.
2. Add the narrowest durable rule that would have prevented it.
3. Pair negative rules with the correct command, file pointer, or alternative.
4. Remove obsolete adjacent rules if the new rule supersedes them.

## Default Sections

Use only sections that have real content:

- Stack: exact versions and non-standard tools.
- Commands: install, dev, build, test, lint, typecheck, and single-test variants.
- Non-Obvious Patterns: counterintuitive project rules and their mechanism.
- Boundaries: Always / Ask First / Never.
- Testing and Verification: concrete commands and completion gates.
- Reference Map: links to deeper docs with when to read each.

## Anti-Patterns

- Auto-generated context committed without human pruning.
- Directory listings the agent can discover.
- Generic principles such as "be careful" or "follow best practices".
- Style rules already enforced by formatter or linter.
- Big architecture essays in root context.
- Unverified commands or tool versions.
- Negative-only rules without the correct alternative.
- Parallel CLAUDE.md, Cursor, and Copilot instruction copies that drift.

## Output

When drafting or reviewing, provide:

1. Proposed content or patch.
2. Short rationale tied to local evidence.
3. Review-rubric result.
4. Assumptions, open questions, and any commands not verified.
