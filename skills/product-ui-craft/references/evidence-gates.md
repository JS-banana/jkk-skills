# Artifacts, Evidence, and Release Gates

Use Gates to prevent unverified assumptions from spreading downstream. Persist decisions using the project's existing documentation conventions; do not impose fixed filenames or templates.

## 1. Minimum Artifact Set

| Gate | Required artifact | Passing evidence |
|---|---|---|
| Product Truth | Users, jobs, states, data sources, primary flow, trust boundaries, P0s, assumptions, unknowns | Page responsibilities exist, the flow closes, and P0s have decisions |
| Experience Architecture | Scene map, state matrix, desktop/mobile low-fi, CTA and long-content paths | Low-fi is approved and key states are covered |
| Art Direction | Narrative axis, visual tokens, signature material, image manifest, calibration concepts | Calibration is approved and implementation paths are credible |
| Motion & Assets | Motion state contracts, prototype decisions, technology choices, asset ledger | Events, fallback, touch, performance, and loading are verifiable |
| End-to-End Pilot | Representative implementation, browser evidence, fidelity ledger | Full state/input coverage passes and every difference has a decision |
| Scene Rollout | Per-scene implementation, responsive, accessibility, and comparison evidence | Each scene closes its complete loop |
| Release | Acceptance matrix, test output, console/network/performance evidence, final ledger | No unresolved release blocker remains |

Record status, last verification time, source evidence, decision owner, and downstream dependencies. Resume from these artifacts and the current diff, not from conversational memory alone.

## 2. Concept-to-Implementation Fidelity Ledger

Classify every material composition, surface, state, and interaction as:

- **Faithfully reproduced:** implemented with a page/state/browser evidence pointer;
- **Intentional deviation:** changed for function, usability, accessibility, performance, or new evidence, with reason, impact, and approver;
- **Missing:** not implemented, with user impact, owner, action, and target Gate.

Do not use “roughly matches” as a status. Visual similarity with incorrect state is not faithful reproduction. Correct behavior built from an invalidated concept requires an intentional-deviation decision and a specification update.

## 3. Separate Build from Verify

Build provides implementation, self-check commands, and known differences. Verify returns to the real entry point:

1. Start the real application and record version, branch, and build source.
2. Run the complete primary flow, including waiting, failure, and recovery.
3. Inspect visible state, URL/persistence state, network, console, and command output.
4. Compare against architecture, concepts, motion contracts, and the fidelity ledger.
5. Return a Gate decision: pass, revise, or accept deviation.

One person may hold both roles, but Verify must collect fresh evidence. “I implemented it” is never acceptance evidence.

## 4. Browser Acceptance Matrix

Cover at least:

- desktop, 375px mobile, and any structurally meaningful intermediate width;
- empty, input/edit, waiting, partial success, completion, error, retry, back, and refresh recovery;
- short, long, multiple, and empty data;
- pointer, keyboard, touch, visible focus, and reduced motion;
- console errors, failed requests, resource size, conditional loading, and cache behavior;
- horizontal overflow, clipping, hit targets, scroll lock, stacking context, and safe areas;
- heading hierarchy, semantic controls, labels, errors, color contrast, and non-motion feedback;
- the project's performance budget and target devices.

Keep reviewable screenshots, recordings, test output, or network evidence labeled by scene and state. A polished idle screenshot does not prove interaction quality.

## 5. Trace Feature Changes to the Earliest Invalid Gate

Ask in dependency order:

1. Did the product promise, user job, state, or data truth change?
2. Does the scene, CTA, sequence, and recovery architecture still hold?
3. Do the visual material, density, and concepts still express the job?
4. Do motion contracts and assets still map to real events?
5. Do implementation, tests, and the acceptance matrix cover the change?

The first “no” is the earliest invalid Gate. Record affected downstream artifacts and unaffected artifacts with preservation reasons. Rebuild only what depends on the change.

## 6. Release Decision

State the passing scope, verification environment, raw evidence, accepted deviations, deferrals, and remaining risk. Resolve every **missing** item by completing it, explicitly deferring it outside this release, or removing the affected promise.

Declare complete or release-ready only when tests, browser evidence, the fidelity ledger, and the real primary flow agree.
