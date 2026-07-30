# Tool Commands

Run `agent-reach doctor --json` first and use active backends. Command syntax is
drift-prone; verify with `which` or `--help` when a command fails.

## Reddit

```bash
opencli reddit search "QUERY" -f yaml
opencli reddit subreddit "SUBREDDIT" -f yaml
opencli reddit hot -f yaml
opencli reddit read "POST_URL_OR_ID" -f yaml
rdt export "QUERY" -r SUBREDDIT -n 5 --format json -o /tmp/rdt_output.json
rdt search "QUERY" -n 10 --compact
rdt read POST_ID --compact
```

- Prefer OpenCLI when `agent-reach doctor` reports it active.
- Use `subreddit`, `hot`, and `read` for board/feed browsing; do not rely only
  on `search`.
- Use `rdt export` for batch mining when OpenCLI is unavailable; subreddit
  filter works there.
- Do not use `rdt search -r subreddit`; that path has been unreliable.

## Xiaohongshu

```bash
opencli xiaohongshu search "QUERY"
opencli xiaohongshu note "FULL_SIGNED_URL" --format plain
opencli xiaohongshu comments "FULL_SIGNED_URL" --format plain
```

- Requires Chrome/OpenCLI session.
- `note` and `comments` require the full signed URL from search results.
- Write `原始链接` as the canonical form
  `https://www.xiaohongshu.com/explore/NOTE_ID` — the signed `search_result`
  URL carries an expiring `xsec_token`. Note IDs' first 8 hex chars are the
  publish timestamp in seconds (use for `发布时间`).
- `read` is not a subcommand.
- If three different queries return `[]`, note possible logged-out browser
  session and switch source.

## Bilibili

Prefer OpenCLI in this environment. `bili` may not be installed even when the
channel is available.

```bash
opencli bilibili search "QUERY" -f yaml
opencli bilibili video BV_ID -f yaml
opencli bilibili comments BV_ID -f yaml
opencli bilibili subtitle BV_ID -f yaml
opencli bilibili ranking -f yaml
```

- Use `search` or `ranking` for leads, then `video` and `comments` for evidence.
- Comments can be primary evidence when they contain the real workflow pain.
- Ignore generic support comments such as "加油" or "求链接" unless they expose
  a concrete job or platform gap.

## Twitter/X

```bash
twitter search "QUERY" --type latest --lang en -n 10
twitter search '"exact phrase" OR "alternative"' --type latest --exclude retweets -n 10
twitter feed -n 20
```

- Binary: `twitter` (package: `twitter-cli`).
- Use `-n`, not `--limit`.
- Chinese demand signals are often weaker on Twitter than Xiaohongshu/V2EX.

## V2EX

Direct curl can fail; use Jina Reader.

```bash
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
curl -s "https://r.jina.ai/https://www.v2ex.com/?tab=hot" -H "Accept: text/plain"
curl -s "https://r.jina.ai/https://www.v2ex.com/t/POST_ID" -H "Accept: text/plain"
curl -s "https://r.jina.ai/https://www.v2ex.com/go/qna" -H "Accept: text/plain"
```

- Prefer node browsing and replies over only hot feed.
- Hot feed often contains promotion or launch posts; require independent user
  evidence before accepting.

RSS is better for recurring collection:

```bash
python3 -c "import feedparser; d=feedparser.parse('https://www.v2ex.com/feed/qna.xml'); print([(e.title,e.link) for e in d.entries[:5]])"
python3 -c "import feedparser; d=feedparser.parse('https://www.v2ex.com/feed/create.xml'); print([(e.title,e.link) for e in d.entries[:5]])"
python3 -c "import feedparser; d=feedparser.parse('https://www.v2ex.com/feed/jobs.xml'); print([(e.title,e.link) for e in d.entries[:5]])"
```

Use API for replies:

```bash
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=qna&page=1" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"
```

## Hacker News

```bash
curl -s "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=5"
curl -s "https://hn.algolia.com/api/v1/items/ID"
```

HN is developer-heavy. Use it for technical workflow pain or cross-validation,
not as the default for ordinary users.

## YouTube

```bash
yt-dlp --flat-playlist --dump-json "ytsearch5:QUERY"
yt-dlp --dump-json "VIDEO_URL"
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "VIDEO_URL"
yt-dlp --write-comments --skip-download --write-info-json --extractor-args "youtube:max_comments=20" -o "/tmp/%(id)s" "VIDEO_URL"
```

- Search and subtitles are stable enough for direction and education demand.
- Comments are best-effort and may be incomplete; use them as evidence only
  when `info.json` contains the original comment.

## Web, Reviews, And Product Directories

```bash
curl -s "https://r.jina.ai/URL" -H "Accept: text/plain"
mcporter call 'exa.web_search_exa(query: "QUERY", numResults: 5)'
```

Use for readable pages, review pages, public complaints, tenders, and industry
forums. If Jina returns login, CAPTCHA, or empty content twice, switch source or
use a browser session.

Useful verified paths:

```bash
# App Store public page reviews. Prefer this over legacy RSS, which may return zero entries.
curl -s "https://r.jina.ai/https://apps.apple.com/us/app/APP_SLUG/idAPP_ID"

# Product Hunt topics, products, reviews, and forums.
curl -s "https://r.jina.ai/https://www.producthunt.com/topics/productivity"
curl -s "https://r.jina.ai/https://www.producthunt.com/products/PRODUCT/reviews"

# Chrome Web Store. Use the full detail/reviews URL from search/browser results.
curl -s "https://r.jina.ai/https://chromewebstore.google.com/detail/EXTENSION_SLUG/EXTENSION_ID"
```

- Product Hunt is usually direction/lead. Accept only concrete reviews or forum
  posts with a real actor and workflow.
- App Store public pages expose a small review sample and ratings. Treat them as
  review evidence after reading the review body.
- G2 and Fiverr often return CAPTCHA through Jina; use Exa snippets only as
  leads, not accepted evidence.

## Marketplace Reviews And Feedback Boards

Access patterns verified 2026-07; re-verify with a sample fetch when one fails.

```bash
# Shopify App Store: rating filter jumps straight to 1-3 star pain.
curl -s "https://apps.shopify.com/APP_SLUG/reviews?page=1&ratings%5B%5D=1"

# WordPress.org plugins: reviews by star, and the unresolved-threads view
# (a live list of unmet needs).
curl -s "https://wordpress.org/support/plugin/PLUGIN_SLUG/reviews/?filter=2"
curl -s "https://wordpress.org/support/plugin/PLUGIN_SLUG/unresolved/"

# Atlassian Marketplace: public REST, structured JSON reviews (stars, full
# text, date, helpful votes). No auth.
curl -s "https://marketplace.atlassian.com/rest/2/addons?limit=25&hosting=cloud"
curl -s "https://marketplace.atlassian.com/rest/2/addons/ADDON_KEY/reviews"

# Public feedback boards: server-rendered, vote counts included. No central
# directory — discover boards with search dorks.
curl -s "https://COMPANY.canny.io/BOARD"
mcporter call 'exa.web_search_exa(query: "site:canny.io CATEGORY", numResults: 5)'
curl -s "https://COMPANY.uservoice.com/forums/FORUM_ID"

# Gumroad Discover: SPA, must go through Jina. Review count ≈ sales proxy.
curl -s "https://r.jina.ai/https://gumroad.com/discover?query=QUERY" -H "Accept: text/plain"

# Google Suggest: free, no key. Seed with pain phrasing ("how to", "best",
# "alternative to", "why is X so").
curl -s "https://suggestqueries.google.com/complete/search?client=firefox&q=how+to+SEED"
```

## Chinese Communities

```bash
# 豆瓣小组: explore feed plain-fetches (titles + snippets = leads). Topic
# detail pages return 403 without login even via Jina (verified 2026-07) —
# read originals through the RSSHub douban group route or a browser session.
curl -s "https://www.douban.com/group/explore" -H "User-Agent: Mozilla/5.0"

# 掘金: SPA, must go through Jina (or an RSSHub route).
curl -s "https://r.jina.ai/https://juejin.cn/tag/%E5%88%9B%E4%B8%9A" -H "Accept: text/plain"

# 电鸭社区: freelance/remote workflow + budget signals. Jina-readable.
curl -s "https://r.jina.ai/https://eleduck.com/" -H "Accept: text/plain"

# 电诉宝: public complaint list, complements 黑猫 on platform/B-side disputes.
curl -s "https://www.100ec.cn/Index/complain_list.html" -H "User-Agent: Mozilla/5.0"

# SegmentFault 问答: plain HTTP.
curl -s "https://segmentfault.com/questions" -H "User-Agent: Mozilla/5.0"

# 虎扑: plain HTTP with UA, rate-limit yourself.
curl -s "https://bbs.hupu.com/all-gambia" -H "User-Agent: Mozilla/5.0"
```

什么值得买 / 贴吧 / 即刻 / 酷安 are RSSHub-route-only; 知乎 / 京东 / NGA /
Linux.do are dead ends (see `source-map.md`). Do not build direct fetchers for
them.

## Paid Manual Services

Search marketplaces manually or through browser/search tools with:

```text
代做 报价单
代整理 PDF Excel
代填 表格
transcribe podcast service
convert pdf to spreadsheet service
```

Evidence is the paid listing, order/review count, and the repeated workflow it
reveals.

Exa is useful for finding readable service pages:

```bash
mcporter call 'exa.web_search_exa(query: "site:upwork.com spreadsheet automation data entry", numResults: 5)'
mcporter call 'exa.web_search_exa(query: "site:fiverr.com excel google sheets automation service", numResults: 5)'
```

Do not accept a snippet alone. Read the listing or cross-check the same workflow
in reviews, communities, or procurement.

## Procurement And Tenders

```bash
mcporter call 'exa.web_search_exa(query: "site:ccgp.gov.cn 采购需求 软件 数据 管理", numResults: 5)'
curl -s "https://r.jina.ai/PROCUREMENT_URL" -H "Accept: text/plain"
```

- Extract buyer organization, budget, deadline, workflow requirement, delivery
  constraints, and acceptance criteria.
- Procurement is strong B-side evidence, but not a consumer demand signal.

## Third-Party Scale Sources

Use these only to rank topics or validate recurrence:

```bash
curl -s "https://api.npmjs.org/downloads/point/last-month/PACKAGE" | jq .
curl -s "https://pypistats.org/api/packages/PACKAGE/recent" | jq .
gh search issues "QUERY" --limit 10 --json title,url,repository,commentsCount,createdAt
curl -s "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=5"
```

- Downloads, stars, ratings, and rankings never pass the evidence gate alone.
- For developer products, pair scale metrics with GitHub issues, HN comments, or
  product reviews.

## Batch Pattern

For deep runs, create `/tmp/{platform}_{category}.json` per platform:

1. Define queries for one category.
2. Execute sequentially with subprocess.
3. Parse native output.
4. Dedupe by URL/title.
5. Sort by engagement.
6. Read top 3-5 originals before gating.
