# The project-learning reader

The viewer is owned by this Skill: `scripts/render.py` and `assets/reader.*`.
It is designed around learning implementation, not a generic document theme.
Its useful unit is a question connected to a mechanism and evidence. Do not
edit or require another Skill to create a learning page.

## Compose for understanding

Start with the answer. Give the project a selective map of responsibilities and
explicitly authored relationships. Node order does not establish dependencies.
Connect a map node to a deeper mechanism when that relationship was investigated.
The map is an entry into the explanation, not a substitute for it.

For each mechanism, use a concrete question and a short answer, then a continuous
reading path. Explain what happens, who invokes it, what changes, and under which
conditions. A useful step has explanatory prose, not just input/output labels.
Use state and transition fields only when they help explain the actual behavior.
The reader presents steps as reading order; it never infers runtime transitions
from that order. Explicit branches retain normal continuation, failures, and
loops where relevant. Use the implementation's concepts instead of filling an
obligatory sequence of stages.

Explain why the mechanism works, its observable trade-offs, and the constraints
on reusing it. Label inferred rationale; do not ascribe motives to an author
without support. Show sources beside the claim they support. Source excerpts
are exact, concise, continuous ranges; illustrative pseudocode belongs in the
explanation. A source URL is a checking route, not proof of an interpretation.

The page has one navigation rail, an overview map, a focused step explanation,
and expandable evidence. Keep the prose self-contained before evidence is
expanded. For orientation only, omit mechanisms that have not been investigated.
For a deep question, spend the detail on the implementation rather than making
its overview larger. The map uses a simple responsive layout; when its edges
become hard to follow, reduce it to the relevant cooperation and explain the
subsystem inside a mechanism. Do not infer or omit a consequential relationship
just to simplify the layout. Relationship text remains available alongside it.

## Author and render

Read [study-format.md](study-format.md) for the data contract. The bundled
`examples/archify.study.json` is a complete worked artifact, useful when learning
the format; its content is not a template for conclusions about another project.

Save `study.json` in the user's artifact location, outside the project being
studied by default. Resolve `LEARN_PROJECT_SKILL` to this Skill directory, not
the caller's current working directory. Python 3.10+ and its standard library
are sufficient:

```bash
python3 "$LEARN_PROJECT_SKILL/scripts/render.py" /output/study.json --check
python3 "$LEARN_PROJECT_SKILL/scripts/render.py" /output/study.json --output /output/study.html
```

This generates a self-contained `study.html` and a readable `study.md` beside it.
CSS and JavaScript are embedded; the HTML opens offline with no server or CDN.
The Markdown is a complete portable export, not a second source of truth. Keep
the JSON with the outputs for later questions. Update only relevant explanations
and evidence, then regenerate the same outputs. Files are replaced individually;
the two exports are not a multi-file transaction. A failed invocation must not
be reported as a completed delivery.

The validator checks types, references, safe URL schemes and excerpt line counts.
It does not read the studied repository or prove source accuracy, architecture,
runtime behavior, or completeness. Verify these during investigation. Prefer
fixed-revision HTTP(S) source links for committed public code. For local or dirty
code use accurate path/symbol locations and excerpts, without creating misleading
permalinks. Editor `path:line` syntax is not a portable browser URL.

## Inspect what the reader will use

Open the generated HTML if browser tooling is available. Check the actual user
path: understand the answer, select a part, enter its mechanism, switch steps,
read a branch, and expand its supporting source. Check that navigation and the
selected explanation agree. Direct section links and browser Back should retain
that reading context. Do not claim an interaction was checked merely because its
control exists.

Check a narrow screen for page overflow and readable code. The full study remains
in the HTML: without JavaScript it can be read sequentially; printing expands the
study and its evidence. When available, check these behaviors rather than promise
them solely from the template. Do not claim a complete accessibility audit from
a keyboard smoke check.

Deliver the HTML link with a brief substantive answer and what was actually
checked. Link the data or Markdown when useful for continuation or portability.
If a local browser requires HTTP, use a loopback-only preview and retain the
offline file. Do not publish externally merely to provide a preview.
