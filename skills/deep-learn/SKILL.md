---
name: deep-learn
description: >-
  Manual-only deep research workflow for systematically learning an unfamiliar topic, technology, product, mechanism, research question, or source packet. Use only when the user explicitly invokes $deep-learn and wants more than a single Web search: independent research routes, subagent collaboration, primary evidence, real cases and failures, adversarial verification, a transferable knowledge model, clear boundaries, and unresolved unknowns. Do not use for quick fact lookup, article drafting, choosing an editorial stance, or replacing professional review.
license: MIT
disable-model-invocation: true
---

# Deep Learn

Turn an unfamiliar subject into a knowledge model the user can explain, test, apply, and extend. Do not measure completion by source count or agent consensus. Finish when the core questions have reliable answers, the evidence boundaries are explicit, and the resulting understanding transfers to new situations.

Follow the user's language for interaction and the final deliverable. Keep research instructions, route contracts, evidence states, and technical identifiers precise even when the user works in another language.

## Preserve the boundary

- Handle learning, research, evidence verification, cognitive modeling, and unknown management.
- Do not draft the article, choose its position, design its narrative, or publish it. Downstream work may use the adjudicated knowledge pack, not unreviewed intermediate reports.
- Do not treat one agent's search summary as deep research or several agents repeating the same source as independent confirmation.
- Work read-only by default. Unless the user explicitly requests persistence, deliver in the conversation. When a host project specifies a destination, write only the final knowledge pack and do not persist subagent reports.

## Establish the learning contract

Before searching, derive these fields from the request and available local material:

- **Core question**: what must be understood or decided;
- **Intended use**: learning, technical selection, product judgment, problem solving, or upstream support for writing;
- **Starting point**: what the user already knows, tried, or observed;
- **Success criteria**: what the user should be able to explain, distinguish, apply, predict, or decide;
- **Scope**: inclusions, exclusions, time, region, version, population, and operating conditions;
- **Evidence standard**: which claims require primary documents, source code, data, experiments, or real cases;
- **Stop conditions**: what closes the evidence loop and what must wait for new data, access, experiments, or expertise.

Keep the user's experience and intuitions as motivations or observations to test. Do not promote them to facts. If the contract is sufficiently clear, proceed. Ask one necessary question only when different answers would materially change the research portfolio.

## Select the research intensity

- Use **focused research** when the question is narrow, authoritative sources are concentrated, and there are no independent evidence mechanisms. The lead agent completes the full evidence loop.
- Use **portfolio deep research** when the subject is unfamiliar, spans multiple mechanisms, depends on real cases, contains source conflict, or the user explicitly requests systematic multi-angle or subagent research. Prefer this mode when at least two high-value routes can advance independently.

Do not start subagents to simulate effort. When the host cannot use subagents, execute the routes sequentially and state that the exploration was not independently parallelized.

## Design the research portfolio

First map what is known, unknown, disputed, and dependent. Design routes around unknowns that could most change the answer. Separate routes by **reasoning or evidence mechanism**, not by website, keyword, or desired wording.

Possible route families include, but are not limited to:

- definitions, history, and authoritative facts;
- mechanism, causality, and end-to-end system behavior;
- source code, data, experiments, or runtime evidence;
- real adoption, successful cases, and failed cases;
- alternatives, counterexamples, disputes, and applicability limits;
- correspondence between the user's observations and external evidence.

Maintain a lightweight route registry:

| Field | Meaning |
| --- | --- |
| Route family | Distinct mechanism or evidence type |
| Core question | High-value unknown this route must reduce |
| State | active / stalled / blocked / supported / falsified |
| Concrete artifact | Primary source, data, code, experiment, case, counterexample, or model |
| Largest gap | Critical premise still unsupported |
| Reopen condition | New mechanism or evidence that would justify another round |

Merge routes that are substantively identical and redirect capacity toward underexplored mechanisms. A polished reformulation that stops at the same hard premise is not progress.

## Orchestrate independent discovery

Keep discovery routes independent during their first pass:

- Give each subagent only the learning contract, its assigned route, allowed inputs, and acceptance criteria.
- Do not reveal the favored explanation, expected conclusion, or findings from other routes.
- Assign only bounded routes that can advance independently and require an auditable research packet.
- Keep subagents read-only and have them return results by message. Do not let them write to the shared source of truth.
- Do not assume subagents inherit this Skill. Pass the route contract and acceptance packet explicitly in each assignment.
- The lead agent must own the integrated model, cross-route relationships, and at least one highest-value gap. Never act as a report concatenator.

Require every route packet to contain:

1. the route and question;
2. consequential claims with direct primary sources;
3. what each source supports and does not support;
4. counterevidence, failures, conflicting sources, and applicability limits;
5. a distinction among confirmed, inferred, disputed, and unknown;
6. the exact point where searching or execution stalled;
7. the precise next action most likely to change the overall judgment.

Reject unsupported status prose, vague optimism, unannotated source lists, and claims such as “the industry generally agrees.”

## Run the claim-evidence loop

Integrate evidence rather than report prose:

1. Extract the claims that could change understanding or a decision.
2. Deduplicate by original provenance. Syndication and repeated agent citations count as one source.
3. Mark each claim as verified, conditional, disputed, insufficient, or false.
4. Check whether definitions, samples, time, region, version, test settings, and operating conditions actually match.
5. Use new evidence to support, refute, constrain, or eliminate explanations.
6. Launch the next round only for the highest-value remaining gap.
7. Reopen a stalled or blocked route only when new data, mechanisms, tools, access, or experiment designs become available.

Prefer official documentation, original papers, source code, primary datasets, regulations, standards, and first-party statements for consequential facts. Use expert analysis for context. Use community material to discover terminology, cases, failure modes, and counterexample leads, but not as sole proof of generality.

For technical or product research, verify the real chain separately: documentation claims, source capability, build or configuration, runtime behavior, persistence or delivery, and the target user environment. Automated tests, vendor demos, and isolated success cases do not establish universal behavior.

## Apply an independent verification gate

After the leading explanation stabilizes, separate verification from discovery:

- Have a verifier reopen high-impact primary sources rather than trusting agent summaries.
- Attack the strongest current explanation. Check circular support, hidden conditions, common provenance, proxy metrics, selection effects, and causal leaps.
- For implementation claims, inspect code, data, experiments, or the target runtime when possible. Label static inspection and unexecuted claims honestly.
- Classify source conflict as factual, scope, version, or interpretation conflict.
- Preserve unresolved questions as unknowns. Do not fill them with consensus language or fluent prose.

For medical, legal, financial, safety-critical, or publishable academic conclusions, require the appropriate expert, formal standard, real-world data, or peer review. This workflow does not replace professional judgment.

## Build transferable understanding

Do not stop at source summaries. Build a cognitive ladder around each central concept:

1. **Definition**: what it is and how it differs from adjacent concepts;
2. **Motivation**: what problem requires it;
3. **Mechanism**: how inputs, process, outputs, and constraints connect;
4. **Example**: how a real case exhibits the mechanism;
5. **Counterexample**: where the intuitive explanation fails;
6. **Transfer**: how the model predicts or explains a new situation not copied from a source;
7. **Boundary**: what remains conditional, disputed, or dependent on expert judgment.

If the model cannot explain the mechanism, predict a new case, or name its failure conditions, return to the evidence loop instead of polishing the prose.

## Deliver one knowledge pack

Return one self-contained Markdown knowledge pack. Let the question determine its section order, but always include:

- the learning contract;
- a scoped answer to the core question;
- the concept model or dependency ladder;
- consequential claims, evidence, and adjudication state;
- real cases, failures, counterexamples, and applicability limits;
- explicit separation of fact, inference, user observation, dispute, and unknown;
- what was actually reopened, inspected, executed, or left unverified;
- a source ledger;
- the remaining high-value questions and exact next actions.

Place clickable citations next to facts, data, quotations, and dated claims. In the source ledger record source class, title, publication date, access date, original URL, supported claim, and known limitation.

Respect an upstream project's required path and format, but keep the knowledge pack independent of personal profiles and private project context. Do not retain route reports, chat transcripts, or rejected conclusions as parallel sources of truth.

## Stop on evidence, not activity

Do not use fixed source, agent, round, or word counts as quality targets. Stop when all of these are true:

- the core question has a scoped answer, or the exact reason it cannot yet be answered is established;
- the central concepts can be explained, distinguished, and transferred to a new case;
- high-impact claims have direct evidence;
- the strongest counterexamples, failure conditions, and competing explanations were tested;
- source conflicts were explained or explicitly preserved;
- another round would add repeated material without changing the knowledge model;
- remaining gaps require new data, experiments, access, or expertise rather than more language inference.

End by distinguishing what this run confirmed, inferred, disputed, and did not verify, followed by the user's highest-value next action.
