# Source Map

Use live backend availability, not hard-coded platform assumptions.

## First Command

```bash
agent-reach doctor --json
```

Use the active backend for Reddit, Xiaohongshu, Twitter/X, Bilibili, V2EX, RSS,
Exa, and web. If a backend is unavailable, switch source family instead of
pretending the platform is covered.

## Default Mix

For narrow runs, use at least three source families:

1. Mass-market lived pain: Xiaohongshu, Douban groups, Reddit, V2EX, Bilibili
   comments, Hupu.
2. Explicit ask or dissatisfaction: Q&A, reviews, complaints, recommendation
   threads, public feedback boards (Canny/Featurebase/UserVoice).
3. Money/workflow evidence: paid manual services, product reviews, procurement,
   tenders, industry forums, marketplace reviews (Shopify/WordPress/Atlassian),
   freelance communities (电鸭).

For general or deep runs, add a fourth lane:

4. Third-party direction or scale: Product Hunt, app/store rankings, trend
   pages, package downloads, job posts, funding/product directories, and search
   volume proxies.

Include both Chinese and international sources unless the user narrows scope.
Do not compensate for weak quality by adding developer-only sources.

Choose acquisition modes from `acquisition-strategy.md` before writing queries.
Keyword search is auxiliary unless the run is explicitly a query-mining run.

## Operational Channel Matrix

Use this matrix to choose sources before running commands. "Primary evidence"
can produce accepted records after original reading. "Direction/scale" can only
prioritize topics or validate recurrence.

| Channel | Best role | Tool path | Default status |
| --- | --- | --- | --- |
| Reddit subreddit/search/read | Primary evidence, international depth | `opencli reddit subreddit/search/read -f yaml` | Default international source |
| V2EX API/RSS/node/replies | Primary evidence, Chinese tech/life/workflow | `curl` public API, `feedparser` RSS, Jina post read | Default Chinese stable source |
| Bilibili search/video/comments/subtitle | Primary evidence from Chinese video comments and creator workflows | `opencli bilibili search/video/comments/subtitle -f yaml` | Default Chinese mass-market source |
| Xiaohongshu note/comments/feed | Primary evidence for Chinese lifestyle scenes | `opencli xiaohongshu search/note/comments -f yaml` | High value but session-sensitive; fallback after repeated `[]` |
| App Store public app pages | Review evidence and category gaps | Jina Reader on `apps.apple.com` app pages; direct HTML parse if needed | Use page reviews; legacy RSS may return zero |
| Chrome Web Store extension pages | Review evidence for browser workflows | Jina Reader on full extension detail/reviews URL, Exa to find pages | Use when page is readable |
| Product Hunt topics/products/reviews/forums | Direction and lead source; some review evidence | Jina Reader on topic/product/review/forum pages | Direction by default; accept only concrete reviews/forums |
| YouTube search/subtitles/comments | Education demand and product-comparison comments | `yt-dlp` search/subtitle/comments | Secondary; comments are best evidence |
| Twitter/X search/feed/tweets | Speed, meta discussion, and switching language | `twitter search/tweet/feed` | Noisy; direction unless concrete actor/workflow |
| GitHub Issues/HN/Stack Overflow | Developer workflow pain | `gh search issues`, HN Algolia/Jina | Developer-only unless scoped |
| Procurement/tenders | Budgeted B-side workflow evidence | Exa search + Jina Reader on notices/PDFs | Strong B-side evidence |
| Paid service marketplaces | Money-backed manual workflows | Exa/Jina/manual browser for Fiverr, Upwork, Taobao, Xianyu, ZBJ | Strong if listing/order/review is readable |
| Job posts | Budgeted role/workflow signal | LinkedIn if configured; otherwise Exa/Jina job boards | Validation/direction unless task pain is explicit |
| Package/download metrics | Adoption and developer ecosystem scale | npm API, PyPIStats, GitHub stars/issues | Scale only |
| Trend/market data | Timing and category selection | Exploding Topics, Google Trends, reports, directories | Direction only |
| Shopify App Store reviews | Primary evidence from paying merchants | Plain fetch `apps.shopify.com/{slug}/reviews?page=N&ratings[]=1` (rating filter hits 1-3 star directly) | Default B-side review source; no login |
| WordPress.org plugin reviews/support | Primary evidence; `/unresolved/` view is a live unmet-needs list | Plain fetch `wordpress.org/support/plugin/{slug}/reviews/?filter=1` and `/unresolved/` | Default international review source; support threads beat reviews |
| Atlassian Marketplace | Primary evidence, structured JSON, B2B high willingness-to-pay | Public REST, no auth: `marketplace.atlassian.com/rest/2/addons/{key}/reviews` | Easiest integration; star/full text/date/votes in JSON |
| Public feedback boards (Canny/Featurebase/UserVoice) | Structured explicit demand; vote counts are pre-quantified demand magnitude | Plain fetch `{co}.canny.io/{board}`, `{co}.featurebase.app`, `{co}.uservoice.com/forums/{id}`; discover via `site:canny.io` dorks — no central directory | Structured-demand lane; long-Open high-vote posts = incumbent gaps |
| Gumroad Discover | Willingness-to-pay direction; review count ≈ sales proxy | Jina on `gumroad.com/discover` (SPA; plain fetch returns nothing) | Direction/WTP only |
| Google Suggest / PAA | Search-intent recall, pain phrasing space | Free no-key `suggestqueries.google.com/complete/search?client=firefox&q=`; Answer Socrates for PAA | Auxiliary recall only |
| dev.to / Lobsters / Indie Hackers | Developer/indie direction, occasional primary | Public JSON `dev.to/api/articles`, `lobste.rs/hottest.json`; plain fetch IH | Direction unless concrete actor/workflow |
| F5Bot | Recurring Reddit/HN keyword monitoring | Free email alerts (GummySearch shut down 2025-11) | Monitoring channel for scheduled runs |
| 豆瓣小组 | Chinese mass-market life pain (租房/考公/攒钱/抠门组) | Explore feed plain-fetches (`douban.com/group/explore`, titles + snippets); topic detail pages 403 without login (verified 2026-07) — read originals via the RSSHub douban group route (item body carries content) or a browser session | Feed = lead source; original reading needs RSSHub/browser |
| 掘金 | Primary evidence for indie-dev monetization/workflow (变现复盘、踩坑) | Jina on `juejin.cn` (SPA); RSSHub route | Chinese indie/dev source |
| 电鸭社区 | Primary evidence for freelance/remote workflow + budget signals | Jina on `eleduck.com`, no login wall | Money/workflow source |
| 电诉宝 | Complaint evidence, platform/B-side disputes | Plain fetch `100ec.cn` complaint list | Complements 黑猫 (which skews C-side retail) |
| SegmentFault / Gitee issues | Chinese developer workflow pain, OSS feature gaps | Plain fetch `/questions`, targeted repo issues; RSSHub | Developer-only unless scoped |
| 少数派 / 虎扑 | Tool-direction discussions; male-skewed consumer/digital pain | Plain fetch `sspai.com`, `bbs.hupu.com` (UA + rate limit) | Secondary Chinese sources |
| 什么值得买 | 求推荐/平替/避坑 evidence | RSSHub smzdm route ONLY — direct fetch and Jina both blocked | Use via RSSHub or skip |

## Source Families

| Family | Use for | Sources | Notes |
| --- | --- | --- | --- |
| Daily-life social | Mass-market lived pain | Xiaohongshu, 豆瓣小组, Reddit, Bilibili comments, 虎扑 | Best for lifestyle, health, travel, home, shopping, study, family; 豆瓣/虎扑 balance XHS's demographic skew |
| Feedback boards | Vote-ranked explicit demand | Canny, Featurebase, UserVoice public boards | Votes quantify magnitude; long-Open high-vote posts reveal incumbent gaps; discover via `site:` dorks |
| Idea communities | Direct "someone make this" leads | r/SomebodyMakeThis, r/AppIdeas, r/Startup_Ideas, Unvalidated Ideas, IdeasAI | Leads only; require original demand evidence before accepting |
| Question/recommendation | Explicit unsolved needs | V2EX, Reddit, Quora if readable, Zhihu if logged in | Reject generic recommendation without scene |
| Reviews/ratings | Existing product gaps | App Store, Google Play, Chrome Web Store, Shopify App Store, WordPress.org plugins, Atlassian Marketplace, G2, Capterra, Trustpilot, AlternativeTo | Prefer 2-4 star reviews; 1-star is often product rage; Shopify/WordPress/Atlassian are login-free |
| Consumer complaints | Strong service pain | 黑猫投诉, public complaint boards | Treat as service/process pain, not always product opportunity |
| Paid manual services | Repetitive paid workflows | Fiverr, Upwork, 淘宝, 闲鱼, 猪八戒 | Search `代做`, `代整理`, `代填`, `代录入`, `代转写` |
| Business/procurement | Budgeted workflow needs | 中国政府采购网, public resource exchanges, industry forums | Strong for B-side; extract role, workflow, budget, requirement |
| Product/revenue directories | Validated products and gaps | Starter Story, Indie Hackers Products, MicroConf, Product Hunt, BetaList, 1000 Tools | Ask what people pay for and where gaps remain |
| Trend/VC | Direction and timing | Exploding Topics, Google Trends, Glimpse, YC RFS, a16z, NFX, First Round Review, industry reports | Direction only; never enough for an accepted record |
| Developer sources | Technical workflow pain | HN, GitHub Issues, Stack Overflow | Fallback unless user asks for developer products |
| Hiring/jobs | Budgeted operational work | LinkedIn, job boards, company career pages | Good for role/workflow discovery; not direct user pain alone |
| Usage/scale metrics | Adoption and recurrence proxy | npm, PyPIStats, GitHub stars/issues, app ratings, Chrome users | Scale only; pair with reviews or posts |

## Source Roles

| Role | What it can prove | Examples |
| --- | --- | --- |
| Direction | A category may be worth exploring | Trend reports, VC essays, Product Hunt, product directories |
| Lead | A possible pain exists | Idea communities, generic recommendation threads, broad search results |
| Evidence | A real actor has a job, obstacle, and current behavior | Original posts, reviews, complaints, comments, service listings |
| Validation | The pain repeats or money is involved | Multiple sources, 2-4 star reviews, paid services, procurement, order counts |
| Scale | A category or tool has adoption | Downloads, stars, ratings, rankings, traffic estimates |

Only the Evidence role can produce accepted records; the gate for the other
roles is `evidence-gate.md` (Third-Party Data Rule).

## Language Scope

Do both Chinese and English unless the user narrows scope. The two languages
are not interchangeable — build queries from the native phrase families in
`acquisition-strategy.md`, never by translating one language's keywords into
the other.

## Deep Mining Categories

Pick 3-4 per deep run:

| Category | Inspect scenes | Evidence to prefer |
| --- | --- | --- |
| Health/Fitness | Habit adherence, sleep, ADHD, postpartum, rehab, chronic tracking, caregiver handoff | Long posts, app reviews, coaching/services, device complaints |
| Work/Productivity | Reminders, meetings, approvals, document handoff, team coordination, "chat plus spreadsheet" workflows | Workflow posts, 2-4 star SaaS reviews, tool-switching threads |
| Money/Finance | Subscriptions, budgeting, portfolio tracking, reimbursement, invoices, tax prep | Switching intent, paid apps, spreadsheet workarounds, finance forums |
| Learning/Education | Practice feedback, exam planning, language learning, parent-child study, credential prep | Study communities, app reviews, paid tutoring/service evidence |
| Jobs/Career | Resume, applications, interview prep, recruiting outreach, freelancer operations | Job-seeker threads, recruiter workflows, paid services, templates |
| Home/Life | Chores, cooking, pet care, storage, family schedules, errands | XHS/Bilibili comments, Reddit verticals, service listings |
| Travel/Housing | Trip planning, visas, rentals, home viewing, moving, local transport | Long complaint posts, review sites, agency/service evidence |
| Creative/Media | Writing, design, video editing, asset management, publishing, creator admin | Creator forums, software reviews, paid manual services |
| Business Workflow | Quotations, customer records, inspection reports, contracts, data entry, migrations | Procurement, service marketplaces, ops forums, repeated manual cost |
| AI/Automation | Tool cost, model migration, privacy, reliability, team governance, AI workflow handoff | Pricing complaints, workflow failures, local/offline asks, team usage posts |

## Dead Ends (verified 2026-07)

Do not spend rounds on these; the wall is the platform, not the query. Re-verify
only if access conditions visibly change.

| Channel | Why not |
| --- | --- |
| Quora | 403 anti-bot wall on question pages |
| Etsy | CAPTCHA even through Jina; needs paid scraper |
| Amazon reviews | Heavy anti-bot; use HuggingFace review datasets for cold-start instead |
| Salesforce AppExchange | Consent-wall shell; low ROI vs Atlassian's open API |
| Facebook Groups / Discord / Skool | Login-walled or private |
| Figma Community | Reviews/comments do not render; install counts are direction only |
| 知乎 (no login) | Security CAPTCHA even via Jina; needs login cookie |
| 京东问答/评论 | 「京东验证·请登录」risk-control wall |
| NGA / 一亩三分地 | 403, forced login |
| 百度贴吧 direct | Slider CAPTCHA; RSSHub route only |
| 百度知道 | Empty returns + SEO spam, weak first-hand pain |
| 即刻 / 酷安 web | Login wall / marketing shell; RSSHub routes only |
| Linux.do | Cloudflare challenge; lower signal density than 掘金/电鸭 anyway |
| 百度指数 / 巨量算数 / 微信指数 | Login-walled, scale curves only — validation, never discovery |
| 公众号第三方索引 | 搜狗微信 lags months + CAPTCHA (lead only); 新榜/西瓜 are paid | 

## Stop Rules

- Stop after 30 inspected candidates or 8 strong accepted records by default.
- Switch source after two rounds of snippets, ads, product pages, or unreadable
  pages.
- Switch source if a platform returns empty results for three varied native
  queries; record this as source unreliability, not absent demand.
- For high-engagement posts, scan top 5-10 comments before accepting or
  rejecting.
- If all results are developer-only and scope is general, change source family.
