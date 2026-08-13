---
name: to-illustration
description: >-
  Design and generate coherent pencil-drawn editorial, annotated and simple explanatory illustrations from Chinese articles or single ideas. Use when the user asks for 文章配图、手绘批注图、概念图、技术概念解释、简单流程图、聊天辅助表达 or an illustration shot list. Route articles through a 3–5 image plan before generation and render clear single concepts directly. Do not use for photo editing, logos, full poster/card/PPT layouts, or exact technical diagrams with strict topology.
license: MIT
---

# To Illustration

Turn written ideas into original pencil editorial scenes. Repeat the same reasoning and QA process, not the same composition.

Resolve `SKILL_DIR` to the installed directory containing this `SKILL.md`; use absolute paths derived from it for scripts and assets.

## Load the right references

- Before choosing a scene, read `references/composition.md`.
- Before every generation, read `references/visual-language.md` and `references/prompting.md` in full.
- When any visible text appears, use `assets/lettering-board.jpg` as a lettering reference.
- When the traveler appears, also read `references/character.md` and use `assets/character-sheet.jpg` as a reference.
- Before delivery, read `references/quality-bar.md` and apply every hard gate.

## 1. Route and lock the thesis

Determine the intended use, language and aspect ratio. Write one sentence: `This image must communicate: <thesis>.`

- **Article:** read the full source, choose 3–5 cognitive anchors, and return a shot list using the fields in `references/composition.md`. Wait for approval unless the user explicitly asked to generate immediately.
- **Single concept:** continue directly when the meaning is clear. Ask at most one question only when the missing answer would materially change the thesis or destination.
- **Wrong fit:** route full layouts, photo edits, logos and exact complex diagrams to a more suitable capability.

Complete this step only when the thesis, destination, ratio and character decision are explicit.

## 2. Design one connected composition

Choose exactly one register: editorial scene, annotated scene or explainer sketch. If the subject is visually specific or unfamiliar, gather trustworthy factual references first and extract only stable visual cues.

Describe one shared world: ground or spatial frame, viewpoint, focal action, scale relationship, negative space and reading direction. Do not assemble independent symbols into a collage.

Complete this step only when the composition can be described as one caught scene and every element serves the thesis.

## 3. Build and render the prompt

Follow `references/prompting.md`. Use the built-in image generation tool; do not add a provider layer.

- Pass `assets/style-board.jpg` as Image 1, a style reference only.
- When text appears, pass `assets/lettering-board.jpg` as the next reference and follow its hierarchy and hand rhythm without copying its words or objects.
- When the traveler is present, pass `assets/character-sheet.jpg` as the next reference and preserve its invariants.
- Quote every in-image string and follow the register-specific text budget in `references/visual-language.md`.
- Generate article images separately, never as a contact sheet.

Complete this step when the output exists at the requested ratio and the final prompt is recorded.

## 4. Inspect and repair

View every output and apply `references/quality-bar.md`.

- Fix one failure at a time while restating all invariants.
- When text is correct but looks typeset, repair only its lettering against `assets/lettering-board.jpg`; do not use the overlay script for a style failure.
- For wrong text, make one text-only repair. If it still fails, regenerate the same scene with clean blank label zones.
- After two text failures, read `references/text-overlay.md`, then overlay exact labels only if its requirements are available:

```bash
python3 "$SKILL_DIR/scripts/overlay_labels.py" input.png output.png labels.json
```

Complete this step only when every hard gate passes and the aesthetic score reaches the delivery threshold.

## 5. Save and deliver

For an article, save non-destructively beside the source:

```text
assets/<article-slug>-illustrations/
  PROMPTS.md
  01-<concept>.png
  02-<concept>.png
```

Record the approved shot list, final prompts and meaningful reject reasons in `PROMPTS.md`. Modify the source Markdown only when explicitly asked. For a standalone concept, use the user's destination or a task-specific workspace asset folder.

Report the final paths and which images are optional. Keep the explanation shorter than the visual plan.
