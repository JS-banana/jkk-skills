# Scale: growing without collapsing

Read this when a project has many similar components, when the index has stopped being scannable, or during any lint. A knowledge base rarely fails by being wrong. It fails by becoming unnavigable, by repeating itself across dozens of pages, and by continuing to read as authoritative after it stopped being true.

- [Keeping the index loadable](#keeping-the-index-loadable)
- [Splitting when one index is not enough](#splitting-when-one-index-is-not-enough)
- [Many similar things](#many-similar-things)
- [Knowing when a page has gone stale](#knowing-when-a-page-has-gone-stale)
- [Retiring pages](#retiring-pages)
- [When to reach for a search tool](#when-to-reach-for-a-search-tool)

## Keeping the index loadable

The index is read every single time the knowledge base is opened, which makes it the one file with a hard budget. Past roughly 200 lines or 25KB it stops being reliably read in full, and entries below the cut are effectively invisible — the worst failure mode available, because the page exists, the index lists it, and nobody finds it.

Three rules keep it inside the budget:

**One line per entry.** Detail belongs in the page, not the index.

**Entries are routing lines, not summaries.** The job of an entry is to let a reader decide whether to open the page, so it should carry the words someone would actually search for — the entity names, the mechanism, the competing option — rather than a compressed restatement of the conclusion. `Plugin lifecycle — register/mount/onSchemaChange/unmount, host API surface, permission model` routes. `Notes about how plugins work` does not.

**Compact in the same pass that overflows it.** After writing the index, check its size. If it is near the budget, merge related entries, shorten routing lines, and drop entries for pages that have been archived. If it is over, the fix is not a smaller font — it is splitting, below.

Every page must be reachable in one hop from an index. References nested deeper get skimmed rather than read, which produces confidently incomplete answers. If reaching a page takes two hops, the intermediate node should be an index of its own.

## Splitting when one index is not enough

Escalate one rung at a time, and only when the current rung shows its specific symptom. Each rung costs something, so do not pre-emptively adopt the end state.

| Symptom | Move to | What it costs |
| --- | --- | --- |
| Index within budget, entries still findable | One flat index. Stay here | Nothing — this is the right answer for most projects |
| Index over budget, or a section is no longer scannable | Per-directory indexes: each area gets its own index, and the root index routes only to those | The root index stops describing content and starts describing areas, so a reader takes one extra hop |
| Areas drift apart, conventions diverge, nobody owns the root | Give each area an owner and a review date; keep cross-cutting conventions at the root only | Requires a human per area, which a personal knowledge base may not have |
| Navigation by name starts failing — you know something is there but not what it is called | A search tool over the same Markdown | See [below](#when-to-reach-for-a-search-tool) |

Per-directory indexes are the workhorse rung and worth reaching for early in a multi-repo or many-component project, because the split is obvious there: knowledge sits next to the thing it describes, and the root carries only what spans areas. The root index in that arrangement is short and stable, which is exactly what an always-loaded file should be.

Give each directory index a one-line statement of what the area covers at the top. It costs nothing and it makes a grep hit interpretable — a reader who lands mid-tree can tell where they are.

## Many similar things

Dozens of plugins on one runtime, a family of providers behind one interface, twenty services built from the same template. Writing one page per instance produces dozens of near-identical pages, which is expensive to write, worse to maintain, and actively misleading: the reader cannot tell which differences are real and which are just different wording of the same thing.

The documented factoring, and the right one, has three parts:

**One concept page per shared mechanism.** Whatever every instance does the same way — the lifecycle contract, the capabilities the host grants, the registration and dispatch path, the permission model — is written once, from the source, with an intention-revealing name. This page is the only place that mechanism is explained.

**One table of all instances.** Name, what it is responsible for, where its code lives, and which concepts it applies. A row per instance, in the area's index or a page next to it. This is the complete inventory, and for most instances it is the *entire* documentation, which is the point.

**Individual pages only for instances that earn one.** An instance gets a page when it is surprising, risky, complex, or volatile — when someone reading the concept page plus the table would still get it wrong. The ordinary, boring, standardized instances stay as rows. Prefer relevance over completeness here; completeness is what makes the collection unreadable.

A page written under this factoring contains only what differs. It never restates the shared mechanism; it links to the concept page. When you find yourself explaining the lifecycle again inside a plugin page, that content belongs in the concept page and the plugin page should be quoting the exception.

Two supporting moves:

**Declare the shape once.** When instances do get pages, state the fields every one carries — responsibility, entry point, what it diverges from, known pitfalls — so the set stays comparable and gaps are visible. Deriving that shape from the pages that already exist is usually better than designing it up front: whatever most existing pages carry is what the shape actually is.

**Mark instances with the concepts they apply.** An instance can apply several. The mark is what makes "which plugins touch permissions" answerable by grep instead of by reading everything.

## Knowing when a page has gone stale

Staleness is not incorrectness. A stale page may still be right; it just has not been confirmed lately, and the knowledge base cannot tell the difference without help.

Three distinct dates, which are routinely conflated and should not be:

- **Updated** — when the page was last written. An agent rewrite bumps this and verifies nothing.
- **Reviewed** — when a human last confirmed it. Only a human sets this; never fabricate it, and never set it as a side effect of an edit.
- **Watched paths** — the source files the page describes. This is the sharpest signal available for notes about code, because a page about a module goes stale when the module changes, not when a calendar interval elapses. Record the paths in the page's frontmatter and let lint compare their last commit against the review date.

Pages whose truth has a known horizon — a version comparison, a pricing claim, an "as of" survey — should carry an explicit expiry rather than relying on anyone noticing.

Large or sensitive evidence does not belong in the knowledge base at all. Benchmark output, logs, session dumps, exported datasets, and anything with credentials in it should live outside it under a stable identity, with the page carrying only that identity and a bounded excerpt. A hash identifies bytes only while those bytes are still retrievable, so record where they are, not just what they hashed to.

The strongest defense against staleness is upstream of all of this: do not write what can be derived. A page that inventories a directory or lists dependencies is stale the moment the code moves and will keep reading as authoritative. Keep the rationale, the pitfall, the trade-off, and the non-obvious mechanism; those age slowly, and when they do age it is meaningful.

## Retiring pages

Archive rather than delete: move to an archive location or mark the status, remove the inbound links so nothing routes to a dead conclusion, and drop the index entry. The file stays in git and stays readable by path. What must not survive is its appearance of currency.

Superseded pages are a special case worth handling well. Keep the page, mark it, and link it forward to what replaced it. The reasoning that turned out wrong is often more instructive than the conclusion that replaced it, and a reader who finds the old page through a stale link needs to be told where to go.

Pages that are never read are the quiet cost. During a lint, look for pages nothing links to, pages that no longer appear in any index, and subjects that were investigated once and never referenced again. Some should be merged into a page that is read; some should be archived. Carrying them costs index budget and dilutes search.

## When to reach for a search tool

Names and indexes are deterministic: an explicit reference finds exactly what it names, with no false positives and no misses. Grep extends that to anything the index does not carry, and between them they handle the overwhelming majority of retrieval.

Reach past them only for the case they genuinely lose: a large body of research where you do not yet know the vocabulary, and so cannot name the thing you are looking for or grep for it. That is where semantic search earns its cost — and it is a layer over the same Markdown, never a replacement for it. The knowledge base must remain fully usable with an editor, git, and grep, because that is what makes it portable across tools and readable in five years.

Note also that these numbers and thresholds are asserted by the tools that publish them rather than independently measured. Treat them as reasonable defaults with a known origin, not as findings; if a project's index stays readable past the budget, that is information about the project.
