# Frontend Implementation and Fidelity Workflow

Use this reference after representative concepts, motion contracts, and required assets are approved. It turns visual intent into production code without letting an implementation tool redefine the product.

## Contents

- [Route Responsibilities Explicitly](#1-route-responsibilities-explicitly)
- [Extract an Implementation Contract Before Coding](#2-extract-an-implementation-contract-before-coding)
- [Preserve the Repository and Product Boundary](#3-preserve-the-repository-and-product-boundary)
- [Build One Representative Slice First](#4-build-one-representative-slice-first)
- [Implement Scene by Scene](#5-implement-scene-by-scene)
- [Run the Fidelity Loop](#6-run-the-fidelity-loop)
- [Control Deviations](#7-control-deviations)

## 1. Route Responsibilities Explicitly

- **Product UI Craft** owns product truth, architecture, approved design decisions, Gate state, and deviation policy.
- **ImageGen** owns visual exploration, scene/state concepts, keyframes, and image-shaped runtime assets.
- **Frontend App Builder** or the host's equivalent capability owns faithful concept-to-code execution after approval.
- **Browser and image-inspection tools** own rendered evidence and concept-to-render comparison.
- **Verify** owns acceptance and must re-run evidence independently from Build's claims.

Use an installed frontend-app-builder capability when available; in Codex, prefer Frontend App Builder for visually significant builds and redesigns. Otherwise execute this workflow directly in the repository. Tool availability changes the executor, not the quality bar.

## 2. Extract an Implementation Contract Before Coding

Record from the approved concept and upstream artifacts:

- exact visible copy, navigation, CTA labels, data labels, and state messages;
- native concept viewport and first-viewport composition;
- palette, surface, border, shadow, radius, spacing, and motion tokens;
- typography families, fallbacks, scale, weight, line height, tracking, and control styles;
- icon inventory: metaphor, source family, stroke/fill, weight, size, color, alignment, and states;
- component families and variants;
- container model: open layout, band, rail, list, table, card, canvas, sidebar, drawer, or modal;
- image/media treatment, crop, mask, overlay, transparency, and standalone asset needs;
- responsive restructuring and structurally distinct mobile scenes;
- real state transitions, interactions, accessibility branches, and motion contracts;
- allowed deviations and unresolved details.

Regenerate a fresh scene/state/detail concept when the approved image is too small or ambiguous to extract. Do not invent missing visual decisions during Build.

## 3. Preserve the Repository and Product Boundary

Follow the existing framework, routing, state, component, styling, accessibility, and asset conventions. Do not introduce a new application shell or framework into an established product merely because an executor prefers it.

Keep live UI code-native:

- copy, controls, forms, tables, data, state, focus, and navigation → semantic DOM;
- scalable paths and icons → production-quality SVG;
- layout, typography, surfaces, and basic motion → CSS;
- continuous high-count rendering → Canvas/WebGL only when the motion contract justifies it;
- photographic, illustrative, or non-programmatic material → image assets.

Do not ship concept screenshots as UI or recreate central raster assets with rough CSS substitutes.

## 4. Build One Representative Slice First

Choose a scene that tests the app shell, primary content density, signature material, real state changes, and responsive behavior. Implement it through the extracted design system rather than one-off markup.

Complete the slice end to end:

1. exact structure and visible copy;
2. real or contract-faithful data states;
3. signature material and approved assets;
4. primary interaction and state-driven motion;
5. waiting, partial success, error, retry, and recovery;
6. desktop, intermediate, and mobile restructuring;
7. keyboard, touch, focus, screen reader, and reduced motion;
8. browser render and concept comparison.

Pass the pilot Gate before expanding. Do not finish a fleet of static pages and postpone interaction.

## 5. Implement Scene by Scene

For each approved scene or key state:

1. Build the first viewport at the concept's native dimensions when practical.
2. Capture the browser render and compare it with the matching concept.
3. Repair visible drift before moving to the next scene.
4. Verify downstream states and responsive continuation.
5. Update the fidelity ledger.

Preserve approved copy, hierarchy, density, palette, typography, spacing, radii, borders, shadow, image treatment, icon language, container model, and interaction model. Do not add unapproved components, decorative labels, fake metrics, gradients, overlays, or copy to make the screen feel “complete.”

## 6. Run the Fidelity Loop

Use the host browser or in-app browser first. Fall back to Playwright only when the primary browser capability is unavailable or unreliable, and record the reason.

In the same QA pass, inspect both the accepted concept and latest implementation screenshot with an image-inspection tool; in Codex, use `view_image`. Compare at least five concrete points spanning:

- exact copy and CTA hierarchy;
- layout, proportion, and first-viewport balance;
- typography and control chrome;
- palette, surface, border, shadow, and gradient treatment;
- icons and asset framing;
- spacing and container model;
- responsive restructuring;
- motion and real interaction states.

Capture at the concept's native viewport when practical. Record any blocker and still verify the actual target viewport.

Functional QA and fidelity QA are separate. Passing tests or clicking controls cannot replace screenshot comparison; a matching screenshot cannot replace real state and interaction verification.

## 7. Control Deviations

Classify each mismatch as **faithfully reproduced**, **intentional deviation**, or **missing**.

Fix accidental drift. Use intentional deviation only when product truth, usability, accessibility, performance, repository constraints, or new evidence requires it. Record the concept evidence, rendered evidence, reason, impact, approver, and downstream specification update.

If a functional change invalidates the concept, return to the earliest affected Gate. Do not force visual fidelity to an obsolete specification.

## Implementation & Fidelity Gate

Pass only when the representative slice and every completed scene have real browser evidence; concept and render were inspected together; at least five comparison points are recorded; core interaction updates real state; responsive, touch, keyboard, and reduced-motion paths work; and every material mismatch is fixed or explicitly decided.
