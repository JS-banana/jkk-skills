---
name: find-gap
description: >
  Demand-signal mining for product discovery. Use when the user wants to
  collect or deep-dig user pain points from Reddit, Xiaohongshu, V2EX, forums,
  app/marketplace reviews (App Store, Shopify, WordPress, G2), feedback
  boards, complaints, paid services, or procurement; when screening or
  reviewing already-collected demand rows; or when preparing and writing
  demand rows to the Feishu Base through lark-cli.
license: MIT
---

# Find Gap

Find evidence-backed demand signals. A demand signal is not an idea, product
list, bug report, feature request, trend, or recommendation. It is a concrete
person or role, in a concrete scene, stuck on a job, with original evidence of
pain, workaround, cost, reaction, payment, or repeated demand.

## Load Rules

- Before collection or screening, read `references/source-map.md`,
  `references/acquisition-strategy.md`, and `references/evidence-gate.md`.
- When turning broad topics into search angles, read
  `references/easy-vibe-method.md`.
- Before platform commands, read `references/tool-commands.md`.
- Before preparing or writing Feishu rows, read `references/feishu-schema.md`.
- For quick review of already-collected rows, read only
  `references/evidence-gate.md` and `references/feishu-schema.md`.

## Workflow

1. Frame the batch.
   - Default target: inspect up to 30 candidates and keep 3-8 records.
   - Pick at least three source families unless the user narrows scope.
   - Include one Chinese mass-market or vertical source, one international
     source, and one money/workflow source when available.
   - For deep or general discovery, add one third-party direction or scale
     source when cheap: Product Hunt, trend pages, app rankings, downloads,
     procurement search, or job posts.
   - Choose the acquisition mode first: feed browsing, review mining, comment
     mining, paid workflow, procurement, alternatives, structured-demand
     boards, template census, or search probe.
   - State whether keyword search is primary or auxiliary for this run.
   - Watch for 需求方向 over-concentration: money/subscription signals cluster
     easily; if a batch skews to one direction, note it and plan a follow-up on
     under-covered categories. This is a soft guard, not a quota — never drop a
     strong signal just to spread categories.
   - Completion: target count, source families, acquisition modes,
     platform-native phrase families, fallback sources, and rejection bar are
     stated before collection.

2. Collect candidates.
   - Run `agent-reach doctor --json`, then choose available backends.
   - Use platform-native language. Do not translate query terms mechanically
     between Chinese and English.
   - Search or browse by people, scene, job, workaround, and pain language;
     avoid only searching product names.
   - Keep a short hit/miss note for queries and sources that failed or were too
     noisy.
   - Save long-running candidate lists under `/tmp/`.
   - Completion: every candidate has `source`, `title`, `url`, `reaction`, and
     a short raw excerpt.

3. Read original evidence.
   - Open every candidate URL before judging it.
   - For high-engagement posts, scan top comments or reviews; a comment can be
     the primary signal if it contains the stronger demand.
   - Reject unreadable or untraceable sources.
   - Completion: every kept candidate has original evidence and a source URL,
     not only a search result or model summary.

4. Apply the evidence gate.
   - Use `references/evidence-gate.md`.
   - Keep a rejected list with one-line reasons, and a parked list for
     candidates missing exactly one gate (shape in
     `references/evidence-gate.md`).
   - Completion: every kept record passes all hard gates and no one-vote
     exclusion applies.

5. Shape the demand record.
   - Reduce the evidence to this job sentence (canonical form in
     `references/easy-vibe-method.md`):
     `当___的时候，我想要___，以便于___。现在我只能通过___勉强完成。`
   - Write `原文内容` as natural Chinese evidence, not an analysis report and
     not headings such as `用户情况`.
   - Completion: the row makes clear who is stuck, where, on which job, current
     workaround, cost or reaction, and why it is productable.

6. Validate and write.
   - Prepare rows with `references/feishu-schema.md`.
   - Run `python3 scripts/run.py --input /tmp/find-gap-rows.json --existing /tmp/find-gap-existing.json --output /tmp/find-gap-feishu.json --report /tmp/find-gap-report.json`
     (`--existing` is the `+record-list` dump described in
     `references/feishu-schema.md`; it makes cross-run dedupe deterministic).
   - Before writing, reconcile against the live Base with `lark-cli base
     +field-list`: confirm every select value in your rows (来源平台, 需求方向,
     产品形态, 处理状态, 需求强度, 需求普遍性, 语言) exists in the Base's current
     options. The live Base is authoritative — add the missing option or fix the
     value first; never assume the documented enums still match.
   - For scheduled runs, write with `lark-cli` and verify record count and
     sample URLs. For review-only runs, stop at validated JSON.
   - Completion: accepted/rejected/duplicate-skipped counts are reported;
     written rows are verified or clearly marked as not written.

## Deep Mining Mode

When the user asks to deep dig or continue mining, batch by topic category:

1. Read `/tmp/find-gap-parked.json` if present and try to complete each
   parked candidate's missing gate before opening new sources.
2. Pick 3-4 categories from `references/source-map.md`.
3. Pick acquisition modes from `references/acquisition-strategy.md`.
4. Run native-language browsing or query probes across available source
   families.
5. Dedupe by URL or title, sort by engagement, then read originals.
6. Apply the evidence gate and write in batches of 5-8 rows.
7. After each batch, report what was kept, rejected, parked, written, and
   unavailable.

## Rules

- Cron is only a trigger. Source selection, filtering, analysis, field mapping,
  and prompts live in this skill.
- Ordinary users and real workflows come before developer-only sources.
- Trends, VC reports, and AI idea generators are direction sources only; never
  accept them without user/workflow evidence.
- Quality beats volume. Prefer a false negative over polluting Feishu.
- Do not hard-code Feishu Base tokens, table IDs, cookies, or auth state in the
  skill.

## Resources

- `references/easy-vibe-method.md`: first-principles demand model distilled from
  Easy-Vibe.
- `references/source-map.md`: source families, default mix, source roles, and
  deep mining categories.
- `references/acquisition-strategy.md`: acquisition modes, source reliability,
  native Chinese/English phrase families, and query hit/miss rules.
- `references/evidence-gate.md`: hard gates, exclusions, strength scoring, and
  translation rules.
- `references/feishu-schema.md`: Feishu fields and lark-cli write shape.
- `references/tool-commands.md`: verified platform command syntax.
- `scripts/run.py`: deterministic row validator and Feishu JSON generator.
