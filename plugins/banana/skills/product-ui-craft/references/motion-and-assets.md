# Motion Contracts and Asset Boundaries

Treat motion as a feedback system for product state, operation results, and spatial relationships—not as a decorative layer added at the end.

## 1. Classify Expressive Elements

Assign one primary semantic class to every dynamic element:

- **Product data:** progress, count, status, result, or system event. It must be traceable and truthful.
- **Interaction metaphor:** explains drag, grouping, expansion, confirmation, waiting, or transition. It may be expressive but cannot contradict product state.
- **Decorative material:** texture, ambient movement, light, or atmosphere. It must remain removable and cannot carry the only copy of information.

If an element spans classes, record the priority and its fallback when data is missing or motion is disabled.

## 2. Write a State Contract for Every Key Motion

Record:

- user goal and product fact being explained;
- real trigger event and state source;
- idle;
- engaged/input;
- processing/waiting;
- completion;
- failure;
- interruption, navigation, and refresh recovery;
- touch branch;
- `prefers-reduced-motion` branch;
- keyboard, focus, and screen-reader equivalent feedback;
- hidden-page, route-change, and asset-failure behavior;
- observable completion condition.

Drive state changes from product events. Time-based decorative loops must be visually distinct from progress.

## 3. Make Waiting Honest

A waiting surface must explain what the system is doing, whether the user must act, whether they can leave or cancel, and how failure recovers. Prefer real request stages, streamed output, completed subtasks, or other verifiable system events.

Without a real percentage, use indeterminate progress. For long waits, reveal useful partial output, completed evidence, or preparation for the next task instead of rotating copy that pretends to be work.

## 4. Choose the Lowest Sufficient Technology

Escalate only when the lower level cannot satisfy the contract:

1. **CSS** — hover, reveal, color, transform, and basic transition;
2. **DOM/SVG/framework state** — business state, paths, and accessible structural motion;
3. **Motion library** — complex orchestration, reversible timelines, or scroll-bound sequences;
4. **Canvas** — high object counts, continuous fields, particles, or draw-heavy effects;
5. **WebGL** — 3D, shaders, or effects that genuinely require the GPU.

Evaluate input latency, main-thread cost, memory, initial payload, fallback, mobile thermals, and maintenance. Do not escalate technology merely to signal sophistication.

## 5. Prototype High-Risk Effects

Prototype Canvas, WebGL, heavy motion libraries, complex gestures, and cross-scene signature materials as disposable experiments. Answer only:

- Is the visual memory point real?
- Does it clarify the task or state?
- Do pointer, keyboard, and touch all have natural paths?
- Is the experience clear with reduced motion?
- Does it meet the project's performance budget on target devices and content scale?
- Can it fail or degrade safely?

Passing proves direction, not production readiness. Record the decision and return to the material or technology level when it fails.

## 6. Produce Assets After Motion Is Approved

Keep three asset classes separate:

- **Concept images** — calibration and production specification;
- **Keyframes/prototype assets** — motion and transition validation;
- **Runtime assets** — images, textures, icons, fonts, or models loaded by the product.

For each runtime asset, record its ID, scene, semantic class, purpose, source, format and dimensions, loading condition, responsive variant, fallback, rights, performance budget, owner, and status.

Use images only for image-shaped work. Keep business copy, buttons, inputs, state, data, and accessible interaction in the DOM; prefer SVG for scalable graphics; use Canvas/WebGL only for justified programmatic effects.

Load heavy assets by scene and state. Define first-load scope around the primary task, then verify lazy-loading, prefetching, and caching in real network evidence.

## Motion & Asset Gate

Pass only when key motion has a complete state contract; waiting has a real source; risky prototypes have decisions; touch and reduced motion are first-class branches; every runtime asset has a purpose; and performance and loading validation are defined.
