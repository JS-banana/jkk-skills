# Knowledge Pack Delivery

Read this reference after the research contract is clear and when integrating or reviewing the final delivery. It defines the human-facing delivery layer for `deep-learn`: profile inference, body/appendix responsibilities, the minimum-content rule, and the two completion gates. The parent `SKILL.md` remains authoritative for research governance, evidence work, read-only boundaries, and stop conditions.

## Infer the delivery profile

Infer one profile from the learning contract's intended use. Do not require the user to select a profile. If the request genuinely mixes uses, choose the profile that determines the highest-stakes decision and preserve the other use as a stated secondary constraint.

| Contract signal | Delivery profile | Optimize for |
| --- | --- | --- |
| The user wants to learn, explain, test, apply, or provide evidence to later writing | **Study Reference** | A transferable concept model: distinctions, mechanism, examples, counterexamples, vocabulary, evidence boundaries, and open questions that an upstream writer can use without inheriting an editorial position |
| The user must compare, select, adopt, configure, or judge a product, technology, method, or course of action | **Decision Dossier** | A decision model: the question, aligned options, criteria, operating conditions, trade-offs, failure modes, reversibility, unknowns, and the next check that could change the judgment |

The profile changes emphasis, not the evidence standard or the canonical-file rule. Neither profile drafts a downstream article, chooses its stance or title, or replaces professional review. A Study Reference may serve writing upstream, but the writer still owns editorial narrative. A Decision Dossier may clarify a decision, but it must not turn missing evidence into a recommendation.

### Decision Dossier safeguards

Before preferring or recommending a technical or product option:

- when a current system exists, ground the decision in its real input, interface, runtime or configuration, persistence or delivery, and target-environment chain. For a greenfield choice, use the intended workflow, constraints, and target environment instead. Do not replace project evidence with a generic market survey;
- separate solution layers such as product or service, wrapper, framework, runtime, model or asset, and license, then compare peers at the same layer before combining them into an end-to-end option;
- bind consequential candidates to the concrete version, artifact or asset, license, operating conditions, and directly matched evidence that the judgment requires; keep the option conditional when those facts remain unresolved;
- do not promote a new dependency, abstraction, or candidate to the default merely because it is plausible. First establish which material criterion the existing or built-in path fails; otherwise make the simpler baseline the first falsifiable check;
- pair a preferred path with acceptance, failure, and rollback or reconsideration conditions that can change the judgment.

Reader-oriented compression must not remove project facts, candidate provenance, or failure evidence that could reverse the decision. A focused dossier may omit peripheral history or catalogue breadth, but it must not become a shallow recommendation summary.

## Build one readable canonical file

The final artifact is one Markdown file. It is a continuous explanation for a human reader, with a compact audit appendix at the bottom. Intermediate digests, coverage maps, route registries, outlines, and agent reports are working material only; do not deliver them as parallel sources of truth.

Make the reader promise, scoped core answer, and knowledge map easy to find near the beginning, so the reader can see what they will get and where the explanation is going before detail. Combine or sequence them naturally for the topic; do not force a fixed opening-screen template. Then let the topic determine the order and transitions. The body should normally move through whichever of these are needed to make the answer usable:

- the native definitions and distinctions that prevent category errors;
- the mechanism, causality, or end-to-end behavior, including constraints and meaningful implementation detail;
- real cases or examples that make the mechanism concrete;
- important alternatives, counterexamples, failures, and applicability limits;
- transfer to a new situation, or criteria and trade-offs for a decision.

These are coverage responsibilities, not a mandatory heading sequence. Use continuous explanation when the reader needs to understand mechanism, causality, evolution, or a case. Use a flow, small diagram, or pseudocode only when it materially lowers the cost of understanding; do not generate decorative visual assets. Use tables only for strict aligned comparisons or matrices. Use bullets only for genuinely parallel items.

The body must not read like a route log, a sequence of subagent reports, or a source catalogue. Research can branch; understanding must converge. Do not expose the internal seven-step cognitive ladder as a fixed seven-section template, and do not let the order in which sources were found dictate the explanation.

## Apply the minimum cognitive increment

Keep a passage only when it advances at least one of these: a definition, a mechanism, a live question, evidence for or against a claim, a case, a connection between concepts, a transfer to a new situation, or a consequential boundary. Remove repeated conclusions, generic warm-up, research process narration, unexplained links or numbers, and peripheral encyclopedia material.

Peripheral material can be retained briefly when its omission would mislead: say why it is out of scope and, when useful, give a source or search entry point. Do not expand it into a second survey. A shorter pack is not the goal; the goal is that every retained passage changes what the reader can understand, distinguish, test, apply, predict, or decide.

## Keep evidence close without flooding the reader

Put a citation next to every high-impact fact, number, version, quotation, dated claim, or contested statement. When several consecutive sentences are supported by the same source and the scope is unambiguous, one citation can support the passage. Keep the full source ledger in the appendix so the body remains readable.

The ledger should preserve, for each consequential source, its class, title, publication date, access date, original URL, the claim or claims it supports, and the source's relevant limitation. Deduplicate syndicated copies by original provenance. Do not use a link, citation count, or source list as a substitute for explaining what the evidence establishes and what it does not.

## Internal delivery flow

Run this flow after discovery and integration. The intermediate artifacts stay internal:

`digest → coverage map → topic-native outline → fill → Evidence pass → Reader pass`

1. **Digest** the independent material into claims, evidence, mechanisms, cases, conflicts, and unknowns. Preserve provenance; discard report-shaped repetition.
2. **Coverage map** the core question against the concepts, mechanisms, cases, alternatives, boundaries, transfer or decision criteria, and the contract's evidence standard. Mark an omitted dimension and why it cannot change this answer.
3. **Topic-native outline** choose the explanation order a reader needs, not the research route order or the cognitive ladder order. Put dependencies before claims that rely on them.
4. **Fill** with integrated explanations and directly matched evidence. Make fact, inference, user observation, dispute, and unknown distinguishable in context.
5. **Evidence pass** run the Evidence Gate below. Reopen sources or execute safe, available checks for high-value gaps; return to the research loop if a claim cannot be supported or properly qualified.
6. **Reader pass** run the Reader Gate below. Repair missing explanation, jumps, repetition, and confusing order; if the problem is an evidence gap, go back to the relevant research gap rather than smoothing it over.

## Completion gates

Both gates must pass. Passing one does not compensate for failing the other.

### Evidence Gate

The pack passes when a reviewer can verify that:

- the learning contract, scope, core answer, and stop conditions are represented, including the exact blocker when the answer remains conditional;
- the coverage map addresses the central definitions, mechanism or causes, relevant current alternatives or historical transitions when material, strongest failure or counterexample, and scope conditions, or records why an item is omitted;
- every high-impact claim has directly matched evidence for its definition, sample, time, region, version, setting, and operating conditions, or is explicitly marked conditional, disputed, insufficient, or unverified;
- the leading explanation was attacked with a meaningful competing explanation, counterexample, failure case, or applicability test, and source conflicts are classified rather than silently reconciled;
- the appendix distinguishes what was actually reopened, inspected, executed, or merely inferred from static material, and records exact blockers that require new data, access, experiments, expertise, credentials, fees, devices, production actions, or a temporary test system;
- the source ledger is complete enough to trace consequential claims back to original provenance, and any proposed next action names the check most likely to change the judgment.

Safe, read-only, existing checks that can close a high-value gap should be run when practical. Do not invent a test harness, obtain new authority, spend money, use a real device, or touch production merely to make the gate look complete. Record the unclosed gap and its exact next action.

### Reader Gate

The pack passes when a reader at the stated starting point can:

- understand the opening promise, scoped answer, and knowledge map without reading the audit appendix first;
- learn each central concept before it is used as unexplained shorthand, see how the mechanism connects inputs, process, outputs, and constraints, and understand why the cases or evidence matter;
- distinguish the answer from its evidence, inference, user observation, dispute, and unknown without decoding a research-status dump;
- use the alternatives, failures, boundaries, and transfer or decision criteria to explain, test, apply, predict, or decide within the stated scope;
- follow one continuous topic-native explanation without route chronology, duplicated conclusions, generic warm-up, unexplained links or numbers, or an encyclopedia detour;
- finish with a minimal useful closure and, when one exists, the highest-value next action, rather than a mechanical repetition of every audit status.

If the Reader Gate fails while the Evidence Gate passes, rewrite the explanation and order without changing the claims. If the Evidence Gate fails, return to the relevant research gap; never use prose polish to conceal missing evidence.

## Compact audit appendix

Place the appendix after the human-facing explanation. Keep it compact and combine fields where that improves scanning. It should make the following auditable without duplicating the body:

- the complete learning contract and inferred delivery profile;
- consequential claim states and their supporting or limiting evidence when a separate audit view improves traceability;
- actual source reopenings, code/data/runtime inspections, executions, and unverified items;
- relevant route entries only when a conflict, blocker, reopening, or lack of independence changes interpretation, evidence strength, or the next action; omit ordinary route and subagent status;
- the source ledger;
- remaining material unknowns, exact blockers, and next actions that could change the result.

Do not force each item into a separate heading. The appendix is an audit surface, not a second narrative or a place to preserve rejected routes.

Optional further reading is selective and has no fixed count. Include it only when it materially helps the reader extend the model or perform the next action; label why each item is worth opening.
