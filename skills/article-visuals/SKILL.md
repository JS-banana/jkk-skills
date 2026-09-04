---
name: article-visuals
description: >-
  Plan and produce a complete visual package for a finished article: decide where visuals add evidence or explanation, collect real screenshots and public materials, route suitable gaps to diagrams or AI illustration, process assets non-destructively, preview them at reading widths, and bind approved outputs back to the article. Use for 文章配图、正文截图、配图规划、文章视觉素材 or a full article visual pass. Do not use for a single standalone illustration, cover-only generation, unrelated photo retouching, or publishing images by itself.
license: MIT
---

# Article Visuals

Build an article's visual evidence and explanation layer. A visual must help the reader verify, understand, compare, navigate, or feel something the prose alone cannot deliver as efficiently.

Resolve `SKILL_DIR` to the installed directory containing this file. Run the image tool with absolute paths derived from `SKILL_DIR`; never assume the current working directory is the skill directory.

For responsibility boundaries, state ownership, and extension rules, read [references/architecture.md](references/architecture.md) before changing this Skill or its toolchain.

## Modes

- **Article pass:** read the stable article, plan every useful visual, acquire or generate candidates, process them, request one batch approval, then bind approved assets to the article.
- **Visual run resume:** read the existing `visual-plan.json` and `manifest.json`, inspect their article version, and continue only current work. If the canonical article changed, run the documented `rebase` command; it resets retained assets for semantic review.
- **Single article asset:** when the requested asset and article position are already clear, reuse the same acquisition, processing, preview, and manifest rules without replanning the whole article.

Route a request for one original pencil/editorial illustration to `$to-illustration`; route cover-only generation to the available cover capability; route code/table rendering to `$code-to-image`. This skill may call those capabilities during a full article pass, but does not replace them.

## Workflow

### 1. Establish the article contract

Locate the canonical article and its working directory. When invoked by `jkk-writer-v2`, require the content gate to be current and consume its canonical version, visual hints, evidence IDs, research brief, and channel targets. Standalone use may accept an article path or pasted Markdown.

Create or resume `<article-workdir>/visuals/`. Keep original source material outside this directory read-only.

Before planning, read [references/planning.md](references/planning.md). Produce schema-valid `visual-plan.json` with the article identity/version and one record per proposed visual: position, function, claim or concept served, specific alt text, preferred route, alternatives, and status.

### 2. Route each visual by function

Choose the asset route from the visual's job, not from a fixed real-vs-generated quota:

- evidence or product behavior -> author/runtime screenshot or relevant public material;
- quotation, announcement, identity, or public reaction -> focused webpage/social/media capture;
- code or table -> deterministic rendering;
- process, comparison, architecture, or mechanism -> existing authoritative diagram or deterministic explainer first;
- concept, atmosphere, or an otherwise invisible mechanism -> original illustration when it materially helps;
- cover -> solve the title's information function using the strongest available route.

The source used to verify a fact and the asset used to explain it may differ. Score candidates by claim relevance, authenticity, glance comprehension, reading-width legibility, and visual interest. Do not promote an easy-to-capture image that serves the article poorly.

### 3. Acquire originals with Agent tools

Read [references/agent-tools.md](references/agent-tools.md) before browsing, capturing, rendering, or generating. Let the current runtime's capabilities determine the provider; keep provider-specific calls outside the image core.

Prefer an exact element or information-region capture over a full page followed by destructive cropping. Store every acquired or generated input under `visuals/originals/`; never overwrite it. Register its role and article position before processing.

If visual research reveals a factual conflict or changes the prose claim, stop asset placement and return the finding to the article's content gate. A visual stage must not silently repair prose.

### 4. Process through `visual-assets`

Use the tool contract in [references/agent-tools.md](references/agent-tools.md). The model decides semantic intent; the tool owns pixels and geometry.

For screenshots that need selection:

1. inspect the original;
2. generate an analysis board;
3. view it and propose normalized regions or annotations;
4. submit a declarative recipe;
5. execute non-destructively;
6. view the output and check that no text, label, or context was accidentally lost.

Prefer `element -> trim -> crop -> split -> pad`. Never stretch an image to meet a ratio. Use a reading-height budget rather than a universal aspect ratio: remove irrelevant height, split semantically tall material, and preserve exceptions whose structure needs vertical space.

Keep a clean processed version when annotations are added. Generative fill, object removal, and rewritten screenshot text are not valid repairs for real evidence.

### 5. Preview and approve once

Read [references/acceptance.md](references/acceptance.md). Generate the local preview from `manifest.json` and inspect mobile, WeChat-content, and desktop widths. The default review is one batch containing the recommended set; include alternatives only where the skill is genuinely uncertain.

Wait for approval before binding final assets into the article unless the current request explicitly authorizes direct application. Approval covers asset selection and placement, not publishing or uploading.

### 6. Bind without forking article state

After approval:

- place each image next to the exact claim or concept it serves;
- write specific alt text and an optional source/caption when it improves comprehension;
- update `visual-plan.json` and `manifest.json` as the visual run's only asset state;
- update the article Markdown only when this run is authorized to do so;
- when invoked by `jkk-writer-v2`, return the manifest path, article version, approved asset IDs, and any content-gate findings.

Do not create a second writing state. Pure asset changes revalidate the visual package and channel projection; factual changes return to the canonical article and content gate.

Uploading, R2 URL conversion, channel publishing, and archive cleanup remain separate actions. Call `$to-r2-image` only when the parent workflow or user explicitly reaches that stage.

## Hard requirements

- Originals are immutable; all transforms are reproducible derived outputs.
- `manifest.json` is the sole authority for recipes, hashes, variants, and validation status.
- Image operations go through the declared `visual-assets` interface, not model-written one-off image code.
- No final asset passes on dimensions alone: it must remain useful at actual reading widths.
- A broken image, unreadable crop, generic alt, lost evidence ID, stale article version, or unreviewed final set blocks delivery. Rejected alternatives may remain in the manifest for audit but are never placed.
- Do not leave partial output presented as success. Report the failed asset, preserved originals, and exact next action.
