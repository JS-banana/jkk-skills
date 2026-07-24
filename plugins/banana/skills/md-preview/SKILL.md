---
name: md-preview
description: >
  Turn Markdown research, technical investigations, implementation guides,
  comparisons and architecture reports into a friendly, self-contained HTML
  reading preview with content-aware information architecture. Use when the
  user wants a designed reading page instead of raw Markdown, or when another
  research skill needs a human-facing report.
---

# MD Preview

Treat Markdown as the source of truth and HTML as a derived reading artifact.
Do not merely restyle the Markdown tree. Diagnose what the reader must decide,
understand and do; compile that into a designed presentation layer; keep the
complete source as the traceable dossier beneath it.

## Workflow

1. **Resolve the source.** Read the complete Markdown file and its local
   instructions. Record its path, audience, purpose and current status. Do not
   edit it during rendering.
   **Complete when:** the source and reader's job are explicit.
2. **Choose the content archetype.** Use `field-guide` for implementation plans,
   architecture studies, delivery reports and operational research with
   decisions, flows, gates, workstreams or risks. Use `document` only when the
   source's linear argument is already the right reading experience.
   **Complete when:** the page kind is chosen for content shape, not visual
   taste alone.
3. **Perform the design read.** Read
   [references/editorial-grammar.md](references/editorial-grammar.md). State the
   page kind, audience, vibe, narrative axis and the three dials: design
   variance, motion intensity and visual density. For a redesign, use
   `shape-product-experience` to move through Product Truth → Experience
   Architecture → Art Direction before styling.
   **Complete when:** the first viewport and primary reading path have a reason
   to exist.
4. **Build the presentation plan.** Initialize a source-shaped draft:

   ```bash
   python3 scripts/render.py SOURCE.md \
     --init-presentation /tmp/report-presentation.json
   ```

   Replace the empty modules with a concise decision brief, next move, system
   path, acceptance gates, decision ledger, delivery spine and risk signals.
   Every item must bind to a real `source_section`; do not copy full source
   paragraphs into the plan.
   **Complete when:** the reader can scan the plan without losing uncertainty,
   and every synthesis points back to its evidence.
5. **Route visuals.** Read
   [references/visual-routing.md](references/visual-routing.md) when the report
   contains architecture, workflow, sequence, data flow, lifecycle, comparison
   or chronology. Use typed semantic components for the main reading path;
   retain Mermaid for detailed topology. Invoke `handdrawn-illustrator` only for
   an optional conceptual explainer, never for exact architecture.
   **Complete when:** each visual has one information job and no visual invents
   a relationship.
6. **Render.** Use a temporary output by default so the source repository stays
   clean. Use an explicit user path for a persistent export.

   ```bash
   python3 scripts/render.py SOURCE.md \
     --presentation /tmp/report-presentation.json \
     --output /tmp/md-preview/REPORT.html
   ```

   The renderer must keep raw HTML escaped, embed local images and all runtime
   assets, initialize Mermaid with `securityLevel: strict`, and include the
   original Markdown in the source dialog.
   **Complete when:** the command returns the HTML path and source SHA-256.
7. **Validate and inspect.** Read
   [references/quality-gates.md](references/quality-gates.md), then run:

   ```bash
   python3 scripts/validate.py --html REPORT.html --source SOURCE.md
   ```

   Open the result in a real browser. Check desktop, 375 px, keyboard, dark
   theme, reduced motion, diagram fallback/zoom, print and offline loading.
   **Complete when:** validation passes, the semantic modules visibly precede
   the full dossier, the console has no errors, and desktop/mobile interactions
   have direct evidence.
8. **Hand off.** Return the HTML path, source path/hash, archetype, validation
   result, browser coverage and any degraded assets. Do not call the report
   current when its recorded source hash differs from the source.

## Source Contract

- Rendering never mutates the Markdown source.
- The presentation layer is synthesis, not a second source of truth. Its
  `source_section` bindings must resolve to real headings.
- The complete safe rendering and original Markdown snapshot remain available;
  the presentation may reorder attention but may not erase source material.
- Applying review feedback is a separate content edit: update the Markdown
  first, then regenerate HTML.
- A failed or unsupported Mermaid diagram keeps its readable source fallback.
- Remote images are shown as links instead of being fetched automatically.
  Local images are embedded as data URLs.

## Runtime

The renderer uses Python's standard library plus the vendored Mistune parser
and Mermaid asset. The content-aware layer is semantic HTML and CSS; it needs no
React runtime, package installation, build step, CDN or network connection.
