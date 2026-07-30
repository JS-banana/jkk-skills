# Evidence Gate

Every accepted record must pass all hard gates. If unsure, reject or park.

## Hard Gates

- Concrete URL: a specific post, note, review, complaint, service listing,
  procurement page, or thread.
- Original evidence: the source text, review, comment, or listing was read.
- Real actor: a person, role, buyer, reviewer, practitioner, or organization is
  identifiable from context.
- Specific scene: the situation is clear enough to answer "when does this
  happen?"
- Job and obstacle: the user is trying to make progress and one step is stuck.
- Current behavior: includes workaround, existing product, manual service,
  ignored task, failed alternative, or repeated complaint.
- Signal: includes likes, replies, comments, ratings, orders, budget, paid
  service, repeated reviews, or cross-source recurrence.
- Productable: a product, service, content product, workflow, or physical
  improvement could plausibly help.
- Natural Chinese evidence: `原文内容` is a readable Chinese rendering of the
  original expression.

A keyword hit, semantic-search result, trend mention, or model summary passes no
gate by itself.

## Recency Rule

Evidence published more than 18 months ago is stale by default: the pain may be
solved or the platform landscape changed. Accept it only with recent recurrence
— new comments on the thread, a newer post describing the same job, or a
cross-source match within 18 months. Otherwise park it, and record the
recurrence URL in `佐证链接` when it exists.

## Third-Party Data Rule

Downloads, ratings, rankings, stars, traffic estimates, launch lists, trend
graphs, funding, and job counts are direction or scale evidence only. They can
raise or lower priority, but they cannot create an accepted row unless paired
with a concrete post, review, comment, complaint, service listing, procurement
requirement, or other original actor/workflow evidence.

## One-Vote Exclusions

Reject immediately when the record is mainly:

- Product bug: crash, install failure, plugin cannot load, broken integration.
- Existing-product feature request: "please add X to product Y."
- Product list, comparison, launch, discount, funding, or news.
- Usage help: "how do I configure/disable/enable X?"
- Generic recommendation: "求好用 App" without scene, pain, or current method.
- Developer idea-fishing: "what should I build?" or "what tool do you wish
  existed?" unless the comments themselves contain standalone demand evidence.
- AI-generated idea, VC trend, or market map without user/workflow evidence.
- SEO article, advertorial, affiliate list, or platform-generated summary.
- Future-only intent: "I would use/pay" without past behavior or commitment.
- Unreadable source, missing URL, or copied text that cannot be traced.

An exclusion applies to the post, not its comment section: before dropping a
high-engagement post on a one-vote exclusion, scan its top comments — a comment
can still pass the gate as its own row.

## Comment-Derived Signals

High-engagement comments can be standalone signals.

- A comment with specific pain or product wish can become its own row.
- The parent post provides context and reaction; the comment provides evidence.
- Write `原文内容` from the comment, not the post.
- Multiple comments on the same post can become separate rows only when they
  describe different jobs.
- Same-job corroboration may be folded into `原文内容` as a short `（评论区：…）`
  digest; a comment describing a different job must be its own row, not appended.

## Signal Strength

Strong:

- Explicit paid behavior: paid, subscribed, bought, hired, outsourced, switched.
- Cost: time, money, opportunity, legal/compliance risk, health/family risk.
- Repeated failed workarounds or multiple existing products tried.
- Procurement budget, service orders, repeated reviews, or cross-platform match.

Medium:

- Clear scene, job, pain, and workaround, but little cost detail.
- Several comments or reviews repeat the same issue.

Weak:

- Vague dissatisfaction.
- No scene, user, cost, workaround, or repeated pattern.
- Keep only as a candidate for more research, not as an accepted Feishu row.

## Universality

High:

- Same pain appears independently on Chinese and international sources.
- Large reaction count or many comments/reviews repeat the same job.
- Procurement/service/review evidence confirms money or workflow repetition.

Medium:

- Moderate reaction count or one source with repeated agreement.

Low:

- Isolated but concrete pain. Keep only if strongly productable and evidence is
  original.

## P0 Gate

`P0-立即行动` requires both:

- `需求强度=强` and `需求普遍性=高`
- input-only `P0证据`: explicit willingness to pay/buy/switch, paid workaround,
  urgent replacement behavior, procurement budget, or repeated purchase/service
  failure

Without `P0证据`, score 9 is capped at `P1-重点考虑`.

## Translation Rule

`原文内容` is a natural Chinese rendering of what the original user said — not an
analysis report, and not a mechanical word-for-word translation.

- Read and understand the full original first, then re-express it in idiomatic
  Chinese that a native speaker would actually say.
- For non-Chinese sources, carry over the source's context, tone, and intent.
  Do not translate phrase-by-phrase in a way that reads stilted or foreign.
- Keep the user's own voice. Do not prepend headings such as `用户情况：` or
  `核心需求：`, and do not compress it into a summary report.

Good — natural and faithful:

```text
我每次做报价都要把供应商发来的 PDF 一项项抄进 Excel，再改成客户能看的格式。一个单子经常要折腾一两个小时，还怕抄错价格。
```

Bad — analysis report:

```text
用户情况：供应商报价处理困难。核心需求：需要报价工具。社区反馈：多人评论。
```

Bad — mechanical literal translation of an English source:

```text
我一直尝试习惯应用程序但总是在一周之后掉落。
```

Better — same source, idiomatic:

```text
我试过好几个习惯打卡 App，但每次都坚持不到一周就放弃了。
```

## Rejected And Parked Lists

Keep rejected candidates in this shape during each run:

```json
{"title":"...","url":"...","source":"...","reason":"产品 bug，不是需求信号"}
```

Park is for real-looking demand that misses exactly one gate (usually signal,
recency, or actor detail) — not a soft reject. Save parked candidates to
`/tmp/find-gap-parked.json`:

```json
{"title":"...","url":"...","source":"...","park_reason":"证据超18个月，未见近期复现"}
```

Deep mining runs read the parked list first and try to complete the missing
gate (find recurrence, read more comments, locate the actor) before opening new
sources.
