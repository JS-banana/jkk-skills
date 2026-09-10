# From project orientation to a mechanism: Archify

This example demonstrates a change in reading depth, not a report template.
Its evidence is Archify commit
`5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70`; the links below pin that version.
The explanations use static source and test inspection. They do not claim a
fresh test run, and later users must not report these tests as their own execution.

## First request: “Help me quickly understand this project.”

Archify turns an authored diagram specification into an interactive HTML
artifact. The important boundary is between understanding the subject and
producing the diagram: the host agent interprets the request, inspects relevant
project material, and writes typed JSON. Archify's rendering path consumes that
JSON; it does not itself derive a repository's architecture. The
[authoring workflow](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/SKILL.md#L13-L35)
and [renderer loader](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/renderers/shared/cli.mjs#L19-L38)
show these two responsibilities.

For a representative architecture-diagram delivery, the cooperation is:

```text
host agent authors typed JSON
  → deliver reads the specification and prepares a private candidate
  → architecture renderer loads and validates the specification
      → verifies declared repository references when present
  → renderer produces candidate HTML
  → artifact checker examines that HTML
  → deliver replaces the output only after these steps succeed
```

The source-reference feature checks a narrower claim than “this architecture is
correct.” It checks repository metadata, a pinned Git commit, referenced files,
and requested line bounds. It then constructs source links. It does not decide
whether those lines support the component description or prove a runtime
connection between components. A reference to an existing but irrelevant function
is therefore not ruled out by these checks. See
[repository verification](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/renderers/shared/repository-evidence.mjs#L81-L234).

There are three useful reading routes, depending on what you want to learn:

| Interest | Entry point and what it explains |
|---|---|
| How the agent authors a diagram | The authoring workflow above: input shape, validation feedback, and focused corrections |
| What source-backed evidence means | The repository verifier above: exactly which properties are checked and which remain the author's responsibility |
| How failed generation preserves a prior result | [`commandDeliver`](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L755-L1121): candidate preparation, checks, and final replacement |

This establishes the main responsibility boundary and one delivery path. It does
not cover every diagram renderer or viewer interaction. Those internals are not
needed to answer the orientation request.

## Follow-up: “How does it preserve the old output if generation fails? What can I reuse?”

The decisive step is that rendering writes to a candidate, while the existing
output remains in place. Only a checked candidate reaches the final rename.
The deeper question requires following both the successful path and the returns
that occur before replacement; the renderer's existence alone cannot establish
this property.

Start with a concrete case: `diagram.json` is being delivered to `report.html`,
and `report.html` already contains a useful result.

1. **Read one specification and freeze it.** `commandDeliver` reads the input
   bytes once and parses them. It later writes those same bytes to
   `specification.snapshot.json`, then passes that snapshot to the renderer.
   The specification digest is also computed from those original bytes. This
   keeps the rendered input and the reported input digest tied to one read,
   even if the original file changes later. See
   [input read](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L773-L790),
   [snapshot and invocation](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L870-L899),
   and [receipt digests](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L1004-L1018).

2. **Put the candidate on the target filesystem.** A temporary directory is
   created inside the output directory, and the candidate HTML lives there.
   The source comment explicitly connects this placement to a same-filesystem
   rename. This matters because the final step is a rename, not a copy from an
   arbitrary temporary volume. See
   [candidate preparation](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L841-L871).

3. **Finish generation and checking before touching the destination.** The
   renderer receives the snapshot and candidate paths. A renderer failure
   reports stage `render` and returns. The artifact checker then reads the
   candidate; a check failure reports stage `check` and returns. Neither path
   reaches the destination rename. The checker validates an artifact, not the
   semantic truth of the system portrayed in the diagram. See
   [render and check branches](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L896-L937).

4. **Prepare the receipt, then commit the candidate.** Before replacement, the
   command parses the check result, reads the candidate bytes, extracts any
   repository evidence receipt, and builds digests and validation metadata.
   These operations can still fail without replacing `report.html`. It then
   rechecks the output-path constraints and calls
   `fs.renameSync(candidatePath, outputPath)`. A rename failure is reported as
   stage `commit`; the success receipt is printed only after replacement.
   See [receipt preparation](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L939-L1037)
   and [commit and reporting](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L1039-L1113).

5. **Attempt cleanup on exit.** A `finally` block removes the staging directory
   after the successful path or an earlier return. A cleanup error produces a
   warning. This is ordinary control-flow cleanup, not a guarantee that no
   temporary files survive a process kill or machine failure. See
   [cleanup](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/bin/archify.mjs#L1114-L1121).

The existing tests make useful counterchecks. One test inserts a second SVG into
an installed copy's template, starts with a trusted old output, and expects a
failed final check, unchanged old bytes, and no staging directory. Another uses
invalid diagram data to exercise the renderer-failure branch. A third uses a
directory as the destination to test commit failure without a false success
receipt. These are the expectations encoded in
[the failure tests](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/test/cli.test.mjs#L498-L598),
not tests executed as part of this example. The
[success test](https://github.com/tt-a1i/archify/blob/5769acefcc2ebd696a4f9ed3ac9cb6cca1d75c70/archify/test/cli.test.mjs#L275-L307)
also checks that receipt hashes match the input and final output.

The reusable idea is to separate producing a replacement from making it visible:
freeze the input that must stay consistent, produce a private candidate, validate
the properties that matter to the consumer, and commit at one clear boundary.
For a generated single-file report, that can preserve a last-known-good output
at the cost of temporary disk space and a separate checking pass.

Carry the conditions along with the idea. The checks must detect the failures
you care about; a well-formed diagram can still describe the wrong architecture.
The destination needs the rename semantics this design relies on. This function
does not establish power-loss durability through `fsync`, a transaction spanning
several published files, or concurrency control between competing deliveries.
The JSON success receipt is stdout output after the file commit, so publishing
the file and observing that receipt are not one atomic operation. A multi-file
publisher or a system needing durable acknowledgements requires further design;
copying this sequence alone would not establish those guarantees.

## What changed between the two answers

The overview checked responsibilities and a representative path. The follow-up
reopened one concrete behavior, followed its data and failure exits, used tests
to challenge the explanation, and extracted an idea with its constraints. It
did not repeat the entire architecture or inspect unrelated renderers. Apply
that change in depth to the user's question; do not copy Archify's file pipeline
onto projects whose core behavior is different.

For browser delivery, these passages become one evolving study: the orientation
provides the entry and navigation, and the follow-up extends the relevant
mechanism section. Keep the fixed-version source links beside the explanation,
update the study data and regenerate its HTML and Markdown, then return the page with a brief
description of the added insight. See [the reading-page guide](reading-page.md)
for presentation and verification; this example does not require a separate
report for each turn.
