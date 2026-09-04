# Schema: what the project declares, and the page shapes

Read this during Init, when writing the project's schema file, and whenever a new page type is introduced. The schema is the contract everything else obeys — once it exists, it outranks this Skill.

- [What the schema must state](#what-the-schema-must-state)
- [Frontmatter](#frontmatter)
- [Page shapes](#page-shapes)
- [Index format](#index-format)
- [Log format](#log-format)

## What the schema must state

The schema is a working document for whoever opens this project next, human or agent. It fails when it is generic — a copied template that could describe any project tells the next session nothing it could not have guessed. Write it against what is actually in the tree.

It has to answer six questions:

1. **What is read-only.** Name the actual directories: the cloned repos, the vendored code, the exported material. "Raw sources are read-only" is not actionable; "`pi/`, `pi-mono/`, `prime-agent/` and `oh-my-pi/` are upstream clones — never edit, never write notes inside them" is.
2. **Where knowledge lives**, and why there rather than somewhere that would collide.
3. **What each directory means**, with the naming rule for each. A table works well: directory, type, what belongs there, **what does not**, and how files are named. The exclusion column is the one that earns its keep — most misfiling happens because a category's edge was never stated, not because its centre was unclear.
4. **What frontmatter every page carries**, and which fields are conditional on what.
5. **How the workflows run here** — what an ingest touches, what a query reads first, what lint checks and with which arguments.
6. **The project's rules** — how source references are pinned, how unverified claims are marked, what the archive convention is.

Place it in the root `AGENTS.md` when the project has none. When one already exists, put the schema in the knowledge base's own README and add a short pointer section to `AGENTS.md`; that file usually serves other purposes and belongs to the user.

Do not rewrite a schema that is in use without saying so. If a rule needs to change, change it as its own step, then file under the new rule.

## Frontmatter

Tiered, so that ordinary pages stay cheap to write while the pages that carry real risk stay checkable. Only the first tier is mandatory.

**Required on every page**

```yaml
type: research | study | decision | reference | concept | idea
```

One required field is deliberate: it is what makes the collection machine-partitionable, and anything more would tax the capture path where friction does the most damage. Adjust the vocabulary to the project — these are the types most projects converge on, not a fixed list. Whatever you choose, pass it to lint as `--types` so a typo surfaces instead of silently creating a category of one.

**Recommended on every page**

```yaml
title: Human-readable title
updated: 2026-09-01          # last write; the agent sets this
status: draft                # vocabulary depends on type — see below
tags: [pi, agent]
```

**`status` uses the vocabulary its `type` calls for**, because two genuinely different questions are being tracked and one word cannot answer both:

| For these types | Vocabulary | The question it answers |
| --- | --- | --- |
| `research`, `study`, `reference`, `concept` | `draft` → `verified` → `stale` → `superseded` → `archived` | Has this been checked against the boundary it claims? |
| `decision` | `proposed` → `accepted` → `rejected` → `superseded` | Was this actually settled on? |

Keeping them separate is what stops a thorough investigation from reading as a commitment. A `verified` research page means someone confirmed the findings against the sources — it does not mean the project is doing that. Only an `accepted` decision means that. Conflate the two into one `status: active` and a reader six months later cannot recover which is which, and will assume the more convenient one.

The corollary is worth stating in the schema: a research or design page is never a constraint, no matter how complete or well argued. Promoting a finding into a commitment is a separate act that produces a decision page.

**Conditional, by what the page carries**

```yaml
sources:                     # any page making claims from documents
  - https://example.com/spec
owner: sunss                 # pages someone is answerable for
reviewed: 2026-08-20         # last human confirmation — never set this for a human
watch:                       # pages describing specific code
  - pi/src/tools/registry.ts
stale_after: 2026-12-31      # pages whose truth has a known horizon
```

Three distinctions worth keeping straight, because conflating them is what makes freshness meaningless:

- `updated` records a write. An agent rewrite bumps it and verifies nothing.
- `reviewed` records a human confirming the content. Only a human sets it. Never write it as a side effect of editing, and never backfill it.
- `watch` records what the page describes, so staleness can be measured against the code rather than the calendar. Lint compares the last commit touching those paths against `reviewed`, falling back to `updated`.

**On OKF compatibility.** `type` as the sole required field, the reserved `index.md` and `log.md` filenames, plain relative Markdown links as the graph, and the `sources` / `status` / `stale_after` names are taken from the Open Knowledge Format so the knowledge base stays consumable by anything that speaks it. Two deliberate divergences: this uses `updated` where the current spec has moved to a nested `generated.at`, and it adds `owner`, `reviewed` and `watch`, which the spec does not define. Lint accepts `updated`, `timestamp`, and `generated.at` interchangeably, so a project that prefers strict spec alignment can use the spec's spelling without changing anything else.

## Page shapes

Shapes, not templates. Every one of these should be cut down when the page does not need a section, and none of them should be padded to look complete.

**Research** — a dated answer to a question. `YYYY-MM-DD-topic.md`.

State the question and the boundary first, so a later reader knows what was and was not asked. Then the findings, with a citation next to every consequential claim. Then the comparison if there was one, the conclusion, and what remains unverified. The date is part of the claim: this is what was true when it was asked, and it does not silently become current.

**Study** — how something actually works, read from the source. Grouped per repo.

Pin the source as `repo@rev:path:line`; upstream moves and a bare line number will point at the wrong thing within weeks. Explain the mechanism in your own words — a restatement of the code has no reason to exist. Record what differs from sibling projects, and keep open questions as open questions. Set `watch` to the paths the page describes.

**Decision** — why a choice was made. `NNNN-title.md`, numbers never reused.

Context and constraints, the alternatives that were genuinely considered with what was wrong with each, what was chosen and what drove it, and the consequences including the bad ones. A decision earns a record when it is hard to reverse, a future reader would ask why, and real alternatives existed. Missing any of the three, it is a log line.

Two things make a decision page trustworthy later. State **what this decision does not settle** — the adjacent questions a reader will assume it covered and it did not. And keep corrections as amendments appended to the page rather than edits to the original text, so what was claimed at the time stays recoverable. Superseded decisions stay, marked, linked forward.

**Concept** — one shared mechanism, explained once, for the many components that apply it.

This is the page that prevents N near-identical component pages. Give it an intention-revealing name, describe the mechanism from the source, and let every component reference it instead of restating it. See [scale.md](scale.md#many-similar-things).

**Reference** — a living page that must stay correct: a mechanism, a glossary, a set of conventions.

Every fact traceable to a source or a code location. This is the type that most needs `owner` and `reviewed`, because it is the type readers will trust without checking.

**Capture** — a link and a sentence. No structure, no ceremony, no frontmatter beyond `type`.

The point is zero friction. Reviewed periodically: promote what has earned a page, delete the rest.

## Index format

The always-read entry point, held to a budget it can survive — roughly 200 lines or 25KB, past which entries stop being reliably read. Entries are routing lines: the name plus the words someone would actually search for, not a compressed conclusion.

```markdown
# Index

> Conventions: see AGENTS.md. Updated with every change.

## Research
- [2026-08-26-knowledge-base-methods.md](research/2026-08-26-knowledge-base-methods.md) — LLM Wiki, OKF, C4, ADR, PARA, Zettelkasten compared; 29 primary sources

## Study
- [study/prime-agent/](study/prime-agent/index.md) — RLM recursive kernel, daemon supervisor, ACP server
```

Once an area outgrows a section, give it its own index and let the root route to that instead. The root index then describes areas, not pages, and stays short and stable.

## Log format

Append-only. One entry per change, uniform prefix so `grep "^## \["` works.

```markdown
# Log

## [2026-09-01] ingest | Prime Agent vs Pi architecture comparison
- Added `research/2026-08-31-prime-agent-vs-pi.md`
- Resolved the open question in `study/pi/tool-registry.md`: the discrete tool set is replaced by a single ipython control plane
- Cross-linked from `research/2026-07-14-agent-tool-protocols.md`
- Continual Harness scoring still unverified
```

Record what moved and why, including what was reconciled elsewhere — that is the part nobody can reconstruct later. Never edit past entries.
