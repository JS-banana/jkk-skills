# Methods: choosing the layers

Read this during Init, or when a knowledge base has outgrown the shape it was given. It answers one question — *which layers does this particular project justify* — and records what was already considered and rejected, so the same selection is not re-argued from scratch every time.

- [The skeleton](#the-skeleton)
- [Signals to layers](#signals-to-layers)
- [What gets rejected, and why](#what-gets-rejected-and-why)
- [Worked shapes](#worked-shapes)
- [Primary sources](#primary-sources)

## The skeleton

Every knowledge base gets the same core, because every one of these earns its place immediately:

- **An index** — the always-read entry point. Routing lines, not summaries.
- **A log** — append-only, dated, one entry per change. It is the cheapest possible answer to "what happened here and when."
- **A capture area** — somewhere to put a link or a half-thought with zero ceremony. Without it, everything either becomes a premature page or is lost.
- **The note types this project will actually produce** — created when the first page needs one.

Everything below the skeleton is optional and gets added only against a signal the project actually shows.

## Signals to layers

Read the project, then add the layer each observed signal justifies. Do not add a layer against a signal you have not seen; an unused directory is a standing invitation to file things in the wrong place.

| Signal | Add | Why this layer, specifically |
| --- | --- | --- |
| Options will be compared and one chosen | A decisions area, ADR-shaped: context, alternatives, outcome, consequences | The reasoning is what future readers need, and it is the first thing lost. Record only decisions that are hard to reverse, would surprise a future reader, and had real alternatives |
| Cloned upstream repos being read rather than written | Study notes, one subtree per repo, an entry-point page each | Keeps four codebases from blurring, and makes "which repo was that in" answerable. Source references pin `repo@rev` because upstream keeps moving |
| Investigation of products, competitors, or approaches | Dated research pages | These are answers as of a date, not living documents. The date is part of the claim |
| Facts that must stay correct over time | Reference pages, each with an owner and a review date | A page nobody owns goes stale and nobody notices. Ownership is what makes a freshness date actionable rather than decorative |
| Several systems or repos that interact | An architecture layer, at system-context and container level only | Two levels is where the value is; deeper levels cost more to maintain than they return and are better generated than written |
| Many near-identical components — plugins, providers, adapters, services | One named concept page for the shared mechanism, one table of all instances, individual pages only for the exceptions | See [scale.md](scale.md#many-similar-things). Writing N near-identical pages is the documented failure mode here, not the solution |
| Content accumulating past a scannable index | Per-directory indexes, with the root index routing to them and nothing more | See [scale.md](scale.md#keeping-the-index-loadable) |
| Conclusions that expire | Lifecycle status, plus watched source paths where a page describes specific code | A note about a module goes stale when the module changes, not when a calendar interval passes |
| Work spanning sessions with a handoff cost | A separate session-state file, excluded from the index and from freshness accounting | This is task state, not knowledge. Mixing the two corrupts both — durable pages get churn, and handoff notes get treated as established fact |
| Output aimed at readers outside the project | Nothing. Leave the knowledge base alone | Reader-facing documentation is a separate artifact with a separate structure. Reorganizing research notes around a documentation taxonomy damages them for research |

## What gets rejected, and why

These were evaluated and are not part of the default. Reintroduce one only with a specific reason, not by drift.

**Organizing methods**

- **Zettelkasten** — the strongest long-term compounding of any method, but its cost centre is atomizing and relinking notes by hand, which is precisely the labor an agent now absorbs. What remains is a high-discipline personal practice whose payoff arrives after a long unproductive stretch. Borrow the principle that connections carry the value; do not adopt the ceremony.
- **PARA** — four buckets by actionability is too coarse to be the primary structure; a research topic lands in Resources and still needs an internal shape. Keep only its lifecycle idea: things flow toward archived rather than being deleted.
- **Johnny Decimal** — stable numeric addresses solve retrieval in a filing cabinet. They express nothing about how ideas relate, which is the part that matters here.
- **Digital garden** — optimized for publishing work-in-progress to an audience. Internal research and company platform knowledge have no audience, so the tradeoff it makes buys nothing.
- **Diátaxis** — a typology for reader-facing documentation, not a way to organize investigation. Genuinely useful downstream, when research becomes documentation someone else reads. Applying it upstream forces notes into shapes that fight their purpose.
- **GitHub wiki and gists** — no directory structure, no review flow, not local-first. A gist is a fine way to publish one document and a poor way to hold a knowledge base.

**Agent-memory patterns**

- **A fixed file set as the whole structure** — the memory-bank family fixes five or six files up front. That is a reasonable bootstrap and cannot express twelve similar plugins or a hundred investigated sources. One vendor has already deprecated its own implementation in favor of per-directory instruction files plus on-demand loading. Keep at most a project brief and a session-state file; everything else belongs to a budgeted index over topic pages.
- **Reading every page at the start of every task** — the memory-bank read protocol. It does not survive a knowledge base larger than a handful of files, and it works against a documented effect: recall degrades as the context fills, so loading everything makes the answer worse as well as more expensive. Load the index; read pages on decision.
- **Unbounded append-only files as the main store** — fine for a log or session state, wrong for knowledge, because nothing in the pattern ever compacts them. Any append-only file needs a stated trigger for review and compaction.
- **A database, vector store, or graph index as a dependency** — the knowledge base must stay fully usable with a text editor, git, and grep. These are legitimate accelerants layered on top of the same Markdown, and unacceptable as the substrate: they break human editability, versioning alongside the code, and portability between tools.
- **Semantic retrieval as the default access path** — any retrieval method produces both false positives and false negatives, while an explicit name-based reference does neither. Reserve it as an escalation for the specific case where it wins: hundreds of sources whose vocabulary you do not yet know.
- **Splitting a file into imports to save context** — imported files load with their parent, so this improves organization and saves nothing. Splitting only helps when the parts load lazily.
- **Generated architecture prose** — anything derivable from the tree should be produced on demand, never written into a page that will rot silently while still reading as authoritative.
- **The blogged `CONTEXT.md` / `MEMORY.md` / `SKILLS.md` hierarchy** — no vendor documents it. The one real artifact with a similar name has different semantics. Do not build on it.

## Worked shapes

Illustrations of the selection above, not templates to copy. A project that resembles one of these still gets read on its own terms.

**A workspace of cloned repos being studied.** Raw sources are the clones. The knowledge base sits at the workspace root, outside all of them. Study notes per repo with an entry-point page each; research pages for the cross-repo comparisons that are the actual reason for reading four codebases at once; decisions where the study feeds a build choice. Source references pin the revision.

**A company platform with many repos and many plugins.** The knowledge base goes in its own directory that no repo owns. The platform's shared mechanism — the plugin lifecycle contract, the host capabilities — is written once as a concept page from the source, and every plugin references it. A table lists all plugins with a one-line differentiator; individual plugin pages exist only for the ones that are genuinely surprising. An architecture layer at container level covers how the frontends, backends, and registry fit together. Decisions cover both platform-level and plugin-level choices. Per-directory indexes from the start, because this shape outgrows a flat index immediately.

**A product being investigated before it is built.** Mostly research pages and a capture area, since the work is ideas, competitors, and feasibility. Decisions appear when the selection questions resolve. Little structure up front: this is the shape most damaged by premature directories.

**Personal accumulation with no fixed scope.** Skeleton only. Let the types appear as the content does.

## Primary sources

- Karpathy, LLM Wiki gist — <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Karpathy, The append-and-review note — <https://karpathy.bearblog.dev/the-append-and-review-note/>
- Open Knowledge Format specification — <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>
- OKF announcement — <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/>
- arc42 crosscutting concepts, tips 5-10, 5-28 and 8-11 — <https://docs.arc42.org/tips/5-10/>, <https://docs.arc42.org/section-8/>
- arc42 building block view, relevance over completeness — <https://docs.arc42.org/section-5/>
- C4 model, and its FAQ on scaling past a handful of boxes — <https://c4model.com>, <https://c4model.com/faq>
- Nygard, Documenting Architecture Decisions — <https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>; MADR — <https://adr.github.io/madr/>
- Anthropic, Effective context engineering for AI agents — <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- Claude Code memory, including the index load budget — <https://docs.claude.com/en/docs/claude-code/memory>
- Claude Code, working with large codebases — <https://code.claude.com/docs/en/large-codebases>
- Agent Skills best practices, on progressive disclosure — <https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices>
- Serena memories, on preferring references to search — <https://oraios.github.io/serena/02-usage/045_memories.html>
- Cline Memory Bank — <https://docs.cline.bot/prompting/cline-memory-bank>
- Kilo Code, deprecating its memory bank for AGENTS.md — <https://kilocode.ai/docs/advanced-usage/memory-bank>
- basic-memory knowledge format and schemas — <https://docs.basicmemory.com/concepts/knowledge-format/>
- Backstage software catalog system model — <https://backstage.io/docs/features/software-catalog/system-model>
- Software Engineering at Google, ch. 10, on freshness dates and ownership — <https://abseil.io/resources/swe-book/html/ch10.html>
- Aider repo map — <https://aider.chat/docs/repomap.html>
- Diátaxis — <https://diataxis.fr>; PARA — <https://fortelabs.com/blog/para/>; Zettelkasten — <https://zettelkasten.de/introduction/>
