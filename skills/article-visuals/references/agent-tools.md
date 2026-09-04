# Agent Tool Routing and `visual-assets`

Read this reference before acquiring or processing assets. Agent runtimes expose different browser and image tools; choose by capability and keep the image core provider-neutral.

## Acquire from the web

Use the current-request override first. Otherwise prefer:

1. `ego-browser` when available, especially for isolated spaces and existing login state;
2. the runtime's Browser or Chrome control Skill;
3. another installed browser automation tool with element screenshots;
4. Playwright CLI fallback when no Agent browser tool is available.

Follow the selected browser Skill in full. Prefer a semantic snapshot to locate the exact element, then capture that element or a deliberate clip. Use a viewport/full-page screenshot only when the page itself is the evidence or the element cannot be isolated.

Save the result to `visuals/originals/` and close or complete temporary browser task spaces according to the selected tool's rules.

## Route deterministic and generated assets

- Code or tables: call `$code-to-image` and register the rendered file as an original.
- Original pencil/editorial explainer: call `$to-illustration`.
- Other suitable generated bitmap work: use the runtime's image-generation capability.
- Existing real assets that need editing: never send them through a generative backend for ordinary crop, resize, masking, or annotation; use `visual-assets`.

Generation providers return pixels. They do not decide the article's visual function, evidence binding, approval, or placement.

## Resolve and prepare the image tool

```bash
VISUAL_TOOL_DIR="$SKILL_DIR/scripts"
npm ci --prefix "$VISUAL_TOOL_DIR"
npm run build --prefix "$VISUAL_TOOL_DIR"
node "$VISUAL_TOOL_DIR/dist/cli.js" capabilities --json
```

Reuse an existing successful install/build. Install only inside the Skill tool directory; never install project dependencies into the article repository.

Set a task-local command prefix instead of relying on a global binary:

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js"
```

## Model-to-tool loop

The model uses the CLI as a typed Agent tool. It must not recreate image-processing code.

### Inspect

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" inspect --input <absolute-image-path> --json
```

Read format, orientation, dimensions, alpha, byte size, and input warnings before proposing a transform.

### Build a selection surface

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" analysis-board --input <absolute-image-path> --output <absolute-board.png>
```

View the board. Identify the smallest region that preserves the served claim and necessary context. Express semantic choices in normalized coordinates so they survive source-resolution changes.

### Transform declaratively

Write a versioned recipe file. Prefer a meaningful output path under `visuals/candidates/` or `visuals/assets/`.

```json
{
  "version": 1,
  "input": "/abs/visuals/originals/source.png",
  "output": "/abs/visuals/candidates/V-agent-control.png",
  "purpose": "Show the Agent control and takeover bar",
  "operations": [
    {
      "op": "crop",
      "unit": "normalized",
      "x": 0.1,
      "y": 0.42,
      "width": 0.8,
      "height": 0.28
    },
    {"op": "resize", "width": 2000, "withoutEnlargement": true}
  ]
}
```

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" transform --recipe <absolute-recipe.json> --json
```

The tool validates paths, bounds, pixel limits, operation order, and output safety. Treat a non-zero exit as failure; read its JSON error and change the recipe or route, not the tool's generated pixels.

For a tall screenshot, let the model choose semantic panels from the analysis board. Segments are full-width vertical regions and may overlap deliberately:

```json
{
  "version": 1,
  "input": "../originals/long-page.png",
  "outputs": ["../candidates/page-01.png", "../candidates/page-02.png"],
  "operations": [
    {
      "op": "split",
      "segments": [
        {"mode": "normalized", "y": 0, "height": 0.56},
        {"mode": "normalized", "y": 0.50, "height": 0.50}
      ]
    }
  ]
}
```

For an annotated variant, keep the unannotated candidate and create a separate recipe/output. Supported annotations are `box`, `highlight`, `arrow`, `number`, `blur`, `redact`, and `zoom-inset`:

```json
{
  "version": 1,
  "input": "../candidates/V-agent-control-clean.png",
  "output": "../candidates/V-agent-control-annotated.png",
  "operations": [
    {
      "op": "annotate",
      "annotations": [
        {"type": "box", "normalized": {"x": 0.1, "y": 0.7, "width": 0.8, "height": 0.18}},
        {"type": "number", "value": 1, "normalized": {"x": 0.1, "y": 0.7, "width": 0.1, "height": 0.18}}
      ]
    }
  ]
}
```

Use `redact` when information must be irreversibly covered. Blur is a reading aid, not a privacy guarantee.

### Preview and validate

Initialize the manifest once before the first manifest-backed transform. Relative recipe inputs and outputs resolve from the recipe file; manifest source, output, and article paths resolve from the manifest file.

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" init \
  --manifest <absolute-manifest.json> \
  --article <article-path-relative-to-manifest-or-absolute> \
  --version <canonical-version> --json

node "$VISUAL_TOOL_DIR/dist/cli.js" transform \
  --recipe <absolute-recipe.json> \
  --manifest <absolute-manifest.json> --json

node "$VISUAL_TOOL_DIR/dist/cli.js" preview \
  --manifest <absolute-manifest.json> \
  --plan <absolute-visual-plan.json> \
  --output <absolute-preview.html>

node "$VISUAL_TOOL_DIR/dist/cli.js" validate \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --profile wechat --json
node "$VISUAL_TOOL_DIR/dist/cli.js" validate \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --profile desktop --json
```

Open the preview, inspect every approved candidate, and verify the adjacent article context. Mechanical validation is necessary but cannot approve visual meaning.

After the user gives the batch decision, record it through the CLI instead of editing JSON by hand:

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" review \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --approve <asset-id,asset-id> --json
node "$VISUAL_TOOL_DIR/dist/cli.js" review \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --reject <asset-id,asset-id> --json
node "$VISUAL_TOOL_DIR/dist/cli.js" validate \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --profile wechat --final --json
```

Passing `--plan` validates visual-plan v1, article/version alignment, plan-to-manifest IDs, final statuses, alt text, and evidence IDs for evidence/demonstration items. Preview uses the same plan to show article position, function, served claim, alt text, evidence, and tradeoffs in article order.

If the canonical article changes, do not edit hashes or keep old approvals by hand. Rebase both authorities together:

```bash
node "$VISUAL_TOOL_DIR/dist/cli.js" rebase \
  --manifest <absolute-manifest.json> --plan <absolute-visual-plan.json> \
  --article <article-path> --version <new-canonical-version> --json
```

Rebase records the previous article binding, updates both article references, resets every retained manifest asset to `unreviewed`, and returns approved/placed plan items to `candidate`. Rejected alternatives remain rejected. Regenerate any affected assets, preview, and review again.

Rejected alternatives remain in the manifest for audit and do not block final validation. An unreviewed, stale, failed, missing, hash-mismatched, or article-hash-mismatched package does block it.

## Failure policy

When a transform cannot preserve information and reading height together, try in order:

1. capture a more exact source element;
2. remove irrelevant outer regions;
3. split at semantic boundaries;
4. pair a readable summary crop with the high-resolution original;
5. keep a deliberate vertical exception.

After two failed variants from the same source and approach, change the source or route instead of accumulating arbitrary crop tweaks.
