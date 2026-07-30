---
name: write-readme
description: >
  Use when the user wants to create, rewrite, audit, or improve a project
  README.md, GitHub README, project documentation landing page, or a
  bilingual README. Trigger on README requests, "帮我写 README",
  "生成项目文档", "README 太烂了", "把 README 弄好看点", "write project
  docs", or /write-readme. Not for agent context files such as
  AGENTS.md or CLAUDE.md — use write-agent-context for those.
---

# Write README

Create README files that are grounded in local project evidence.

The reader is a person who gives the page a few seconds before deciding to
stay or leave. Treat the README as the project's front door: it must explain
what the project is, how to try it, and what claims the repository actually
supports — and it must look deliberate, because visual hierarchy is how humans
scan. This is the opposite optimization from agent context files
(write-agent-context): those minimize tokens for a machine; a README spends
words and layout to earn a human's trust.

## Load Rules

- For create, rewrite, or deep review tasks, read `references/method.md` and
  `references/review-rubric.md` before drafting.
- After scanning the repository, read `references/patterns.md` to choose the
  README shape guidance and section priorities.
- Read `references/presentation.md` when creating or rewriting a README, or
  when the task involves layout, visual polish, badges, media, or bilingual
  docs.
- Read `references/badges.md` only when adding or reviewing badges.
- Read `references/examples.md` only after choosing the target shape.
- For tiny edits under 10 lines, use this file and the existing README only
  unless the edit affects structure, facts, badges, or generated examples.

## Source Of Truth

Before writing new content, inspect the existing README, manifests
(`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.), scripts, CI
files, docs, license files, assets, and source entry points.

Only document facts found locally or explicitly stated by the user. Do not
invent install methods, commands, badges, publish status, screenshots, support
channels, metrics, roadmap, or configuration options. If a fact is unknown,
omit it, mark it as not documented in the review report, or ask.

## Workflow

1. Clarify scope if needed: create, rewrite, audit, small edit, language, and
   whether writing the file is already authorized.
2. Build a fact map: project name, purpose, audience, install path, usage path,
   configuration, tests, license, visuals, and release/distribution status.
3. Choose section priorities with `references/patterns.md`; compose the README
   from project evidence instead of filling a fixed template.
4. Draft from evidence: five-second value proposition, quick start, runnable
   usage, configuration if real, and only sections that have local backing.
5. Review with `references/review-rubric.md`. When a README file or draft path
   exists, run `python3 scripts/validate.py --readme <path>` if possible.
6. Present preview, score, assumptions, and unsupported/missing facts. Wait for
   user confirmation before writing a new or fully rewritten README unless the
   user explicitly asked for direct edits.

## Output Modes

- **Create/rewrite**: README preview, score report, assumptions, and write gate.
- **Audit/review**: findings first with file/line references, score, and focused
  recommendations; do not rewrite unless requested.
- **Direct edit**: apply the smallest patch that satisfies the request, then
  report changed sections and validation results.

## README Rules

- The first screen must answer: project name, what it does, who it helps, and
  the fastest credible way to try it.
- Installation and usage commands must be copy-pasteable and traceable to local
  files or user-provided facts.
- Badges require evidence; prefer no badge over a fabricated badge.
- Use screenshots, demos, or generated assets only when the files exist or the
  user asks to create them.
- Match the repository's existing language. Generate bilingual READMEs only when
  requested or when bilingual docs already exist.
- Preserve accurate existing content when improving a README. Rewrite only when
  the structure is broken or the user asks for a rewrite.

## Completion Checklist

- [ ] No placeholders, sample owner/repo names, or copied example project facts.
- [ ] Every command, badge, link, image, API, and config option has evidence.
- [ ] Relative links and images resolve, or unresolved items are reported.
- [ ] README shape matches project type and audience.
- [ ] Review rubric result and validation output are included in the response.
