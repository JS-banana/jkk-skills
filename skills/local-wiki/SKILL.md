---
name: local-wiki
description: >-
  Build and maintain a local, git-versioned Markdown wiki / knowledge base that an agent maintains and a human curates: initialize a structure fitted to the project at hand, file research, source-code study and selection decisions into it, answer questions from it, and keep it healthy as it grows. Use when the user wants a 知识库 or local wiki / knowledge base set up in a project or workspace, asks to 归档 / 落地 / ingest a finished investigation, wants accumulated research organized across multiple repos or many similar components, or asks for an existing wiki / knowledge base to be checked for drift. Do not use for a project's own user-facing documentation or README, for agent instruction files such as AGENTS.md on their own, or for a published documentation site.
license: MIT
---

# Local Wiki

Turn scattered investigation into a knowledge base an agent can maintain and a human can audit. The reading and the thinking were never the problem; the bookkeeping is. Cross-references go unupdated, conclusions get superseded in one page and left standing in three others, and the index stops matching the directory. An agent does not get bored by that work, which is why it can own it — and why the human's job shifts to curating sources and reviewing judgment rather than filing.

Follow the user's language for the knowledge base contents and for conversation. Keep identifiers precise regardless of language: paths, commit revisions, type names, field names, and URLs.

## Defer to the project's own schema first

Before anything else, look for a knowledge base that already exists: `index.md` and `log.md` together, a `knowledge/` or `docs/` tree of interlinked notes with YAML frontmatter, a `.serena/memories/` or `memory-bank/` directory, or a section in `AGENTS.md` / `CLAUDE.md` describing where notes go.

If one exists, **its conventions outrank everything in this Skill.** Read its schema and follow it, including naming, frontmatter fields, and directory meanings, even where they differ from what this Skill would have generated. This Skill builds and evolves a schema; it does not re-litigate one that is already in use. Propose a schema change only when a real conflict surfaces, and change the schema in its own step before filing anything under the new rule.

**A schema change applies forward only.** Do not bulk-rewrite existing pages to conform, and do not silently reclassify them. Pages written under the old rules stay as they are and stay in the index; appearing in the index means they are findable, not that they meet the current contract. Migrate deliberately, in scoped passes, when a page is being worked on anyway. A sweep that reformats two hundred pages to match a new convention destroys far more than the inconsistency cost — it rewrites what earlier pages actually claimed, and buries the real edits in an unreviewable diff.

If none exists, initialize one.

## Choose the mode

- **Init** — no knowledge base yet, or the user asks to set one up.
- **Ingest** — finished material needs to land: a research report, source-code findings, a decision, a link worth keeping.
- **Query** — a question that the knowledge base should be able to answer.
- **Lint** — a health check, on request or when ingesting reveals broad drift.

Ingest is by far the most frequent. Do not narrate the mode; just work in it.

## Invariants

These hold in every mode, and they are what separate a knowledge base from a folder of files.

- **Raw sources are read-only.** Cloned upstream repos, clipped articles, exported transcripts, and any code the user did not write in this workspace are inputs. Never edit them, never write notes inside them.
- **A change is one transaction.** A page never lands without its links, its index entry, and its log line in the same pass. A half-filed page is worse than an unfiled one, because it looks filed.
- **Write only what cannot be derived.** Directory layouts, dependency lists, file inventories, and API signatures are cheaper to read from the source than to maintain in prose, and they rot silently. Keep the rationale, the pitfalls, the non-obvious mechanism, the trade-off that was actually made, and the conventions that differ from the defaults.
- **Archive, never delete.** Move to an archive location or mark the status; strip inbound links so nothing points at a dead conclusion. Git holds the history, but a superseded page that still reads as current is an active hazard.
- **Provenance travels with the claim.** Findings from documents carry the URL; findings from code carry `repo@rev:path:line`, because upstream moves and bare line numbers drift. What was not verified stays explicitly marked as not verified, in the page, not just in the conversation.
- **Completeness is not adoption.** A thorough investigation is a finding, however well argued. Only a decision page marked accepted records what was actually settled on. This is the distinction a knowledge base loses first: months later, a comprehensive comparison reads as a choice that was made, and nobody can tell whether it was. Keep the two on separate vocabularies — see [references/schema.md](references/schema.md#frontmatter).

## Init: fit the structure to the project

Read the project before proposing anything. What determines the structure is: whether this is one repository or a workspace of several; whether the code is the user's or cloned for study; whether a `docs/` tree already exists and who owns it; whether there are many near-identical components; whether decisions with real trade-offs are coming; and whether this is personal or shared.

Ask at most one short round of questions, and only about forks that would change the structure. Infer the rest — the tree usually answers more than the user will.

**Place it where it cannot collide.** In a multi-repo workspace, the knowledge base belongs at the workspace root, outside every repo. In a single repository that already has its own `docs/`, use a separate directory such as `knowledge/` so the project's documentation and the research notes never fight over the same files. In a single repository with no docs of its own, follow whatever the project already does.

Watch for a third case that is easy to get wrong: a repository the user actively develops and which governs its own documentation, with its own categories, states, and rules. It is not a read-only raw source, and it is also not somewhere to file personal research. Two schemas coexist in that workspace and neither should be written into by the other. Note the boundary in the schema explicitly, because an agent that only checks "is this repo read-only" will get it wrong.

**Choose the layers from the signals**, not from a preset. [references/methods.md](references/methods.md) maps observed signals to the layer each one justifies, and records which methods were considered and rejected so the choice is not re-argued every time. The skeleton is always the same: an index, a log, a capture area, and the note types this project will actually produce.

**Write the project's own schema**, specific enough to be operable: name the actual repositories that are read-only, the actual directories and what belongs in each, the naming rules, the frontmatter fields, and what the ingest and lint workflows do here. A generic template copied in unchanged is the main way this step fails. [references/schema.md](references/schema.md) covers what the schema must state and gives the page templates.

Put the schema in the root `AGENTS.md` when there is none; when one exists, put it in the knowledge base's own README and add a short pointer section to `AGENTS.md` rather than rewriting a file the user maintains for other purposes.

**Create only what has content.** An empty directory is a promise the project has not made yet. `index.md` and `log.md` from the start; everything else when the first page needs it.

Close by writing the init entry in the log, confirming with the user before running `git init` or adding to an existing repo, and telling them in a few sentences how to put things in from now on.

## Ingest: place, reconcile, record

Read the schema first. Then, in order:

**Search before writing.** Find what the knowledge base already says about this — check the index, then grep for the entities, mechanisms, and terms involved. Skipping this is how a knowledge base ends up with five pages that half-cover the same ground and disagree at the edges.

**Then choose what to do**, which is usually not "create a page":

- **Extend** an existing page when the material sharpens, corrects, or completes what is already there. This is the default for anything that belongs to a subject the knowledge base already covers. When extending *corrects* something, do not quietly overwrite the old wording — say what changed and why, so a reader who acted on the earlier version can tell that it moved. Silent correction is how a page becomes untrustworthy without ever becoming wrong.
- **Create a page** when the material answers a genuinely different question, or when it is a dated one-time investigation that should stay readable as of its date.
- **Supersede** when the material contradicts a recorded conclusion. Keep the old page, mark it superseded, and link it forward to the replacement. The reasoning that turned out wrong is worth more than a clean history.
- **Capture a line, or nothing at all**, when the material does not clear the write threshold.

**The write threshold.** A page earns its place when it is surprising, hard-won, decision-bearing, or volatile. Ordinary, derivable, or standardized material does not get a page no matter how true it is — it inflates the index and dilutes what is worth reading. A decision specifically earns a record when it is hard to reverse, when a future reader would ask why it was made this way, and when real alternatives were considered; missing any of the three, it is a line in a log, not a page.

**Reconcile.** This is the step that makes a wiki out of a directory, and the step most likely to be skipped. New material almost never touches only one page. Before finishing, find:

- open questions elsewhere that this answers — search for the project's unverified marker and resolve the ones this closes, rather than leaving a stale question next to a page that answers it;
- recorded conclusions this changes, weakens, or confirms;
- pages that should link here, and pages this should link to.

Make those edits in the same pass. An ingest that adds a page and updates nothing else has filed a report, not integrated knowledge.

**Record.** Add the index entry as a routing line — the name plus the words someone would actually search for, not a summary — and append the log entry in the project's exact format. Then re-read the index: if it has outgrown its budget, compact it in the same pass rather than letting it silently stop being read.

## Query: navigate by name, read on decision

Read the index and navigate by page name. Names and one-line routing entries are what make retrieval deterministic, so they have to be self-disambiguating; when they are not, that is a lint finding, not a reason to read everything.

Grep for terms the index does not carry. Read pages when a decision requires them, not preemptively — reading the whole knowledge base to answer one question degrades the answer as much as it costs.

Answer with the pages cited, and distinguish what the knowledge base establishes from what it merely suggests. If the answer took real work and is not in the knowledge base, that is an ingest: file it before it disappears into the conversation.

## Lint: mechanical first, judgment second

Run `scripts/wiki_lint.py <wiki-dir>` for everything a machine can settle: dead links, orphan pages, pages on disk that no index reaches, missing or malformed frontmatter, an index over its load budget, pages whose watched source paths have changed since review, expired pages, and superseded pages with no forward link. Pass `--types` from the project schema and `--project-root` when pages watch code. It reports; it does not edit.

Then do what the script cannot: find pages that contradict each other, coverage that has become redundant, pages filed under the wrong type, subjects the project clearly needs and does not have, and pages whose conclusions have quietly been overtaken.

Report grouped findings with the highest-consequence ones first and get agreement before a broad rewrite. On a large knowledge base a full pass will surface far more than is worth acting on at once; fixing everything silently is its own kind of damage.

## Grow without collapsing

Read [references/scale.md](references/scale.md) when the project has many similar components, when the index stops being scannable, or during any lint. It covers keeping the index within a budget it can survive, splitting into per-directory indexes, describing dozens of near-identical things without dozens of near-identical pages, and deciding when a note is stale.

## Work with other skills

`deep-learn` and `deep-analysis` produce a finished pack and explicitly defer to the host project for where it goes — the project schema is that destination contract, so hand them the schema's location and naming rule up front, then ingest the returned pack through the flow above rather than dropping the file in. `agent-reach` and web research produce raw material, which belongs in the capture area until it is worth a page.

Ingest is where the value is realized. A finished investigation that never lands is one that has to be redone.

## Boundaries

This builds the project's internal knowledge base. It is not the project's user-facing documentation or README, which is `write-readme`; not agent instruction files as such, which is `write-agent-context`, though the schema may live inside one; and not a published documentation site, which needs its own information architecture downstream. It does not modify raw sources, and it does not silently rewrite a schema the user already relies on.
