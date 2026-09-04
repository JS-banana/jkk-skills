# Architecture

This package separates article judgment from provider calls and pixel execution. The separation is a stability boundary, not presentation layering.

## Components

```text
article + evidence + channel targets
                 |
                 v
        article-visuals Skill
      plan / route / judge / approve
         |          |          |
         v          v          v
 browser tools   renderers   image generation
         \          |          /
          \         v         /
           immutable originals
                    |
                    v
          visual-assets CLI
 inspect / board / transform / preview / validate
                    |
                    v
       manifest + reproducible outputs
                    |
                    v
       article binding / parent workflow
```

### Skill: semantic authority

The Skill reads the article, decides whether a visual is useful, assigns its function and anchor, selects a source route, interprets analysis boards, judges the result at reading width, requests approval, and reports content conflicts.

It may use Agent tools, but it never treats a provider response as approval and never writes ad-hoc pixel-processing code.

### Acquisition adapters: replaceable providers

Browser control, code/table rendering, diagrams, and image generation are capabilities of the current Agent runtime. Their invocation stays in Skill instructions instead of the CLI. A provider can be added or replaced without changing recipes or manifests.

Provider output becomes an immutable original before entering the image core. Acquisition metadata records the URL or local source, capture time when relevant, provider, and the distinction between fact source and display source.

### `visual-assets`: deterministic executor

The CLI owns image decoding, geometry, annotation, encoding, hashing, atomic writes, manifest checks, and preview generation. It does not decide whether a crop is truthful or whether an illustration belongs in the article.

Recipes are versioned data. The same supported input and recipe must reproduce equivalent geometry and content; output encoding metadata may vary across compatible libvips versions and must not be mistaken for a semantic change.

### Manifest: visual-run authority

`manifest.json` is the single machine-readable state for inputs, source hashes, recipes, derived files, dimensions, validation, approval, and article identity/version. `visual-plan.json` records semantic proposals and placement decisions. The parent writing workflow stores only their paths and current/stale state.

Do not duplicate asset lists in Markdown state, channel files, or upload ledgers. Upload systems may keep their own delivery ledger but must reference the visual asset ID and source hash.

## Invariants

- Originals are immutable and derived outputs never overwrite their input.
- Relative recipe paths resolve from the recipe file; manifest paths resolve from the manifest file.
- Writes are atomic: a failed transform cannot replace a valid prior output or leave a success record.
- Geometry and input pixel limits are checked before expensive work.
- EXIF orientation is normalized before model-selected normalized coordinates are applied.
- A transform can be mechanically valid and semantically rejected; production `status` and human `approval` remain separate fields.
- A stale article version blocks final validation even when every image file still exists.
- Real evidence images never receive generative fill, object replacement, or rewritten source text.

## Extension rules

### Add an acquisition provider

Update `agent-tools.md` with capability detection, invocation, cleanup, and metadata mapping. Do not add the provider SDK to `visual-assets`.

### Add an image operation

Add a versioned recipe schema, deterministic implementation, bounds and resource validation, manifest serialization, and success/failure tests. If the operation changes source meaning rather than presentation, it does not belong in the CLI.

### Add a channel profile

Add reading widths and mechanical limits to validation/preview without creating a second transform pipeline. Channel-specific derivatives remain variants of the same asset ID.

### Change a schema

Increment the schema version only for incompatible changes. Keep the previous reader or provide an explicit migration; never silently reinterpret an existing recipe or manifest.

## Why this is a CLI, not a service

The current workload is local, file-oriented, single-run, and needs direct Agent invocation. A service would add deployment, authentication, concurrency, and storage state without improving the core result. Introduce a service only when multiple concurrent users, remote workers, a persistent review UI, or centralized asset governance becomes a real requirement.
