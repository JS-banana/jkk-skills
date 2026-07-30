# Acquisition Strategy

Choose how to acquire signals before choosing keywords. Keyword search is a
recall booster, not the default source of truth.

## First Principle

A demand radar run is trying to observe real behavior:

- who is stuck
- in which scene
- on which job
- what they do now
- what cost, workaround, payment, or repeated reaction proves the pain

A keyword hit only says "this text matched a phrase." It does not prove demand
until the original evidence and comments/reviews/listings are read.

## Source Reliability

| Tier | Sources | Use | Risk |
| --- | --- | --- | --- |
| Stable pull | RSS/API feeds, public review pages, procurement pages, marketplace listings | Recurring collection and longitudinal comparison | Still needs dedupe and original reading |
| Community feed | Subreddit/node/forum hot, new, top, and comment feeds | Primary discovery for lived pain and repeated questions | Ranking drift, jokes, meta posts, promotion |
| Review/complaint | App Store, Google Play, Chrome Web Store, G2, Capterra, Trustpilot, 黑猫投诉 | Existing product gaps and willingness to switch | Product rage or support bugs can dominate |
| Paid workflow | Fiverr, Upwork, 淘宝, 闲鱼, 猪八戒, tenders | Money-backed repetitive tasks | Listing may reflect supply, not demand |
| Search probe | Reddit/XHS/V2EX/web keyword or semantic search | Fill recall gaps, test a hypothesis, find examples | Language mismatch, session state, SEO noise |
| Third-party scale | Product Hunt, app pages, package downloads, GitHub metrics, trend pages, job posts | Direction, prioritization, and recurrence checks | Never proves demand alone |
| Direction only | Trend reports, Product Hunt, VC essays, idea lists | Topic selection and timing | Never enough for an accepted record |

Default: make stable pull, community feed, review/complaint, or paid workflow
the primary mode when available. Use search probes after the source plan is
clear.

Access routing: try plain fetch first; if a source is an SPA that returns empty
or a shell (Gumroad, 掘金, 电鸭, 什么值得买), route through Jina or its RSSHub
route instead of retrying plain fetch. `source-map.md` marks which tier each
channel needs and which channels are dead ends.

## Acquisition Modes

| Mode | When to use | How to read it |
| --- | --- | --- |
| Board/feed browsing | You need broad discovery without overfitting keywords | Browse relevant communities by hot/new/top; keep posts where the actor, scene, and workaround appear |
| Comment mining | A post has strong reaction but weak original text | Read top comments; the comment can become the primary signal |
| Review mining | A category already has products | Prefer 2-4 star reviews; use rating-filter deep links (`?ratings[]=1`, `?filter=1`) to jump straight to low-star pages; extract failed expectation, switching reason, and missing workflow |
| Complaint mining | Service/process pain is likely | Treat as process evidence; reject if it is only one company's support failure |
| Paid service mining | People already outsource the work | Extract the repeated manual job, order/review count, price, and buyer role |
| Procurement/tender mining | B-side budget may exist | Extract buyer organization, workflow requirement, budget, deadline, and constraints |
| Alternatives mining | Existing tools are costly or unsatisfactory | Search native switching language and read why current tools fail |
| Structured-demand board mining | Demand is already posted, explicit, and vote-ranked | Enumerate public feedback boards (Canny/Featurebase/UserVoice), public roadmaps, and Q&A boards board-by-board instead of searching; votes give magnitude, high-vote long-Open posts reveal incumbent gaps; the post plus its comments are the evidence |
| Template census | Users already self-serve a job with templates or spreadsheets | Enumerate template marketplaces (Notion gallery, WPS/Office templates, Etsy digital) by sales/downloads; a high-usage template is a structured job people solve with a workaround — then return to its reviews/comments for first-hand evidence |
| Search probe | You need recall for a known scene | Use platform-native phrase families; log hits and misses |
| Product directory mining | You need categories and incumbents | Use only as leads; go find users, reviews, complaints, or paid workflows |
| Third-party scale check | You need to rank categories before deeper reading | Use downloads, rankings, ratings, launch/review volume, job posts, or trend pages; then seek original evidence |

## Native Lexicon Rule

Do not mechanically translate Chinese keywords into English or English keywords
into Chinese. Build a native lexicon per platform from observed posts, comments,
reviews, and missed searches.

For each run, keep a short hit/miss note:

```json
{"platform":"reddit","query":"\"what do you use\" \"spreadsheet\" manage","result":"hit","notes":"found finance, CRM, pet-sitting workflow posts"}
{"platform":"xiaohongshu","query":"订阅太贵 平替 app","result":"miss","notes":"OpenCLI returned []; likely session/search issue, switch source"}
```

Use translation only after evidence is collected, when writing Chinese Feishu
rows.

## English Phrase Families

Reddit and English forums often use sentence-level intent patterns. Pair these
with a subreddit, role, category, or workaround; standalone phrases are noisy.

| Family | Native phrases | Good for | Common traps |
| --- | --- | --- | --- |
| Unmet wish | `I wish there was`, `why isn't there`, `does this exist`, `somebody make this` | Direct productable pain | Jokes, fantasy, developer idea-fishing |
| Lookup/recommendation | `is there an app for`, `what do you use to`, `how do you manage`, `any tool for` | Existing workflows and alternatives | Generic recommendation without scene |
| Workaround | `using spreadsheets`, `currently use Excel`, `Google Sheets`, `manual process`, `copy paste`, `messy workaround`, `second job`, `mental load` | Hidden operational pain | Broad enterprise stories and unrelated anecdotes |
| Switching/cost | `alternative to`, `replacement for`, `switched from`, `too expensive`, `enterprise pricing`, `subscription fatigue`, `tired of paying`, `no-subscription` | Willingness to switch or pay | Product comparison posts without real job |
| Ownership/privacy | `offline-first`, `privacy-focused`, `local-only`, `open-source alternative`, `self-hosted` | Anti-cloud and trust gaps | Developer-only ideology without user workflow |
| Paid intent | `would pay for`, `premium`, `budget`, `hired someone`, `outsourced`, `for our team`, `client work` | Money-backed demand | Hypothetical "would pay" with no past behavior |

Observed useful English samples:

- Reddit `I wish there was` produced strong posts such as ADHD memory load and
  house-showing review pain, but also jokes and movie memes.
- `looking for a tool` + `too expensive` surfaced recruiting outreach, Active
  Directory migration, Webflow A/B testing, and multiserver management posts.
- `what do you use` + `spreadsheet` surfaced subscription tracking, portfolio
  tracking, CRM, and pet-sitting client management workflows.

## Chinese Phrase Families

Chinese sources use different social markers. On Xiaohongshu, V2EX, Bilibili,
Zhihu, and complaint boards, native query language is usually scene-plus-tone,
not a direct product-wish sentence.

| Family | Native phrases | Good for | Common traps |
| --- | --- | --- | --- |
| 求推荐 | `求推荐`, `有没有好用的`, `大家都用什么`, `你们怎么处理`, `怎么管理` | Finding active workarounds | Empty "求 App" without scene |
| Friction | `太麻烦了`, `折腾`, `坚持不下来`, `用不下去`, `忘记`, `救命`, `有没有人和我一样` | Lived pain in daily life | Emotional vent without productable job |
| Manual workaround | `手动整理`, `复制粘贴`, `Excel表`, `表格`, `微信+表格`, `截图收藏`, `一项项录入` | Repetitive workflow and B-side tasks | Tutorial or template posts |
| Switching/cost | `平替`, `替代`, `不想续费`, `订阅太贵`, `开会员`, `割韭菜`, `智商税`, `不值` | Price pain and replacement behavior | Pure bargain hunting |
| Bad experience | `避坑`, `踩雷`, `后悔买`, `吐槽`, `不好用`, `白花钱` | Review and complaint mining | Single-product defect |
| Paid manual service | `代做`, `代整理`, `代填`, `代录入`, `代转写`, `报销`, `发票`, `报价单`, `客户资料` | Money-backed manual jobs | Seller spam without buyer evidence |

## Platform Notes

Reddit:

- Prefer subreddit/feed browsing for known communities, then use phrase probes.
- Useful communities depend on category: examples include `r/ADHD`,
  `r/smallbusiness`, `r/personalfinance`, `r/macapps`, `r/Productivity`,
  `r/SomebodyMakeThis`, `r/AppIdeas`, and vertical communities.
- Treat `r/SomebodyMakeThis` and developer "what should I build?" posts as lead
  sources only. Accept the comments or linked user stories, not the prompt.
- Raw keyword search drifts semantically (e.g. `subscription fatigue` surfaces
  unrelated finance rants); use it only to locate specific posts to `read`, then
  mine comments. Skip pinned/stickied/mod/announcement posts when browsing feeds.

V2EX:

- Prefer node browsing and replies over only hot feed. Useful nodes often
  include `qna`, `share`, `create`, `jobs`, `programmer`, `fit`, and `life`.
- Hot feed is noisy and promotion-heavy; promotion posts need independent user
  evidence before acceptance.
- RSS feeds are stable recurring inputs for `qna`, `create`, and `jobs`.

Xiaohongshu:

- Use native lifestyle and scene language. Read notes and comments, not only
  search result titles.
- OpenCLI depends on browser session and signed URLs; repeated empty results
  are a reliability issue, not market evidence.

Bilibili:

- Use search/ranking for lead discovery, then `video` and `comments` for
  evidence.
- Comments often reveal better demand than the video title. Prefer comments
  that mention current workaround, platform limits, mobile/desktop gap, privacy,
  or willingness to use/pay.

Reviews:

- Mine 2-4 star reviews before 1-star reviews.
- Keep rows only when the review reveals a job, failed expectation, workaround,
  or switching reason.
- Public App Store RSS may return zero reviews. Read public App Store pages via
  Jina or direct HTML first; use App Store Connect only for apps the user owns.
- G2/Capterra/marketplace pages may return CAPTCHA or login walls. Switch after
  two blocked reads.

Paid services and procurement:

- These channels are more reliable for budgeted workflows than social likes.
- Extract buyer type, repeated task, price/budget, service/order count, and
  delivery constraints.
- Fiverr/Upwork pages are often CAPTCHA-prone through Jina. Exa snippets can be
  leads, but accepted records require a readable listing, order/review signal,
  or another source confirming the workflow.

Third-party data:

- Product Hunt, trend pages, downloads, stars, app ratings, and job posts rank
  where to dig next. They do not pass the evidence gate without a concrete
  review, post, comment, listing, or procurement requirement.
- Package downloads and GitHub stars are useful only for developer products.
- Job posts prove budgeted work exists, not that users are dissatisfied.

## Batch Source Plan

Before collection, write a compact source plan:

```text
Primary mode: board/feed browsing + review mining
Search probe role: auxiliary recall only
Chinese sources: V2EX qna/fit/life, Xiaohongshu if session returns notes
International sources: Reddit r/ADHD/r/personalfinance/r/macapps
Money source: App Store 2-4 star reviews + Fiverr/Upwork listings
Third-party source: Product Hunt category + npm/PyPI/app ratings as direction
Native phrase families: EN workaround + switching/cost; ZH 求推荐 + 手动整理 + 平替
Fallback: if XHS returns [] three times, switch to V2EX/Bilibili comments
```
