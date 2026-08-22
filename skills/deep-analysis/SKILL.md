---
name: deep-analysis
description: >-
  Analyze a bounded question that affects a current judgment or writing progress,
  using evidence-backed search by default: frame the claim, verify sources, compare
  explanations, and make a provisional judgment constrained by the evidence; optionally
  apply longitudinal and cross-sectional lenses. Suitable for implicit model invocation.
  Do not use for simple fact lookups, open-ended research, outlining, drafting, or publishing.
license: MIT
---

# Deep Analysis

Move a bounded question to the strongest judgment the current evidence can support. By default, search for and verify the facts that could change the answer. When the evidence does not close the question, deliver the boundary, competing explanations, and next action instead of filling the gap with fluent prose.

Follow the user's language for interaction and the final deliverable. Keep analysis contracts, adjudication states, source details, and technical identifiers precise in any language.

## Bound the question first

Establish a minimal analysis contract before investigating:

- **Core question**: state in one sentence what must be answered or judged; do not hide several conclusions inside a vague request to “analyze this”;
- **Intended use**: understand a mechanism, compare options, judge a claim, solve a problem, or prepare evidence for writing;
- **Scope**: define the subject, time, region, version, sample, operating conditions, and explicit exclusions;
- **Success criteria**: identify the one thing the user must be able to explain, distinguish, choose, predict, or confirm;
- **Evidence standard**: decide which claims require official material, original research, source code, data, experiments, real cases, or expert judgment;
- **Delivery boundary**: provide analysis, evidence, and judgment without choosing an article's position, title, structure, or prose.

When the question is broad but can be narrowed without changing the user's goal, reduce it internally to one answerable core question and list the necessary subquestions. Ask one necessary question only when different answers would materially change the analysis route; do not use clarification to avoid a boundary you can infer safely. If the request contains inseparable goals, or every plausible narrowing would change the user's goal, do not choose a subproblem on the user's behalf. Explain that the request is not yet suitable for this Skill, stop the analysis, and ask for a boundary or priority.

## Search by default; skip it only under strict conditions

Search even when the user did not explicitly ask for it. Claims about external facts, current state, conflicting sources, comparative data, causality, named people, or conclusions that could change with a new version require search and verification.

Obey an explicit instruction not to search, but do not let that constraint turn an externally dependent claim into a verified fact. Analyze only what the allowed material can support and record the missing external evidence in the deliverable.

Purely internal analysis may skip external search only when all of these conditions hold:

1. The user or caller defines a closed material boundary, such as specified text, code, data, or conversation;
2. The question asks only about the internal logic, structure, contradictions, reasoning, or relationships within that material;
3. The answer needs no external fact, current state, benchmark, or definition beyond the supplied material;
4. Every judgment can be traced back to that material.

If any condition is uncertain, search. When search is unavailable or a source cannot be accessed, record the tool and evidence gap; never describe an unsearched claim as verified.

## Run the claim-evidence loop

Map what is known, unknown, disputed, and dependent, then work on the highest-value gap that could change the answer:

1. Decompose the question into verifiable claims. Discover the field's terminology and leads, then trace consequential facts to their original primary source;
2. Deduplicate by original provenance. Syndication, summaries, repeated search results, and multiple reports citing the same material count as one source;
3. Mark each consequential claim as **verified, conditional, disputed, insufficient, or false**, and state what each source directly supports and does not support;
4. Check whether definitions, samples, time, region, versions, metrics, experimental settings, and operating conditions are genuinely comparable;
5. Actively seek counterexamples, failed cases, and competing explanations. Correlation, marketing material, one successful case, or consensus language does not establish causality or generality;
6. Use new evidence to support, refute, constrain, or eliminate explanations. Continue only with the highest-value remaining gap.

Match source quality to claim risk. Use official documentation, original papers, source code, primary data, regulations, standards, and first-party statements to establish facts. Use authoritative analysis and expert interviews for context. Use community material to discover terminology, cases, failure modes, and counterexample leads, but not as sole proof of a general claim.

## Cross-validate existing analyses only when asked

Read other reports or analysis packets only when the user explicitly requests cross-validation and specifies the inputs. Extract the claims that could change the core judgment, merge evidence by original provenance, and reopen the consequential primary sources. Distinguish factual conflict from scope or version conflict and from interpretive conflict, then adjudicate everything into one analysis packet using the same claim states. Report count, agent count, and agreement do not constitute independent evidence. Do not overwrite the input reports, vote across them, or concatenate their prose into the result.

## Apply longitudinal and cross-sectional lenses when useful

Use only the lenses that could change the core judgment; never force them to fill a report template. They may be used separately or together:

- **Longitudinal evolution**: trace the starting point, consequential turning points, institutional or technical changes, failures, and continuities that shaped the present. Separate documented sequence from a retrospective story that makes the outcome look inevitable;
- **Current cross-section**: compare relevant subjects on the same time slice. Align dimensions, versions, resources, incentives, metrics, and operating conditions before interpreting differences;
- **Cross-explanation**: use earlier choices to explain present differences, then use current cases and counterexamples to test whether the proposed historical mechanism still matters. Separate documented links, analytical inferences, and disputes instead of using slogans such as “first mover” or “the market chose it” as explanations.

When using one or more of these lenses, state why they matter, which comparison basis was aligned, and which path-dependent relationship remains unverified. Do not let them expand a bounded question into an exhaustive competitor report, future scenarios, or a grand narrative.

## Make a provisional judgment constrained by the evidence

A provisional judgment is allowed when the evidence is incomplete, but its strength must match the support:

- State a clear conclusion for the part directly supported by evidence;
- Qualify anything that holds only for a particular sample, version, period, or operating condition;
- When competing explanations cannot be eliminated, explain which one the evidence favors and why instead of presenting it as the only cause;
- Classify consequential missing evidence as insufficient or unknown, unresolved source conflicts as disputed, and unexecuted checks as unknown; record the precise blocker for each.

Keep the reasoning continuous: **claim → evidence → limitation → current judgment**. Repeated wording across sources, agreement among agents, and search ranking are not votes that upgrade a claim.

## Audit search sufficiency and stop on evidence

Do not use fixed source, round, or word counts as quality targets. Before finishing, verify that:

- Every claim capable of changing the answer has direct evidence with matching conditions, or a precise reason it could not be verified;
- The strongest counterexample or competing explanation was checked, and repeated provenance was not counted as independent confirmation;
- Currency, version, scope, and comparison conditions were aligned; source conflict was explained or explicitly preserved;
- Another search round would repeat material rather than change the judgment, boundary, or next action.

If the remaining gap requires new data, access, an experiment, code execution, or professional review, stop searching and record it as unverified. “Not found” is not “does not exist,” and a provisional judgment is not a settled fact.

## Add a writing-use gate when relevant

When the caller says the analysis will support writing, add four evidence-status groups:

- **Usable**: directly supported, correctly scoped facts, cases, data, or explanatory material;
- **Needs qualification**: support exists, but the statement must retain its time, sample, scope, conditions, source status, or uncertainty;
- **Do not use yet**: evidence is insufficient, conflict remains unresolved, support comes only from anecdotes or community signals, or the claim would imply unjustified causality;
- **Needs confirmation**: items that require the user to supply original material, firsthand facts, access, runtime results, or expert judgment.

These groups are an evidence gate, not an article outline. Do not select the author's position, design sections, draft publishable paragraphs, or make narrative decisions on the author's behalf.

## Isolate complex work without creating an agent swarm

By default, one lead agent completes the analysis. When the caller determines that the problem is complex enough to benefit from isolation, the lead agent may assign one bounded route that can advance independently to one isolated subagent. The subagent must not delegate further. Give it only the analysis contract, assigned route, allowed material, and acceptance criteria; do not disclose the preferred explanation. The subagent remains read-only and returns an auditable packet of claims, sources, and limitations rather than writing to a shared source of truth. The lead agent must reopen consequential sources, resolve conflicts, and own the integrated judgment. Concatenating reports is not verification.

## Deliver one analysis packet and persist only when asked

For a standalone invocation, return one self-contained analysis packet in the conversation and create no files. Persist only when the caller provides an explicit destination. Do not guess a directory, overwrite another file, or retain intermediate reports. If the destination is unavailable, report the blocker instead of silently choosing another path.

Let the question determine the packet's section order, but always include:

1. The core question, intended use, scope, and search or no-search decision;
2. The provisional answer and its judgment strength;
3. Consequential claims, evidence, limitations, and adjudication states;
4. Any selected longitudinal or cross-sectional lens, plus relevant cases, counterexamples, competing explanations, and applicability limits;
5. An explicit distinction among fact, inference, user observation, dispute, and unknown;
6. What was actually opened, searched, executed, or left unverified;
7. A source ledger with source class, title, publication date, access date, original URL, supported claim, and known limitation;
8. The highest-value remaining question and the exact next action most likely to change the judgment.
