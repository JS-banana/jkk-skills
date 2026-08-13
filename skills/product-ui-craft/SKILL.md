---
name: product-ui-craft
description: Orchestrate product truth, experience architecture, art direction, motion, assets, faithful frontend implementation, and browser evidence as one traceable experience spine. Invoke manually for greenfield products, application redesigns, or feature changes that may invalidate approved UX or visual work.
disable-model-invocation: true
license: MIT
---

# Product UI Craft

Build visual quality on top of a product that is useful, trustworthy, and finishable. Treat the current UI as evidence, not a boundary; treat concept art and code as revisable downstream artifacts, not as product truth.

Communicate and write project artifacts in the user's language. Preserve exact product UI copy. Use canonical English design and engineering terms when translation would blur meaning.

## Operating Rules

- Follow this dependency order: **Product Truth → Experience Architecture → Art Direction → Motion → Assets → Implementation → Verification**.
- Treat product facts and approved decisions as the authority. Reopen the earliest invalidated Gate when new evidence appears.
- Persist every Gate's inputs, decision, unknowns, accepted deviations, and next action. Resume from those artifacts and the current diff.
- Interpret an Awwwards-level ambition as a coherent product world, a memorable interaction idea, strong hierarchy, meaningful motion, and agency-grade finish—not as more decoration, more animation, or more empty space.
- Advance only to the next decision Gate. Do not present downstream work as approved while an upstream Gate is unresolved.
- Read [references/evidence-gates.md](references/evidence-gates.md) whenever opening or closing a Gate, verifying a build, or declaring release readiness.

## Choose the Entry Point

### Greenfield

Start from the product promise, user jobs, state model, data sources, and trust boundaries. Do not start with style, components, or hero composition.

### Redesign

Run the real product first. Read user feedback, code, assets, and authoritative documents. Preserve verified constraints; redesign structures that obstruct the job.

### Change

Trace the change through **Product Truth → Architecture → Art Direction → Motion → Assets → Implementation**. Reopen the earliest invalidated Gate and update only affected downstream artifacts. Preserve everything still supported by evidence.

At the start, state the entry point, current role, target Gate, known facts, assumptions, and unknowns. Use one role at a time:

- **Design** — produce an architecture, direction, or contract for approval.
- **Build** — implement approved artifacts without silently changing product decisions.
- **Verify** — re-run the product and inspect raw evidence; do not accept Build's self-report as proof.
- **Gate** — summarize evidence and request approve, revise, or explicitly accept a deviation.

## 1. Product Truth Gate

Define the user, context, primary job, inputs, outputs, states, data sources, waits, errors, recovery, completion path, and trust boundaries. Treat these as P0:

- incomplete functionality, dead ends, or an undiscoverable next step;
- certainty claims that exceed available evidence;
- hidden progress, failure, recovery, or data provenance;
- unusable long content, multi-item input, or return-state management;
- pages or states without a real responsibility.

Label unknowns as **unverified** and temporary choices as **assumptions**.

**Pass when:** every page and key state has a real responsibility; the core flow closes; trust failures and P0 gaps have decisions; assumptions and unknowns are visible.

## 2. Experience Architecture & Low-Fidelity Gate

Give each independent scene one primary job, one primary CTA, entry and exit conditions, and an information hierarchy. Cover:

- desktop, mobile, and any breakpoint where structure changes;
- empty, input, waiting, partial success, error, complete, and refresh recovery;
- keyboard, touch, long content, and multi-item management;
- back, retry, cancel, resume, and next-step discovery.

Every area of whitespace must serve focus, separation, or a motion field. Reassign unowned space to content, controls, or state feedback.

**Pass when:** the complete flow, state matrix, responsive paths, and primary CTA hierarchy are approved. Do not enter high-fidelity concept generation before approval.

## 3. Art Direction & ImageGen Gate

Read [references/art-direction.md](references/art-direction.md). Derive a narrative axis and signature interaction material from the product's positioning, user mental model, real data, and interaction jobs. Never reuse another product's cultural symbols, materials, or compositions as defaults.

Publish the image manifest and total count first. Create one image per independent scene or key state. Generate only 1–2 representative calibration concepts before expanding to remaining desktop scenes, keyframes, and structurally distinct mobile views.

**Pass when:** shared visual tokens and product-specific materials are locked; representative concepts are approved; every remaining image has a defined job, state, real content, and interaction implication. Treat concept images as production specifications, while keeping runtime UI code-native.

## 4. Motion Contract & Asset Gate

Read [references/motion-and-assets.md](references/motion-and-assets.md). Classify each expressive element as:

- **Product data** — must truthfully represent business state;
- **Interaction metaphor** — explains operation or state change;
- **Decorative material** — creates atmosphere without pretending to be system truth.

Define idle, trigger, process, completion, failure, recovery, touch, and reduced-motion branches for every key motion. Map waiting feedback to real events, streamed output, or an explicit system activity.

Choose the lowest sufficient technology: CSS → DOM/SVG/framework state → motion library → Canvas → WebGL. Prototype high-risk effects before production.

Produce runtime assets only after motion direction is approved. Keep concept images, motion keyframes, and runtime assets separate.

**Pass when:** key states have honest motion contracts; technical choices have evidence; risky prototypes have a decision; the asset ledger records purpose, loading, fallback, performance, rights, and ownership.

## 5. End-to-End Pilot Gate

Read [references/implementation-and-fidelity.md](references/implementation-and-fidelity.md). Select one representative scene that combines core structure, real state changes, and the signature material.

Before coding, extract the accepted concepts into an implementation contract: exact copy, tokens, typography, icons, component families, container model, assets, responsive behavior, motion contracts, and core interactions. Use the host's frontend-app-builder capability when available; in Codex, prefer Frontend App Builder as the implementation executor. The executor does not own product or design decisions.

Implement the representative scene end to end: real content, real state-driven motion, responsive layout, keyboard, touch, reduced motion, error, retry, and recovery. Compare the accepted concept with the browser render and classify every material difference as **faithfully reproduced**, **intentional deviation**, or **missing**.

**Pass when:** the scene works in a real browser, concept-to-render comparison is complete, and every difference has a decision. Expand only after this pilot passes.

## 6. Scene-by-Scene Build + Verify

Close the same loop for each scene: structure → content → material → real state motion → responsive behavior → accessibility → browser comparison → fidelity ledger.

Build reports implementation and self-checks. Verify independently re-runs the application, core workflow, network, console, responsive states, and visual comparison. Follow [references/implementation-and-fidelity.md](references/implementation-and-fidelity.md) for the concept-to-code loop and [references/evidence-gates.md](references/evidence-gates.md) for acceptance evidence.

## 7. Dynamic Feedback Loop

When a feature, user report, or runtime observation changes, record:

1. Which product fact or approved decision changed?
2. What is the earliest invalid artifact?
3. Which downstream architecture, concept, motion, asset, implementation, and test artifacts depend on it?
4. Which artifacts remain valid, and why?
5. Who must approve the update, and what evidence will close it?

Reopen only the earliest invalid Gate and its affected downstream work. Do not restart everything or force an obsolete concept onto the product.

## 8. Release Gate

Use [references/evidence-gates.md](references/evidence-gates.md) to assemble release evidence. Cover desktop, 375px mobile, necessary intermediate widths, pointer, keyboard, touch, reduced motion, error, recovery, and the complete primary flow.

Resolve every **missing** item by completing it, explicitly deferring it outside the release scope, or removing the affected promise. Declare complete or release-ready only when the real product, tests, browser matrix, fidelity ledger, and approved deviations agree.
