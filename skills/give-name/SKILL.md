---
name: give-name
description: >
  Deliberate naming for companies, brands, products, services, projects,
  repositories, packages, websites, communities, publications, events, and
  naming systems. Use when creating names, expanding naming directions,
  comparing or validating candidates, developing Chinese/English counterparts,
  or explaining a chosen name. Not for routine code identifiers such as local
  variables or database columns.
license: MIT
---

# Give Name

Give a thing a name it can grow into. Treat naming as a decision, not a word
dump: understand the subject, explore distinct territories, separate generation
from evaluation, and verify reality before recommending a winner.

## Load Rules

- For a full naming run, read `references/creative-territories.md` and
  `references/evaluation.md`.
- For comparing existing candidates, read `references/evaluation.md`; also read
  `references/clearance.md` when the name will be public or long-lived.
- For a public, discoverable, or commercial name, read
  `references/clearance.md` before making a final recommendation.
- For Chinese/English counterparts or any cross-language work, read
  `references/cross-language.md`.
- For a tiny internal codename, use this file only unless the user asks for
  research or validation.

## Choose the Branch

- **Create**: run the complete workflow from Brief through recommendation.
- **Expand**: preserve the existing Brief, open new Territories, and stop at a
  fresh longlist unless the user also asks to choose.
- **Compare**: normalize the same evidence for every candidate, screen, and make
  the tradeoffs explicit.
- **Validate**: investigate one candidate's provenance, pronunciation,
  collisions, and relevant namespaces without inventing alternatives.
- **System**: design a naming family only after the parent identity and member
  roles are clear.
- **Explain**: verify provenance first, then write the origin story, tagline, or
  README copy for a name that has already been selected.

## Workflow

1. Lock the Brief.
   - Identify the Naming Subject: what is being named, where the name appears,
     who must say or type it, and how long it should last.
   - State the positioning or job in one sentence, the desired and rejected
     feelings, target languages/markets, existing parent names, and hard
     constraints such as package syntax, domain needs, length, or legal scope.
   - Rank the three criteria that matter most for this subject. Infer from
     available project evidence; ask only for an unknown that would reverse the
     direction.
   - Completion: the subject, audience, context, stakes, top criteria, and hard
     constraints are explicit, with consequential assumptions labeled.

2. Map the Landscape when the name is public or the user asks for research.
   - Use live research to find category patterns, close competitors, crowded
     word families, and conventions worth following or breaking.
   - Treat competitor names as boundary evidence, never as a style template.
   - Completion: the exploration zones and avoid zones are clear before names
     are generated.

3. Open Territories.
   - Read `references/creative-territories.md`.
   - Build 4-7 semantically distinct Territories for a public or deep naming
     task; use fewer for a lightweight internal name.
   - Tie every Territory to the Brief and give it a different image world or
     construction strategy. A synonym list is one Territory, not many.
   - Completion: each Territory states its promise, imagery, construction
     moves, and failure mode, and none duplicates another.

4. Build the Longlist before judging it.
   - Generate within each Territory independently. For a public or commercial
     task, reach at least three structurally distinct viable candidates per
     Territory before evaluation; use 20 or more raw candidates in deep mode.
   - Record each candidate's Territory, construction type, provenance class,
     intended pronunciation, and one-line rationale.
   - Do not announce a favorite while generating. Show the user the useful
     range, not every discarded fragment.
   - Completion: every selected Territory has been explored and no repeated
     root, suffix, or fashionable naming pattern dominates the longlist.

5. Run the Kill Screen.
   - Read `references/evaluation.md`.
   - Remove candidates with subject mismatch, likely reading or spelling
     failure, false provenance, unwanted meaning, category imitation,
     restrictive scope, or an obvious live collision.
   - Keep a compact reject log. Do not rescue a weak name with a long story.
   - Completion: every survivor passes all hard gates; unknowns remain labeled
     instead of being scored as safe.

6. Preflight the provisional Shortlist.
   - Read `references/clearance.md` and search only as deeply as the subject's
     stakes require.
   - For coined names, distinguish intended pronunciation from likely first
     readings. For cross-language names, apply `references/cross-language.md`.
   - Timestamp dynamic evidence. Never equate an empty exact-match search with
     availability or legal clearance.
   - Completion: each finalist is labeled `no obvious blocker`, `crowded`,
     `blocker`, or `unknown`, with evidence and scope.

7. Recommend with tradeoffs.
   - Return one lead and up to two alternatives that represent meaningfully
     different choices, not spelling variants.
   - Explain what each gains and sacrifices against the ranked Brief criteria.
   - Include pronunciation, provenance, fit, risk, realistic written forms,
     and the next validation step. Use a weighted score only when the Brief
     supplies meaningful weights; never hide judgment behind fake precision.
   - Completion: the user can choose, reject a Territory, or request another
     round without reconstructing the reasoning.

## Rules

- Separate **source** from **story**. Say `derived from` only for an attested
  derivation; otherwise say `inspired by`, `coined from`, or `brand-assigned`.
- No naming style is universally superior. Descriptive, suggestive,
  metaphorical, arbitrary, and coined names trade clarity, distinction,
  extensibility, and protectability differently.
- Foreign roots do not automatically make a name premium, technical, or
  tasteful. Verify the language and use it only when the Brief earns it.
- A Chinese counterpart is not automatically a translation. It may be a direct
  carryover, transliteration, semantic rendering, phono-semantic recreation, or
  independent parallel name.
- Record the user's likes and dislikes as evidence. Taste is part of the Brief,
  not noise to average away.
- Write the polished origin story or naming system only after selection unless
  the user explicitly asks to explore those artifacts early.

## Output

For a full run, return:

1. Brief and consequential assumptions
2. Landscape and avoid zones when researched
3. Territory map
4. Shortlist with provenance, pronunciation, rationale, and risk
5. Lead recommendation plus distinct alternatives
6. Reject log and next validation steps

For Compare, Validate, System, or Explain branches, return only the sections
needed for that branch.
