# Study data, version 1

The owned renderer reads UTF-8 JSON, with text strings (never raw HTML). Prose supports a small explicit
inline grammar: `code`, **emphasis**, and [[term-id]] or [[term-id|label]].
These tokens do not nest; other Markdown is ordinary text. Titles, navigation labels, questions, diagram captions, term definitions, source
labels, paths and excerpts remain literal text, including any markup-like strings.
Semantic prose fields are summary/next; overview body, node/group summaries, edge
label/diagram_label, journey body and path summary; mechanism answer/principle/limits;
step body/input/output/state and branch condition/effect; evidence supports/reading_goal
and annotation body. Inline code spans do not recursively interpret term syntax. One study is the source of both the interactive HTML and the portable
Markdown export. Do not maintain a second hand-written report with competing
claims. Author this data after investigating; formatting is not research.

Required fields:

```json
{
  "version": 1,
  "project": {"name": "Project", "revision": "revision or working-tree description", "scope": "What was inspected and what was not", "language": "en"},
  "title": "A question worth understanding",
  "summary": "The answer first, in a short paragraph.",
  "overview": {
    "body": ["Explain the representative cooperation."],
    "nodes": [{"id": "entry", "title": "Entry", "summary": "Its responsibility", "evidence": []}],
    "edges": []
  },
  "mechanisms": [],
  "evidence": [],
  "next": ["A useful next reading question and where to investigate it."]
}
```

`project.language` is `zh-CN` or `en` (default `en`) and controls interface
labels. Write study prose in the user's language. `project.url` is optional.
IDs are unique within their collection, matching `[a-z][a-z0-9-]*`.
The mechanism ID `overview` is reserved for navigation.

Overview nodes can optionally include `mechanism`, the ID of a deeper
explanation. Edges are authored relationships, never inferred from node order:
`{"from":"entry","to":"result","label":"passes the request"}`.
An optional `evidence` list on each edge supports that connection. Layout does
not imply execution order; use precise edge labels for calls, data, events or
authored transformations. Empty maps are allowed when no diagram helps.

Each mechanism:

```json
{
  "id": "delivery",
  "title": "Preserving the previous output",
  "question": "What happens if generation fails?",
  "answer": "Explain the mechanism before asking the reader to explore it.",
  "steps": [
    {
      "id": "prepare",
      "title": "Prepare a candidate",
      "body": ["Explain what the code actually does and how it is connected."],
      "input": "Optional concrete input",
      "output": "Optional result",
      "state": "Optional owner and state change",
      "branches": [{"condition": "Optional condition", "effect": "What happens", "target": "prepare"}],
      "evidence": ["source-one"]
    }
  ],
  "principle": ["Explain why this arrangement works; label inferred rationale."],
  "limits": ["Its costs, counterexamples, limitations or unverified behavior."],
  "evidence": ["source-one"]
}
```

Steps are an explanatory reading sequence. Their order alone does not assert
runtime edges. Use `branches` to describe actual transitions, including normal
continuation and failure; `target` is optional and must name a step in the same
mechanism when present. Branches are never called executed traces unless they
were run. Do not add invented state, branches or steps to fill fields. Steps,
principle, limits and evidence can be empty; omit optional input/output/state.

Each evidence item:

```json
{
  "id": "source-one",
  "label": "Candidate creation",
  "kind": "implementation",
  "path": "src/export.js",
  "lines": [40, 47],
  "url": "https://example.org/repository/blob/commit/src/export.js#L40-L47",
  "excerpt": "Optional exact contiguous source excerpt, not illustrative pseudocode",
  "supports": "The specific claim this source supports; also state relevant limits."
}
```

`focus_lines` optionally lists absolute source line numbers inside `lines` to
highlight; it does not change the exact excerpt.

`kind` is `implementation`, `docs`, `test`, `inference` or `execution`.
Reading a test uses `test`; `execution` requires an actually performed check
described in `supports`. `path`, `lines`, `url`, `excerpt` are optional: for
local-only sources give a path/location and a useful exact excerpt, without
inventing a browser-accessible URL. Links accept only HTTP(S). `lines`, if
present, is a positive inclusive `[start, end]`. For an excerpt with `lines`,
copy that exact complete range. Ellipses and pseudocode belong in explanations,
not in an excerpt presented as source. Prefer revision-pinned source URLs and
check that they match the studied contents.

The renderer checks types, IDs, references, URL schemes and safe escaping. It
does not verify source existence, excerpt accuracy, relationships, or the truth
of an explanation. The investigating Agent remains responsible for those.

Use the bundled `examples/archify.study.json` as an editable, complete example;
keep its project-specific conclusions out of unrelated studies. For a short
orientation, use a compact overview and no mechanisms. For deeper questions,
add only the mechanisms actually investigated.

## Optional reading structure (backward-compatible with version 1)

- `mechanisms[].nav_title`: a short, reader-facing navigation label. Keep the full
  explanation title in `title`; do not compress an unfamiliar acronym into navigation.
- `terms`: `[{"id":"acp","label":"ACP","definition":"Its role in this project."}]`.
  References such as `[[acp]]` are validated and open a definition; definitions
  are also included in the portable export. Do not mark every English word.
- `overview.groups`: `[{"id":"host","title":"Application host","summary":"Its boundary."}]`.
  A node's optional `group` must reference one. Groups express researched boundaries
  or responsibilities, not invented layers. An ungrouped map remains supported.
- `overview.journey`: `[{"title":"Receive a request","body":"A concrete transition.",
  "evidence":["source-one"],"mechanism":"delivery"}]`. Evidence and mechanism are
  optional. Use this for one representative action; explicitly distinguish a
  static explanation or illustrative input from an executed trace. Never infer
  runtime transitions from the array order.
- `frontmatter`: optional Markdown metadata object, with lowercase keys and string
  or string-array values. The renderer writes quoted YAML values from this same
  data. Preserve destination metadata conventions; do not auto-sign human review.

Groups and journey entries also appear in Markdown. Browser reading state is not
study content: it stays in local browser storage, keyed by project and section
content. A changed section is marked for rereading, not silently treated as read.

## Architecture flow and source guidance

The overview renders an SVG with labeled, directed relationships. Optional fields:

- `nodes[].caption`: a short literal responsibility label for the diagram; the full
  `summary` remains in node details. Prefer reader-facing words to symbol lists.
- `nodes[].position`: `[column, row]`, integers 0–20. Supply for every node or none;
  positions must be distinct. Omit for grouped column layout. This arranges the
  diagram, never establishes a runtime relationship. Canvas bounds include routed
  edges, labels and path markers; this is a conservative text estimate, not browser
  font measurement or a general collision-free graph layout guarantee. Keep groups spatially separate
  and leave intermediate rows free for long connections; inspect label collisions.
- `edges[].diagram_label`: a concise label for the same relationship. Full `label`
  and evidence remain in the relationship detail. Do not omit material uncertainty
  in the short label; explain any compact marker nearby.
- `edges[].role`: `primary` (default) or `support`; controls solid vs dashed styling,
  not evidence confidence. Mark documented/inferred relations in their prose.
- `overview.paths`: `[{"id":"request","title":"Follow a request",
  "summary":"What this illustrative path covers and excludes.","edges":[0,2]}]`.
  Indices refer to the overview edge array in explanatory order; each must exist
  and be distinct. Renumber when editing the edge array. A path highlights existing
  relationships; it does not add edges or assert a measured execution trace.

For meaningful excerpts, optionally add `reading_goal` and `annotations`:

```json
{
  "reading_goal": "Understand which failure is retried.",
  "annotations": [{"lines": [42, 45], "body": "Only this condition takes the fallback."}]
}
```

Annotation ranges are inclusive absolute source lines and must lie inside an exact
excerpt with `lines`. Explain guards, ownership, state changes, or error propagation;
avoid line-by-line syntax translation. These are separate reading notes, never
inserted into source text. Markdown retains them and copy excludes them.

`language` accepts a nonempty language name. The highlighter recognizes `plain`,
`kotlin`, `javascript`, `typescript`, `python`, `shell`, `json` and file-extension
aliases such as `js` or `kt`. Otherwise infer it from the source path. An unknown
explicit language preserves its display name and uses plain text; it never blocks
a valid study or silently selects another language from the path. The bundled conservative
lexer colors lexical tokens, not semantic symbols; unknown languages remain plain.
No network or external highlighter is required. Nested embedded languages remain
strings in the host language, rather than pretending to parse the embedded program.

Semantic edge labels render as prose in the relationship list and resolve to plain
text before SVG wrapping. Both use the same term definitions as Markdown.

Each rendered evidence occurrence has a unique source anchor. Search indexes
original excerpts and line-range notes, merges repeated evidence results, and
opens the owning section and disclosure before positioning the hit. Source line
links refer to the excerpt's absolute line numbers, not highlighted HTML offsets.
