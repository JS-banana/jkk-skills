---
name: find-bounty
description: >
  Use when finding, screening, recording, or reminding about AI/vendor developer
  campaigns: hackathons, challenges, credits, beta incentives, data contests,
  feedback rewards, content rewards, user-forwarded campaign notices, or Hermes
  cron AI activity radar scans.
license: MIT
---

# Find Bounty

Find actionable AI and developer campaign opportunities. This is not AI news
monitoring; it only keeps opportunities that a person can enter, claim, submit,
or register for, with a concrete reward and a direct link.

## Load Rules

- Before any public scan, read `references/source-registry.md`,
  `references/keyword-clusters.md`, `references/tool-fallbacks.md`, and
  `references/agentdeadlines-guide.md`.
- Before writing, validating, or debugging Feishu Base data, read
  `references/bitable-api-patterns.md` and treat the live Base as the source of
  truth.
- Before changing cron behavior, read `references/cron-architecture.md`.
- Before changing MCP/search setup, read `references/mcp-enhancement.md`.
- For a user-forwarded notice, read only `references/bitable-api-patterns.md`
  unless the notice needs web verification.

## Scan Integrity Rules (hard gates, do not skip)

These rules prevent silent coverage gaps. If any rule cannot be met, report the
reason in `【未覆盖】` — never silently skip.

1. **Structured endpoints first, in one call.** Run `scripts/collect_structured.py`
   to batch-fetch AgentDeadlines + Devpost + CompeteHub (双月) + aihot in a single
   tool call. Do not curl each source individually.

2. **Community signals are mandatory.** Run `agent-reach doctor --json` before
   any community queries. Query at least ONE Chinese community source AND ONE
   English community source per scan. If agent-reach is unavailable, use
   DDG/web_search as fallback — but never skip this step entirely.

3. **At least one broad discovery query.** Run `broad_zh` OR `broad_en` every
   daily scan (see `references/keyword-clusters.md`). This catches domestic
   events that aggregators miss (外滩大会, WeaveFox, 小红书黑客松, etc.).

4. **Devpost pagination: stop at 2 pages in daily scan.** The filter
   `themes[]=Machine Learning/AI` + `status[]=open` limits results to ~30.
   Pages 3+ add diminishing returns; save them for weekly deep scans.

5. **aihot failure is not silent.** If `collect_structured.py` reports aihot
   extraction failed, try Jina Reader (`r.jina.ai`) before marking it uncovered.

6. **Expired candidates must be filtered.** Any deadline < today (UTC) is
   expired. Reject before scoring. If deadline is ambiguous, verify — do not
   assume expiry from publish date.

## Opportunity Gate

Keep only opportunities that pass all hard gates:

1. The user can participate, apply, submit, claim credits, or register.
2. The reward is explicit: cash, credits, membership, beta access, official
   incentive, certificate, physical prize, or meaningful exposure.
3. A direct entry, registration, claim, rules, or official detail URL exists.
4. The source is official, a recognized platform, or cross-checkable.
5. The deadline is open, ongoing, or explicitly long-term.

Allowed types: `Hackathon`, `开发者挑战赛`, `开发者激励`, `AI竞赛`, `内测体验`,
`福利发放`, `内容创作`, `其他`.

Reject: invite/referral campaigns, simple repost/share tasks, vague prize posts,
news without an action, unofficial reposts without confirmation, closed
university-only contests, and local offline-only events unless the reward is
exceptional.

## Workflow

1. Frame the run.
   - Choose one mode: daily scan, weekly deep scan, user-forwarded notice,
     active query, or deadline reminder.
   - Choose source roles before queries: discovery, community signal, official
     confirmation, or reminder state.
   - Set the scan budget. Default daily scan: AgentDeadlines first, then 4-6
     high-value searches, then inspect only the best 2-4 candidates.
   - Completion: mode, date/timezone, source mix, write expectation, and stop
     rule are stated.

2. Read live state.
   - For writes or schema-sensitive work, run `lark-cli base +field-list` on the
     Base in `references/bitable-api-patterns.md`; live fields beat cached docs.
   - Read the seen JSONL before dedupe. In Hermes cron, keep the first
     `read_file` result in memory and rewrite the full file with `write_file`;
     do not use `execute_code` or shell append.
   - Completion: field contract, seen baseline, and any schema drift are known.

3. Collect candidates (three mandatory phases, in order).

   **Phase A — Structured endpoints (1 call):**
   Run `scripts/collect_structured.py`. This fetches AgentDeadlines,
   Devpost (auto-paginated), CompeteHub (current + next month), and
   aihot.today (with Jina fallback) in parallel. Save the JSON output.
   Do not curl individual sources — use this script.

   **Phase B — Community signals (2-3 calls, mandatory):**
   - Run `agent-reach doctor --json` first. Note which backends are active.
   - Query at least ONE Chinese source: OpenCLI xiaohongshu if active, or
     linux.do JSON API, or V2EX API.
   - Query at least ONE English source: OpenCLI reddit if active, or X/Twitter
     if authenticated, or HN Algolia API.
   - If agent-reach is unavailable, use DDG `site:` queries as fallback.
     Never skip this phase — report missing backends in 未覆盖.

   **Phase C — Broad discovery (1 call, mandatory):**
   Run `broad_zh` or `broad_en` (rotate daily). These catch domestic
   events (外滩大会/WeaveFox/小红书) and niche international ones that
   aggregators miss.

   User-forwarded notice: skip phases B-C; only verify the forwarded URL.
   Deadline reminder: read existing Base records, verify status, notify.

   Completion: every candidate has source, title, URL, reward, deadline or
   long-term status, and raw evidence.

4. Gate, dedupe, and score.
   - Reject before scoring when a hard gate fails.
   - Dedupe by normalized vendor + campaign name + URL against seen JSONL and
     Base records. With multiple aggregators live, the same campaign appears
     under different titles and vendor spellings; the entry URL is the primary
     duplicate signal, and the sync script hard-blocks writes whose normalized
     报名入口 already exists in the Base. Name-based comparison only catches
     what URL matching cannot (same campaign listed under different entry
     URLs — Devpost, lablab, and vendor sites overlap the most).
   - Score `推荐指数` from 1-5 by averaging reward value, urgency, and official
     confirmation. Difficulty stays separate in `难度评级`.
   - Never drop a candidate silently. A candidate set aside for scan budget,
     assumed expiry, pagination limits, or extraction failure is not a
     rejection: track it for the 未覆盖 section in the output. Assumed expiry
     alone never justifies dropping — a post's publish date is not the
     campaign's deadline; verify the deadline or list the candidate as 未覆盖.
   - Completion: every kept and rejected candidate has a one-line reason.

5. Persist.
   - Write new records through `campaign_bitable_sync.py --write`; do not call
     Feishu record APIs directly unless the user explicitly asks and live fields
     have been checked.
   - Pass `vendor`, `campaign`, `seen_at`, `score`, and `url`; add only verified
     optional Base fields. Never pass `活动详情链接`: the live Base does not have
     that field.
   - Append to seen JSONL by rewriting the whole file in Hermes cron.
   - Completion: record write is `OK` or explicitly skipped, and seen JSONL is
     updated or the reason is reported.

6. Output.
   - If there are no new records, no P0/P1 reminders, and no 未覆盖 entries,
     output exactly `[SILENT]`.
   - Otherwise output compact cards, then a `【未覆盖】` section listing every
     candidate or source skipped for budget, unverified expiry assumption, or
     extraction failure, one line each with the reason. Planned source rotation
     per `source-registry.md` is not 未覆盖. Omit the section when empty:

```markdown
【厂商】...
【活动名】...
【类型】Hackathon / 开发者挑战赛 / ...
【奖励】...
【截止时间】yyyy-mm-dd / 长期
【参与门槛】低/中/高 + reason
【报名入口】[活动名](https://...)
【官方性】✅ 官方确认 / ⚠️ 疑似 / ❌ 非官方
【适合度】⭐⭐⭐⭐⭐
【建议】立即行动 / 值得做 / 观望 / 跳过
【理由】...
```

## Scoring

- Reward value: $100K+ = 5, $10K+ = 4, $1K+ = 3, credits/membership = 2,
  swag/certificate only = 1.
- Urgency: <=3 days = 5, <=7 days = 4, <=14 days = 3, >=30 days = 2,
  long-term = 1.
- Official confirmation: official site/account = 5, official community = 4,
  recognized platform or repost with source = 3, unclear = 1.

Action matrix: low difficulty + high score is `立即行动`; low difficulty +
medium score is `顺手做`; high difficulty + high score is `值得投入`; high
difficulty + low score is `跳过`.

## Resources

- `references/bitable-api-patterns.md`: live Base IDs, field contract, write
  shapes, lark-cli checks, and schema pitfalls.
- `references/source-registry.md`: source tiers, tested extraction paths, source
  roles, source quality, and rotation budget.
- `references/keyword-clusters.md`: query families and platform-specific search
  phrases.
- `references/tool-fallbacks.md`: agent-reach, Tavily, DDG, curl, Twitter, and
  Hermes cron failure recovery.
- `references/agentdeadlines-guide.md`: AgentDeadlines structure and JSON-LD
  parser usage.
- `references/cron-architecture.md`: why Hermes cron uses agent-direct scans.
- `references/mcp-enhancement.md`: optional Exa/Firecrawl/Tavily MCP setup.
- `scripts/parse_agentdeadlines.py`: parse downloaded AgentDeadlines HTML.
- `scripts/parse_competehub.py`: parse downloaded CompeteHub monthly page HTML;
  the only working curl path for CompeteHub data.
- `scripts/collect_structured.py`: **batch collector** — fetches AgentDeadlines
  + Devpost (all pages) + CompeteHub (双月) + aihot (with Jina fallback) in
  one parallel call. Use this instead of individual curl commands.
- `scripts/campaign_bitable_sync.py`: deterministic Feishu Base write path.
