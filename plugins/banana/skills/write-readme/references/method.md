# README Writing Method

Use this file before creating, rewriting, or deeply reviewing a README.

## Core Standard

A good README is evidence-backed. It is not a generic marketing page and not a
dump of every internal detail. It should let a new reader understand the project
quickly, run the smallest useful path, and know where to go next.

## Fact Collection

Create a short working fact map before drafting:

| Fact | Preferred local sources |
|------|-------------------------|
| Name and package identity | README, package manifest, repository name |
| Purpose and audience | Existing docs, source entry points, examples, user notes |
| Runtime requirements | engines, pyproject, go.mod, Cargo.toml, Dockerfile, CI |
| Install commands | manifest scripts, package manager files, docs, Docker files |
| Usage commands | bin field, CLI entry, examples, tests, source entry points |
| Configuration | env examples, config schemas, docs, code defaults |
| Tests and checks | package scripts, Makefile, CI workflow files |
| License | LICENSE file, manifest license field |
| Visual assets | docs/assets, public assets, screenshots, demos |
| Support channels | issues URL, discussions, docs, existing README |

If a fact cannot be traced to a local source or user statement, do not present it
as true.

## Scope Decisions

- **Create**: start from local evidence, then choose a shape from
  `references/patterns.md`.
- **Rewrite**: preserve correct existing facts and links; replace structure only
  when the current README fails the five-second test or has stale/unsupported
  claims.
- **Improve**: edit the requested section and nearby dependencies only.
- **Audit**: produce findings and recommendations first; no rewrite unless the
  user asks.

## Drafting Sequence

1. Opening: name, one-line value proposition, and credible proof or fastest
   runnable example.
2. Value: features or use cases expressed as concrete outcomes, not vague
   adjectives.
3. Quick start: the shortest locally supported path to useful output.
4. Installation: prerequisites and alternate install methods only when they are
   real.
5. Usage: runnable examples with expected output when available.
6. Configuration: table of real options, defaults, and examples.
7. Development: setup, test, build, and release commands only when useful to
   contributors.
8. License/support: include only backed channels and files.

## Language

Match the repository's dominant documentation language. If source comments and
existing docs are mixed, follow the existing README or user preference. For
bilingual output, follow the Bilingual README section in
`references/presentation.md` for file naming, the language switcher line, and
keeping both files aligned and self-contained.

## Confirmation Gate

For new or full rewritten README files, present a preview and wait for explicit
confirmation before writing unless the user already authorized direct edits.
Small requested edits can be applied directly.

## Anti-Hallucination Rules

- Do not infer package publication from a local package name.
- Do not add npm, PyPI, crates.io, Docker Hub, download, star, coverage, or
  social badges without evidence.
- Do not create screenshots or demo links unless assets exist or the user asks
  to make them.
- Do not invent environment variables from names seen in code unless defaults or
  docs show they are user-facing.
- Do not add "Contributing welcome", support email, roadmap, benchmarks, or
  governance sections without evidence.
- Prefer a short "Not documented yet" finding in the report over confident
  filler in the README.

## Validation

When a README draft is available as a file, run:

```bash
python3 scripts/validate.py --readme README.md
```

Use the script for deterministic checks. Use `references/review-rubric.md` for
judgment calls such as value clarity, audience fit, and example usefulness.
