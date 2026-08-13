# Art Direction for Multi-State Products

Use this reference to turn product truth into an implementable visual world and an ImageGen production plan. Design for applications with multiple scenes and states; do not impose a marketing landing-page section pack.

## 1. Derive the Creative Axis from Product Meaning

Write one sentence describing the change the user is making. Then answer:

- What does the user feel before, during, and after the task?
- Which real data or state changes deserve visual emphasis?
- What material, spatial behavior, or feedback can naturally express that change?
- What can recur across scenes while changing behavior with the job?

Condense the answers into one narrative axis and a family of **signature interaction materials**. A material may be a shape, light behavior, sound cue, typography treatment, physical metaphor, data behavior, or spatial relationship.

A strong material is product-specific, state-bearing, reusable across scenes, feasible in browser technology, and still meaningful after decoration is removed.

## 2. Lock the Shared Visual World

Record these shared tokens before generating calibration concepts:

- **Palette:** canvas, surface, text, muted text, accent, success, warning, and error;
- **Typography:** display, heading, body, data, label, and product-chrome roles;
- **Material treatment:** surface, edge, texture, light, shadow, and image processing;
- **Density:** information per viewport, content-to-chrome ratio, and whitespace responsibilities;
- **Light/dark rhythm:** which scenes shift tone, why, and how continuity survives;
- **Component language:** inputs, selections, cards, lists, progress, feedback, and CTA hierarchy;
- **Motion character:** speed, easing, amplitude, continuity, and restraint.

Create unity through shared tokens and materials. Create richness through different jobs, compositional anchors, state feedback, and density. Allow light/dark scene changes only when they serve meaning and preserve continuity.

## 3. Give Whitespace a Job

Classify every meaningful empty area as:

- **Focus** — protects the primary task or conclusion;
- **Separation** — establishes phase, hierarchy, or reading rhythm;
- **Motion field** — gives state change or direct manipulation room to happen.

Whitespace without one of these responsibilities is not sophistication. Reassign it to useful content, feedback, controls, or a stronger composition.

## 4. Build the Image Manifest

Use an **independent scene or key state** as the unit, not a marketing section. Record for every image:

- image ID and scene/state;
- current user job and primary CTA;
- desktop or mobile viewport;
- required real content and information hierarchy;
- current state of the signature material;
- interaction, transition, or waiting behavior the image must imply;
- inherited shared tokens;
- the design question this image must answer.

Publish the manifest and total count before generation. Produce one fresh horizontal image per scene or state. Add a mobile concept only when structure, order, or interaction changes materially. Never compress several product scenes into one unreadable overview.

## 5. Calibrate Before Expanding

Choose 1–2 images that expose the largest design risks: one representative primary job and one difficult state, density, or tonal shift. Generate and review them before the full set.

Evaluate five things:

1. The primary job and CTA are obvious without explanation.
2. The signature material is memorable and product-specific.
3. Density supports the real task instead of relying on empty space.
4. The system can extend to waiting, error, completion, and long content.
5. Layout, hierarchy, and effects have a credible DOM/SVG/CSS/Canvas path.

When calibration fails, repair the creative axis, tokens, or composition before generating more images.

## 6. Write Precise ImageGen Briefs

Include the product and scene, user job, real content, composition, primary CTA, visual tokens, signature material, interaction implication, viewport ratio, cross-image invariants, and scene-specific variation.

Use concrete visible language: where content sits, how much space the primary region owns, how the eye moves, and how state appears. Terms such as “premium,” “modern,” “cinematic,” or “Awwwards-level” are goals, not sufficient instructions.

Write ImageGen briefs in English for precise art-direction vocabulary. Quote exact product UI copy in its real language and require it verbatim. Vary composition by task while keeping typography roles, palette relationships, material logic, CTA hierarchy, and signature material consistent.

If a concept is too small, blurred, crowded, or ambiguous for implementation, regenerate a fresh standalone scene/state/detail concept in the same visual world. Do not crop or enlarge an inadequate image into a false specification.

## 7. Treat Concepts as Production Specifications

Concepts define composition, material, hierarchy, atmosphere, and keyframes. They do not own runtime business logic. Separate the implementation surface:

- semantic content, forms, controls, state, and accessible interaction → DOM;
- icons, paths, and scalable graphics → SVG;
- layout, typography, surfaces, and basic transitions → CSS;
- high-count particles, continuous fields, or draw-heavy effects → Canvas/WebGL only when justified;
- illustrations, photographic material, and non-programmatic detail → runtime image assets.

If business copy, buttons, state, or live data are baked into a raster image, redesign the implementation boundary.

## Art Direction Gate

Pass only when the manifest and count are published; calibration concepts are approved; shared tokens and signature materials are recorded; scene-level task, density, and state differences are clear; key effects have implementation paths; and every mobile concept has a structural reason.
