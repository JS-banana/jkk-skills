# The project-learning reader

The Skill owns `scripts/render.py` and `assets/reader.*`. One study JSON generates
both the offline HTML reader and complete Markdown export. Research determines
facts and learning order; the renderer determines reusable presentation.

## Build a reading path

Start with what someone can do with the project and one useful mental model.
Keep the overview summary short enough to leave room for the system map; defer
ports, flags and function names until they answer a question. Do not duplicate
that summary in a longer introduction. Introduce unfamiliar concepts before
using them, in the reader's language.

Use short navigation labels that describe the reader's question. Explanations
remain continuous within a chapter; the chapter outline scrolls to steps without
hiding their neighbors. Put constraints and trade-offs near the relevant behavior.
Source details expand beside the explanation instead of replacing it.

A system map answers where responsibilities live and how they connect. Use
explicit groups for real runtime or ownership boundaries; put protocols on the
relationships when they describe communication rather than a component. Separate
startup from request execution, and local state from external services. The renderer
shows a directed SVG overview with authored labels and can focus one node's direct connections.
Keep one central collaboration path readable before auxiliary startup and state flows.
A task selector may highlight existing edges with local step numbers; do not number
the complete architecture as if it were one global execution sequence.
Use diagram captions and expand responsibilities and evidence on demand.
It does not infer topology or turn adjacent cards into a runtime sequence.

When useful, add one concrete task journey connecting the overview to mechanisms.
Track the input, the participating components, an observable result, and a decisive
failure or branch. A source-based walkthrough must not claim to be an executed run.
Do not force every project into an application/server/database template.

## Bind explanation to evidence

A source record must support the nearby claim, not merely mention its subsystem.
For a consequential connection, inspect caller, registration/assembly, callee and
important guards. Reusing an import block for several mechanisms is not evidence
of those mechanisms. Keep measured numbers, guarantees and author intent only when
the associated evidence establishes them; otherwise narrow or label the claim.
For decisive excerpts, add a reading goal and a few line-range notes explaining
guards, state, or failure behavior. Keep notes separate from the exact source;
never inject AI comments into an excerpt presented as original code.
Lexical syntax colors and focus-line emphasis serve different purposes.
Exact excerpts do not establish semantic coverage. Reader confidence comes from
this reasoning, not the count of green source badges.

Use explicit inline code for symbols and commands, emphasis for a small number of
key distinctions, and term references for concepts that need a short local explanation.
Do not classify arbitrary English words as code or color every acronym. Read
[study-format.md](study-format.md) for the additive version-1 fields and safe grammar.
Keep omitted optional content empty rather than inventing it.

## Render and inspect

Resolve `LEARN_PROJECT_SKILL` to this Skill's directory. Use Python 3.10+:

```bash
python3 "$LEARN_PROJECT_SKILL/scripts/render.py" /output/study.json --check
python3 "$LEARN_PROJECT_SKILL/scripts/render.py" /output/study.json --output /output/study.html
```

The renderer needs only the standard library. The single HTML has no network,
server, CDN, package, or other Skill dependency. Keep JSON with the outputs and
regenerate after corrections. Optional frontmatter is authored in JSON, not added
to generated Markdown by hand. Files are replaced individually, not as a multi-file
transaction; do not report success after a partial failure.

The validator checks structure, IDs, links, safe escaping, and excerpt line counts.
It does not inspect repositories or verify the truth of conclusions. Independently
check exact excerpts against the stated revision and reopen decisive supporting code.

Inspect a realistic desktop journey with actual long content: overview → mechanism
→ term → source → return → another step. Check readable line lengths, labeled map
relations, code overflow, visible focus, browser Back and direct deep links. Search
must reach hidden chapters as well as the current view, including a symbol found
only in an excerpt and text found only in a line-range note. Check that repeated
evidence does not flood results, snippets show the hit, and selection opens the
right disclosure and source line. Browser Back and reopening a source deep link
must retain a usable destination. Test manual read/question
state and explicit resume after reopening; scrolling is not evidence of understanding.
Content changes must not silently preserve a stale read status. When storage or
clipboard is unavailable, reading must continue and copy failure must be visible.

Use a second, differently shaped study to catch project-specific assumptions.
Check no-JavaScript sequential reading and printing with all evidence expanded.
Distinguish interaction checks from target-project runtime tests or comprehensive
accessibility acceptance. Narrow screens may degrade gracefully; do not expand a
user's desktop-only scope into mobile redesign.

Deliver the HTML link with a short substantive update and precise verification
boundaries. Do not duplicate the whole study in chat or publish it merely to preview it.
