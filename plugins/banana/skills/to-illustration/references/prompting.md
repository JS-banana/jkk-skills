# Prompting

Read `visual-language.md` first. Keep prompts skimmable and change one variable per repair.

## Generation recipe

```text
Use case: stylized-concept
Asset: <article body illustration | conversational concept>, <aspect ratio>
Thesis: This image must communicate: <one sentence>.

Input images:
Image 1 is the canonical style reference. Use its graphite line, selective hatching, spatial calm, scale tension and warm accent; do not copy its scene.
Image <N> is the canonical lettering reference. Preserve its hand rhythm, hierarchy, pressure changes and bilingual character; do not copy its words or objects. <include whenever text appears>
Image <N> is the canonical character sheet. Preserve the traveler identity while changing only pose and action. <omit when absent>

Canvas and framing:
<paper or charcoal>, <viewpoint>, asymmetrical balance, at least one third quiet space, full subject visible, generous safe margins.

Connected scene:
<one ground or spatial frame; focal action; object relationships; scale; reading direction>.

Character:
<exact load-bearing action and invariant traits, or no recurring character>.

Line and color:
Fine graphite contours, slight pressure variation, selective crosshatching, one ochre/pencil-yellow accent only. No other color family.

Hand-lettered text:
Text role: <none | focal line | annotated scene | explainer labels>.
Focal line: "<exact sentence>". <omit when absent>
Labels: "<exact label 1>", "<exact label 2>". <omit when absent>
Render every listed string verbatim and once. Follow the lettering reference: one human writer, mildly uneven baseline, varied character boxes and spacing, visible pressure changes, occasional dry edges. Keep the focal line 1.8–2.5 times the label height. <or: No text anywhere.>

Invariants:
One thesis, one connected scene, shared perspective and line language. No collage, cards, PPT, formal diagram, fake UI, extra title, unrequested English, watermark, copied composition or additional text.
```

Do not place field names, style instructions, color names or hex values inside the image.

## Text-only repair

```text
Keep the composition, objects, character, viewpoint, line work, hatching, canvas and accent unchanged. Change only the hand-lettered text. Render exactly and once: "<label 1>", "<label 2>". Remove every other character or word. Match the canonical lettering board: one writer, natural baseline variation, nonuniform character boxes, visible pressure changes and no font-like regularity. Keep the text in the existing quiet areas and preserve all other pixels as closely as possible.
```

## Lettering-style repair

```text
Keep every word, object, character, position, viewpoint, line, color and crop unchanged. Change only the letterforms. Preserve the exact strings, but make them feel written directly onto the paper by the canonical writer: mildly uneven baseline, varied character width and spacing, visible pressure changes and occasional dry edges. Remove typeset regularity without reducing legibility.
```

## Blank-zone regeneration

```text
Regenerate the same connected scene with the same thesis, viewpoint, character action and pencil style. Remove all text. Preserve clean quiet space at <normalized positions> for later labels. Do not draw boxes, plates, underlines or placeholder marks in those areas.
```

## Reference discipline

- Label each reference by index and role.
- Extract line density, palette, silhouette or factual cues; never ask to copy a complete style, character or composition.
- Repeat the preserve list on every edit.
- Prefer a short targeted correction over adding more adjectives to the base prompt.
