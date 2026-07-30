# Quality Gates

Use these gates before handing off a report.

## Deterministic validation

- The HTML embeds a manifest whose source path and SHA-256 match the Markdown.
- The recorded source size, source heading count and rendered heading count
  match the current source.
- There are no external scripts, stylesheets, fonts or runtime image requests.
- Raw source HTML is escaped.
- Mermaid is bundled and initialized with `securityLevel: strict`.
- The original Markdown is available in the source dialog.
- The document has a skip link, one `main`, a labelled navigation region,
  visible focus styles and a print stylesheet.

## Browser matrix

Serve the output directory on an unused loopback port:

```bash
python3 -m http.server 0 --bind 127.0.0.1 --directory OUTPUT_DIR
```

Use the printed port, then confirm `meta[name="report-source-sha256"]` matches
the renderer result before checking the page.

Inspect the real output at:

- desktop at 1440 px;
- mobile at 375 px;
- 400% zoom or 320 CSS px equivalent;
- light and dark themes;
- keyboard-only navigation;
- `prefers-reduced-motion: reduce`;
- offline or with the network disabled;
- print preview;
- every Mermaid diagram in normal and expanded view.

Expected behavior:

- The article reflows without two-dimensional page scrolling. Wide tables and
  diagrams may scroll inside their own labelled containers.
- The active table-of-contents item follows reading position.
- theme, reading width and density controls remain keyboard accessible.
- code-copy and diagram controls provide visible success/failure feedback.
- failed diagrams retain their Mermaid source and do not hide nearby content.

## Editorial review

- The first screen presents a decision, current state, next move and organizing
  path—not just a title and report statistics.
- `field-guide` output contains system path, acceptance gates, decisions,
  workstreams and risks before the complete dossier.
- Every presentation item links to a real source section.
- The summary and semantic modules contain no facts absent from the source.
- Long content is navigable without flattening its hierarchy.
- Tables retain header semantics and code remains selectable.
- The interface has one spatial narrative and avoids generic hero + KPI + card
  dashboard composition.
- Typography, density, color and motion match the declared design read.
- The complete source remains easy to open, collapse and verify.
