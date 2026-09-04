# Visual Acceptance

Approval is based on the article at reading width, not on isolated source files.

## Candidate review

Present one recommended visual set in article order. For each item show:

- article position and function;
- the adjacent claim or concept;
- original and processed asset;
- processing summary;
- mobile, WeChat-content, and desktop renderings;
- specific alt text;
- unresolved tradeoff, if any.

Show alternatives only when the recommended candidate has a real unresolved tradeoff. Request one batch decision: approve, replace, or omit per item.

## Hard gates

- Every final image has a plan ID, function, article anchor, manifest record, production status `produced`, and approval `approved`.
- The article version matches the visual run or has been explicitly rebased and rechecked.
- The processed file exists, opens, and matches the manifest hash and dimensions.
- Crop boundaries do not cut text, labels, controls, faces, formulas, chart legends, or essential context.
- Annotations do not cover source content or imply a meaning absent from the original.
- The main point is available without opening the full-resolution image; meaningful detail remains available when opened.
- Consecutive visuals do not turn the article into an unexplained image wall.
- Alt text names what the image contributes instead of repeating a generic product or skill name.
- Image text, numbers, quotes, and product state agree with the canonical prose.
- Originals remain intact and every final output can be reproduced from its recipe.

Run final validation with both `--manifest` and `--plan`. Manifest-only validation remains available for pixel-package diagnostics, but it is not the complete article visual gate.

## Channel preview

Inspect at least these content widths:

- `375px`: phone viewport stress view;
- `677px`: WeChat-like content column;
- `960px`: desktop article column.

The preview is a diagnostic artifact, not a substitute for the real channel preview required by the publishing workflow.

## Return contract

Return this compact handoff to the parent workflow:

```json
{
  "article": {"path": "...", "version": "..."},
  "manifest": ".../visuals/manifest.json",
  "preview": ".../visuals/preview/index.html",
  "approvedAssets": ["V-..."],
  "placedAssets": ["V-..."],
  "contentFindings": [],
  "status": "approved"
}
```

Use `blocked` when a required asset cannot be produced, visual research conflicts with the prose, the run is stale, or required approval is missing. Include the exact next action.
