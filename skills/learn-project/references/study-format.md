# Study data, version 1

The owned renderer reads UTF-8 JSON, with plain text strings (not HTML or
Markdown). One study is the source of both the interactive HTML and the portable
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
