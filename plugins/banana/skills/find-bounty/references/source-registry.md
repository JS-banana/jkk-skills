# AI 活动雷达 — 信源注册表

> 分层策略：Tier A（每日必扫）→ Tier B（每周深扫）→ Tier C（按需/用户转发时查）
> 最近更新：2026-07-07（大规模扩源：Devpost 切公开 JSON API、新增 CompeteHub/aihot.today/HN Algolia 等结构化源、
> 新增学术竞赛层与国内线下活动层；标注「2026-07-07 实测」的条目均为当日 curl 验证）

## 结构化优先原则

同一个源有多种采集通道时，按此顺序选择，禁止跳级：

1. **JSON API / RSS / iCal / JSON-LD**（零解析成本，字段完整）
2. **curl 直取 HTML**（需带真实浏览器 UA，见「采集坑汇总」）
3. **DDG / web_search 搜索摘要**（只能做初筛，信息有损）

每次巡检先消费第 1 类源；搜索类查询只用于捕获聚合器之外的漏网活动。

---

## Source Roles

Use roles before choosing queries. A rich channel list is not enough; each kept
record still needs an official or recognized confirmation path.

| Role | What it can prove | Examples | Acceptance rule |
|------|-------------------|----------|-----------------|
| Discovery | A possible opportunity exists | AgentDeadlines, broad search, V2EX/Juejin monthly roundups, X/Twitter, Reddit | Follow up before keeping |
| Platform listing | Reward, deadline, participation format, and platform status | Devpost, lablab.ai, DoraHacks, Tianchi, Kaggle, DataFountain | Can be kept when entry URL and current status are visible |
| Official confirmation | Rules, registration, reward, deadline, or claim path from the organizer | Vendor event pages, challenge pages, official docs/blogs | Required for high-confidence records |
| Community signal | Early or local signal that may not be indexed elsewhere | linux.do, V2EX, Reddit, Bilibili, Xiaohongshu, X/Twitter | Treat as lead unless it links to official details |
| Detail extraction | Page body or structured data for an already found candidate | Jina Reader, curl, Firecrawl, Exa fetch, AgentDeadlines JSON-LD | Verify dates and entry path before scoring |
| Reminder state | Current status of an already recorded opportunity | Feishu Base views, seen JSONL, official status page | Notify only after rechecking current status |

## Tool Routing

For weekly deep scans, active queries, and social/community sources, run:

```bash
agent-reach doctor --json
```

Use the active backend instead of assuming a platform is covered. Current useful
routes are usually Twitter/X via `twitter`, Reddit/Xiaohongshu/Bilibili via
`opencli`, V2EX via public API/RSS, Exa via `mcporter`, and web pages via Jina
Reader. If a backend is unavailable, switch source family rather than marking
the opportunity absent.

## Tier A：每日必扫（每次巡检都要覆盖）

### 🏗️ 直接聚合平台（核心信源，信号密度最高）

| ID | 平台 | URL | 搜索方式 | 提取方式 | 数据质量 | 备注 |
|----|------|-----|---------|---------|---------|------|
| `agentdeadlines` | AgentDeadlines | agentdeadlines.com | curl 直连 → 解析 `<script type="application/ld+json">` | **JSON-LD ✅**（name/startDate/endDate/url/description 全量结构化，web_extract 可作备选） | ⭐⭐⭐⭐⭐ | **AI Agent 专属 deadline 聚合器**（31+ 活动），单页含奖金/截止/格式/赞助商，曾单次发现 KDD Cup $885K / ARC Prize $2M 级别活动。**⚠️ 过期过滤**：约 1/3 条目已过期，先按 endDate < today 排除。详见 `agentdeadlines-guide.md` |
| `devpost` | Devpost | devpost.com/api/hackathons | **公开 JSON API（免鉴权）**：`curl -A '<真实UA>' 'https://devpost.com/api/hackathons?page=1&challenge_type[]=online&status[]=open&themes[]=Machine%20Learning%2FAI'` | JSON 直取 ✅（2026-07-09 实测：`status[]=open` + `themes[]=Machine Learning/AI` 服务端过滤有效，过滤后全量仅 ~24 条/3 页；响应含 `meta.total_count`，9 条/页） | ⭐⭐⭐⭐⭐ | 全球最大 hackathon 平台。**改用 JSON API，弃用 site: 搜索**。**翻页硬规则**：先读 `meta.total_count` 算出总页数（⌈total/9⌉），带过滤参数翻完所有页——过滤后总量很小（~3 页），只看前 1-2 页不算完成；漏页候选记入 未覆盖 |
| `competehub` | CompeteHub（AI赛事通） | **月度页** `competehub.dev/zh/monthly/YYYY-MM`（唯一可 curl 的数据入口） | curl + **真实浏览器 UA**（默认 UA 403）→ `scripts/parse_competehub.py` | 脚本解析 ✅（2026-07-09 实测：月度页 RSC 服务端渲染 298 行，脚本提取 title/prize/dates/status 全量成功）。**⚠️ 列表页 `/zh/competitions` 的竞赛行是客户端渲染，curl 只有 UI 文案，任何正则都提不到数据——不要再试** | ⭐⭐⭐⭐⭐ | **国内竞赛聚合的天花板**：已聚合 Kaggle/天池/DataCastle/华为云/飞桨/讯飞等 50+ 平台、200+ 活跃竞赛，含奖金/截止/城市/30+ 标签，每 24h 更新。**提取失败即切兜底，禁止静默跳过该源**：V2EX 用户 `wuswoo` 月度帖（`curl 'https://www.v2ex.com/api/topics/show.json?username=wuswoo'`，2026-07-07 实测 ✅）及 CSDN/知乎同步版 |
| `aihot` | aihot.today | aihot.today/ai-event | curl + UA ✅ | HTML ✅（2026-07-07 实测 266KB，按月归档；同为 RSC 转义 JSON，单页可提取 60+ 中文活动条目） | ⭐⭐⭐⭐ | 中国 AI 活动/会议/黑客松/沙龙聚合（78+ 条），含日期区间/城市/状态/**公众号原文链接**——公众号私域活动的公开入口，与 CompeteHub（偏竞赛）互补。**⚠️ 存量偏旧**：按月归档含大量往年活动，提取后先按日期区间过滤，只保留结束日 ≥ today 的条目再筛选 |
| `hn_algolia` | Hacker News (Algolia) | hn.algolia.com/api/v1 | `curl 'https://hn.algolia.com/api/v1/search_by_date?query=%22AI+hackathon%22&tags=story'` | JSON 直取 ✅（免鉴权，2026-07-07 实测） | ⭐⭐⭐⭐ | 关键词监听层：hackathon / challenge / 厂商名，最早捕获官方公告与长尾活动；要 RSS 形式用 hnrss.org（`hnrss.org/newest?q=hackathon`）。**⚠️ 发帖时间 ≠ 活动截止**：数周前的旧帖对应的活动可能仍在报名，必须打开链接核实 deadline 才能按过期丢弃；来不及核实就记入 未覆盖，禁止凭时间戳假设过期 |
| `lablab` | lablab.ai | lablab.ai/ai-hackathons | `site:lablab.ai AI hackathon 2026` | web_extract ✅ / curl ❌ Cloudflare JS 挑战（2026-06-26 确认） | ⭐⭐⭐⭐⭐ | AI 专属平台，信号纯净，有 LIVE/Register/Coming Soon 状态。**降级模式**：DDG `site:lablab.ai` 查询结果含活动名+截止日期+描述，信息密度足够做初筛。确认为 Cloudflare JS 挑战页后不再尝试 curl 直连 |
| `dorahacks` | DoraHacks | dorahacks.io | `site:dorahacks.io AI hackathon 2026` | web_extract ✅（newsletter页） | ⭐⭐⭐⭐ | AI+Web3，`/blog/news/dora-hackathons` 是结构化表格 |
| `tianchi` | 天池（阿里云） | tianchi.aliyun.com/competition | `site:tianchi.aliyun.com 2026 大赛 OR competition` | web_extract ✅ | ⭐⭐⭐⭐⭐ | 国内最结构化的竞赛平台，含标签/奖金/队伍数。**⚠️ `/specials/` 路径为 JS 渲染壳**，curl 仅返回导航文字。用 DDG 搜索获取摘要，或 Firecrawl 提取 |
| `aistudio` | 百度 AI Studio | aistudio.baidu.com | `site:aistudio.baidu.com competition 2026` | web_extract ❌（JS SPA） | ⭐⭐⭐⭐ | 搜索可达，详情页需 Firecrawl JS 渲染 |
| `xfyun` | 讯飞开发者大赛 | challenge.xfyun.cn | `site:challenge.xfyun.cn 2026` | web_extract ❌（反爬） | ⭐⭐⭐⭐ | 搜索可达，提取被拦截，用 Firecrawl stealth |
| `dataagent` | KDD Cup Data Agents | dataagent.top | web_search ✅ / DDG ✅ | ❌ JS SPA (React) | ⭐⭐⭐⭐⭐ | KDD Cup 2026 第二赛道（HKUST 主办），不同于 algo.qq.com 的 Tencent UNI-REC。React SPA 无法 curl 提取，需 DDG 搜索获取摘要 |

### 🌐 社区/社交信号（最早发现渠道，v3 恢复）

| ID | 平台 | 搜索方式 | 数据质量 | 备注 |
|----|------|---------|---------|------|
| `linuxdo` | linux.do | `site:linux.do AI credits OR 福利 OR 活动 OR 赠金 OR 大赛 OR hackathon` | ⭐⭐⭐⭐⭐ | 中文开发者福利/羊毛/credits 第一信号源，v2.0 实测极佳。**降级模式**：搜索 API 被 CF 拦截，但 `curl linux.do/t/topic/ID.json` 可直接获取帖子内容（Discourse JSON API），配合 DDG `site:linux.do` 搜索发现 topic ID |
| `v2ex` | V2EX | `site:v2ex.com AI credits hackathon 2026` | ⭐⭐⭐⭐ | 开发者 credits 讨论/赠金。**⚠️ DDG 查询必须用英文关键词**（中文关键词返回 0 条）。"AI赛事通"月度聚合帖已升级为独立 Tier A 源 `competehub`，此处只做 credits/福利类信号 |
| `twitter_auth` | Twitter/X（认证） | `twitter search "AI hackathon prize 2026" --type latest` | ⭐⭐⭐⭐⭐ | 已配置 cookies，twitter-cli 直连，实时信号最强。**⚠️ 401（cookie过期）和 404（ClientTransaction init failure）两种故障模式**，详见 `tool-fallbacks.md` |
| `x_hackathon` | X/Twitter（搜索） | `site:x.com "AI hackathon" OR "agent hackathon" OR "developer challenge" 2026` | ⭐⭐⭐⭐ | web_search 补充，能发现非平台活动 |
| `x_submissions` | X/Twitter（报名） | `site:x.com submissions open OR registration open AI agent prize 2026` | ⭐⭐⭐⭐ | 发现即将截止和刚开放的活动 |
| `hf_community` | HuggingFace | `site:huggingface.co hackathon OR competition AI 2026` | ⭐⭐⭐⭐ | ML 社区专属活动（Mistral Hack-a-ton、LeRobot 等）。**⚠️ HF org 页面可能显示已结束活动**：如 Agents-MCP-Hackathon（2025-06）仍出现在 DDG 搜索结果中。curl 提取 HF org 页面时需检查日期（`📅 Date:` 字段），避免将旧活动误判为当前活动。建议在 DDG 查询中加 `2026` 过滤 |
| `reddit_hackathon` | Reddit | **`.json`/`.rss` 端点免鉴权**：`curl -A '<UA>' 'https://www.reddit.com/r/hackathons/new.json?limit=25'`；搜索 `https://www.reddit.com/search.rss?q=AI+hackathon&sort=new` | ⭐⭐⭐⭐ | 社区草根活动，很多不在主流平台出现。任意 subreddit/搜索加 `.json` 或 `.rss` 即结构化（有速率限制）；DDG `site:reddit.com` 搜索作兜底 |

### 📢 通用发现查询（广撒网，捕获漏网之鱼）

| ID | 查询 | 语言 | 数据质量 | 备注 |
|----|------|------|---------|------|
| `broad_en` | `"AI hackathon" OR "agent hackathon" OR "developer challenge" prize deadline 2026` | EN | ⭐⭐⭐⭐⭐ | 单次最高 ROI 查询，捕获 MIT/Google Cloud/小众活动 |
| `broad_en_simple` | `AI hackathon developer challenge 2026 prize register` | EN | ⭐⭐⭐⭐ | **新发现（2026-06-27）**：平铺关键词无 OR 无 site: 的简单查询，DDG 可靠性最高（10/10 命中）。推荐作为 broad_en 的首选查询模式 |
| `broad_zh` | `"AI 大赛" OR "智能体大赛" OR "编程马拉松" OR "开发者挑战赛" 报名 2026` | ZH | ⭐⭐⭐⭐ | 国内生态全覆盖（DJI/天池/讯飞/华为） |
| `wechat_proxy` | `微信公众号 AI 大赛 OR hackathon OR 开发者挑战赛 OR 黑客松 报名 2026` | ZH | ⭐⭐⭐ | 公众号内容通过搜狗/搜索引擎间接覆盖 |
| `google_alerts` | `AI hackathon OR competition cash prize submissions open 2026 -site:facebook.com -site:instagram.com` | EN | ⭐⭐⭐⭐⭐ | Google Alerts 等效广撒网查询 |

---

## Tier B：每周深扫（周三 + 周日各选一半覆盖）

### 🏗️ 补充聚合平台（GPT 推荐全量覆盖）

| ID | 平台 | 搜索方式 | 提取方式 | 数据质量 | 备注 |
|----|------|---------|---------|---------|------|
| `mlh` | MLH | `site:mlh.io hackathon AI 2026` | web_extract ✅（/seasons/2026/events） | ⭐⭐⭐ | 学生/校园为主，有 Global Hack Week: Agents。无公开 API（MyMLH OAuth 仅用于报名），AI 垂直度一般，降为低频 |
| `hackerearth` | HackerEarth | `site:hackerearth.com AI hackathon 2026` | web_extract ❌ | ⭐⭐⭐ | 企业/招聘型活动多，搜索可达 |
| `hack2skill` | Hack2Skill | `site:hack2skill.com AI hackathon 2026` | web_extract ❌ / **curl ❌ 全站 JS SPA**（2026-06-27 确认所有子页面） | ⭐⭐⭐ | 印度/企业活动，ISRO/Google/Intel 合作。**⚠️ 全站 React SPA**：hack2skill.com 和 vision.hack2skill.com 所有页面 curl 返回 9KB 空壳。只能通过 DDG 搜索获取摘要（snippet 含活动名/截止日期/描述）|
| `devfolio` | Devfolio | devfolio.co/hackathons/open | web_extract ❌ / 有内部 API（社区有示例）与官方 MCP，接入前先验证 | ⭐⭐⭐ | 印度/全球 hackathon 大户，$250K+ 奖池活动，与 Devpost 重叠低 |
| `kaggle` | Kaggle | **官方 CLI**：`kaggle competitions list --sort-by latestDeadline`（需免费 API token；**本机未装，待配置**） | CLI 结构化输出 ✅（装好后） | ⭐⭐⭐⭐ | AI/ML 竞赛权威源，与 Devpost 几乎零重叠。未配置 token 前用 `site:kaggle.com competitions AI 2026` 搜索兜底 |
| `aicrowd` | AIcrowd | `site:aicrowd.com AI challenge 2026` | web_search | ⭐⭐⭐ | AI 竞赛平台，ML 挑战赛 |
| `angelhack` | AngelHack | `site:angelhack.com hackathon AI 2026` | web_search | ⭐⭐⭐ | 全球 hackathon 运营商 |
| `unstop` | Unstop | `site:unstop.com AI hackathon 2026` | web_search | ⭐⭐⭐ | 印度/亚太挑战赛平台，Google/AWS 企业活动常在此发布 |
| `datafountain` | DataFountain | `site:datafountain.cn 2026 大赛` | web_extract ✅ | ⭐⭐⭐ | 国内数据竞赛平台 |
| `eventbrite` | Eventbrite | `site:eventbrite.com AI hackathon 2026` | web_search | ⭐ | **公开搜索 API 已于 2020 年关闭**，无法做跨平台发现；仅搜索兜底，最低优先级 |
| `meetup` | Meetup | `site:meetup.com AI hackathon developer 2026` | web_search | ⭐⭐ | 本地社区活动，信号密度低 |
| `hackernoon_hackathons` | HackerNoon Hackathons | `hackernoon.com/technology-hackathons` curl ✅ | curl 直连 | ⭐⭐⭐ | **新发现（2026-06-27）**：活跃 hackathon 列表页（含 Decentralize AI Hackathon $51K+），可 curl 获取 HTML。信息含赞助商/奖金/参赛机制。适合 Tier B 深扫 |
| `ethglobal_events` | ETHGlobal Events | `ethglobal.com/events` curl ⚠️ | curl 直连 ⚠️ | ⭐⭐⭐ | 结构化活动列表含日期/地点/类型，Web3+AI 交叉。**⚠️ URL 复用坑**：`/events/{slug}` 会返回旧年份数据，需经 DDG 或 AgentDeadlines 确认最新年份 |
| `dev_events` | dev.events | dev.events/hackathons | **RSS**：`curl 'https://dev.events/rss.xml'`（2026-07-07 实测 ✅，支持分类过滤） | RSS ✅ | ⭐⭐⭐⭐ | 策展型开发者会议/黑客松聚合，含 iCal/日历视图，覆盖 Devpost 之外的线下活动 |
| `openai_rss` | OpenAI News | openai.com/news | **官方 RSS**：`curl 'https://openai.com/news/rss.xml'`（2026-07-07 实测 200 text/xml） | RSS ✅ | ⭐⭐⭐⭐ | 大厂官方活动/hackathon 公告最干净的可订阅入口（旧 /blog/rss.xml 已 302 到此） |
| `cerebral_valley` | Cerebral Valley | cerebralvalley.ai/events + /hackathons | 抓列表页 / 订阅其 Luma 日历 `luma.com/cerebralvalley_` | HTML / iCal | ⭐⭐⭐⭐ | SF/NY 高质量 AI hackathon 与大会的核心策展源，**与 Devpost 几乎零重叠** |
| `luma_ical` | Luma Discover（iCal） | luma.com/ai、luma.com/deepmind、luma.com/cerebralvalley_ | **iCal 订阅**（Discover/日历页均支持） | iCal ✅ | ⭐⭐⭐⭐ | AI 线下活动事实聚合地。官方 API 需付费、内部 JSON 端点不稳定（实测 404）——**只走 iCal，不要反推内部接口** |
| `tencent_hackathon` | 腾讯云黑客松官网 | tch.cloud.tencent.com | curl + UA ✅（2026-07-07 实测 200/105KB；单赛事 `/contest/{数字ID}` 可遍历） | HTML 结构化 ✅ | ⭐⭐⭐⭐ | 大厂官方黑客松专站：AI Agent 争霸赛/AI Coding 黑客松（含新加坡场）等，含状态/奖金/日期 |
| `volcengine_activity` | 火山引擎活动页 | developer.volcengine.com/activities | curl -L + UA ✅（2026-07-07 实测：`/activity` 302 → `/activities`，200/177KB） | HTML 结构化 ✅（未开始/进行中/已结束分段） | ⭐⭐⭐⭐ | 字节系官方活动：ADG 城市巡回、AI Agent 工作坊、动手实验挑战，更新勤 |
| `huodongxing` | 活动行 | huodongxing.com/eventlist?tag=IT互联网 | curl 列表页（免登录可浏览，可按时间/城市/状态筛） | HTML 结构化 | ⭐⭐⭐⭐ | 国内活动发布头部平台，AI 线下活动覆盖最广的通用源。**二级站模式**：`{slug}.huodongxing.com` 可订阅特定主办方（极客公园=geekpark.huodongxing.com） |

### 🌐 中文社区（GPT 推荐全量覆盖）

| ID | 平台 | 搜索方式 | 数据质量 | 备注 |
|----|------|---------|---------|------|
| `juejin` | 掘金 | `site:juejin.cn AI大赛 OR hackathon OR 创造力大赛 OR "AI赛事通" 2026` | ⭐⭐⭐⭐ | "AI赛事通" 月度聚合帖很有价值（单帖列出 112 场大赛） |
| `csdn` | CSDN | `site:csdn.net AI大赛 OR 开发者大赛 OR hackathon 2026` | ⭐⭐⭐ | 大赛报道和聚合帖 |
| `infoq_cn` | InfoQ 中国 | `site:infoq.cn AI大赛 OR hackathon 2026` | ⭐⭐⭐⭐ | 深度报道，含技术细节 |
| `oschina` | 开源中国 | `site:oschina.net hackathon OR 大赛 2026` | ⭐⭐⭐ | 开源/量子/AIGC 活动 |
| `jiqizhixin` | 机器之心 | `site:jiqizhixin.com AI大赛 OR hackathon OR 竞赛 2026` | ⭐⭐⭐ | AI 行业媒体报道 |
| `qbitai` | 量子位 | `site:qbitai.com AI大赛 OR hackathon OR 竞赛 2026` | ⭐⭐⭐ | AI 行业媒体报道 |
| `sfchina` | SegmentFault 活动页 | 直抓 `segmentfault.com/events`（分「进行中/过往」，含城市与线上线下） | ⭐⭐⭐⭐ | 2026-07 验证有大量 AI 活动（TRAE 创造力大赛、Agentic AI Summit 等），开发者活动质量高、AI 占比大 |
| `waytoagi` | WayToAGI | 官网 `waytoagi.com/events` + **飞书公开 wiki**（waytoagi.feishu.cn/wiki，可抓） | ⭐⭐⭐⭐ | AI 垂直社区：黑客松/创新赛/训练营，社区日更；官网+飞书文档双通道，采集友好 |

### 🏭 厂商活动页（GPT 推荐全量 watchlist，轮换覆盖）

> **大模型初创厂商（智谱/Kimi/DeepSeek/MiniMax/阶跃）均无公开活动页**（2026-07 调研确认），
> 活动走公众号/微信群/魔搭/天池发布。不必逐家死磕搜索——`competehub` + `aihot` + `huodongxing` +
> 天池/魔搭已能二手覆盖其绝大多数公开活动，下表对应行仅作低频兜底。

| ID | 厂商 | 搜索方式 | 备注 |
|----|------|---------|------|
| `google_dev` | Google Developers | `site:developers.google.com events OR hackathon Gemini 2026` | Build with AI / Gemini API Sprints |
| `slack_dev` | Slack Developers | `site:slack.dev challenge OR hackathon 2026` | Agent Builder Challenge（$42K） |
| `anthropic` | Anthropic | `site:anthropic.com hackathon OR competition OR beta program 2026` | Fellows / events page |
| `microsoft` | Microsoft | `site:microsoft.com developer challenge OR hackathon AI 2026` | Build / Azure AI |
| `aws` | AWS | `site:aws.amazon.com developer challenge OR hackathon 2026` | AWS Activate / Hackathon |
| `nvidia` | NVIDIA | `site:nvidia.com developer challenge OR hackathon AI 2026` | GTC / developer programs |
| `huawei` | 华为 | `site:developer.huawei.com 活动 OR 大赛 OR 激励 OR 鸿蒙 2026` | 天工计划/鸿蒙激励 |
| `aliyun` | 阿里云 | `site:developer.aliyun.com 活动 OR 大赛 2026` | 天池/AI 创新大赛 |
| `bytedance` | 字节/Trae | `Trae OR 豆包 AI大赛 OR 创造力大赛 OR hackathon 2026` | Trae 创造力大赛 |
| `baidu` | 百度飞桨 | `site:aistudio.baidu.com OR site:paddlepaddle.org.cn 大赛 2026` | 飞桨开发者大赛 |
| `tencent` | 腾讯云 | `site:cloud.tencent.com 开发者 OR 大赛 2026` | 腾讯云开发者活动 |
| `volcengine` | 火山引擎 | 首选 Tier B `volcengine_activity`（结构化活动页）；搜索兜底 | — |
| `openai` | OpenAI | 首选 Tier B `openai_rss`（官方 RSS）；搜索兜底 `site:openai.com hackathon OR beta program 2026` | RSS 已实测可用 |
| `vercel` | Vercel | `site:vercel.com hackathon OR challenge 2026` | v0 / Next.js 生态 |
| `cloudflare` | Cloudflare | `site:developers.cloudflare.com challenge 2026` | 实测无信号，低优先级 |
| `github` | GitHub Blog | `site:github.blog hackathon OR developer program 2026` | — |
| `modelscope` | 魔搭 | `site:modelscope.cn 活动 OR 大赛 2026` | ModelScope 社区 |
| `zhipu` | 智谱 | `site:zhipuai.cn OR 智谱 GLM 活动 OR 大赛 OR 内测 2026` | — |
| `deepseek` | DeepSeek | `DeepSeek 活动 OR 开发者 OR credits 2026` | — |
| `minimax` | MiniMax | `MiniMax 海螺 活动 OR credits OR 内测 2026` | — |
| `moonshot` | Moonshot/Kimi | `Kimi 月之暗面 活动 OR 内测 OR 福利 2026` | — |
| `hf_events` | HuggingFace Events | `site:huggingface.co/events` | 直接活动页面 |
| `aitinkerers` | AI Tinkerers | 城市子站（如 sf.aitinkerers.org）+ Luma 日历 | 245 城全球 AI builder 网络，大量线下 hackathon/meetup |
| `gdg` | GDG Community | `site:gdg.community.dev events 2026` | Google Developer Groups |

---

## Tier C：按需/发现后深入

| ID | 平台 | 搜索方式 | 备注 |
|----|------|---------|------|
| `gitee` | Gitee | `site:gitee.com 大赛 2026` | 竞赛代码仓库，非发现平台 |
| `jiqizhixin` | 机器之心 | `site:jiqizhixin.com AI大赛 2026` | 大型赛事报道 |
| `cloudflare` | Cloudflare | `site:developers.cloudflare.com hackathon` | ❌ 实测无信号，降级 |
| `producthunt` | Product Hunt | `site:producthunt.com AI free credits` | 偏产品上线，非活动聚合 |
| `hackmap` | hackmap.io | DDG 搜索命中具体事件 URL 时 curl 提取 | ⚠️ 主页为纯 JS 交互地图，HTML 不含事件数据。2026-06-26 实测确认不可作为独立扫描源，仅在已有具体事件 URL 时辅助提取 |
| `info_ms` | Microsoft Events | `site:info.microsoft.com hackathon 2026` | 2026-06-26 DDG broad_en 发现 Agents League Hackathon（$55K）。厂商注册页模式，可在 Tier B 厂商活动扫描中覆盖 |
| `ainave` | ainave.com | `site:ainave.com hackathon 2026` / DDG broad 搜索命中 | 日本/亚太 DeepTech 活动聚合器，2026-06-26 DDG 广撒网发现。信号质量 ⭐⭐⭐，偏日语/亚太市场，部分活动面向特定区域创始人。适合作为 broad_en 查询的附带命中源 |
| `decentralizeai` | DecentralizeAI.tech | DDG broad 搜索命中 | HackerNoon 旗下 Decentralize AI Hackathon 主站（2026-06-27 发现），Web3+AI 基础设施方向。可通过 hackernoon.com/technology-hackathons 发现 |

### 🎓 学术竞赛层（月度扫一次即可，deadline 周期长）

| ID | 平台 | 采集方式 | 备注 |
|----|------|---------|------|
| `neurips_comp` | NeurIPS Competition Track | 抓 `neurips.cc/Conferences/<年份>/CallForCompetitions` + blog.neurips.cc | 顶会竞赛权威源，大量 LLM/agent 评测赛，奖金常见 $50K+ |
| `openreview` | OpenReview | **有公开 API**：group `NeurIPS.cc/<年份>/Competition_Track` | 竞赛提案的结构化入口 |
| `wikicfp` | WikiCFP | **分类页有 RSS**：`wikicfp.com/cfp/call?conference=artificial+intelligence` | AI/ML 会议 CFP 聚合，含 workshop/challenge deadline |

### 🧑‍🤝‍🧑 国内黑客松组织方（低频官网直抓，更新以「届」为单位）

| ID | 组织 | 采集方式 | 备注 |
|----|------|---------|------|
| `zhenfund` | 真格基金黑客松 | curl `zhenfund.com/Hackathon`（结构化，量小可整页解析） | AI 创业向黑客松（Level Up! AI Game 等），质量高、意外好抓 |
| `adventurex` | AdventureX | 官网 `adventure-x.org`（静态） | 中国最大青年黑客松，年度制，低频人工级抓取即可 |
| `geekpark_hdx` | 极客公园/Founder Park | **活动行二级站** `geekpark.huodongxing.com`（主域 geekpark.net 有抓取风控） | IF 大会 / AGI Playground / Founder Park Meetup 的报名多走活动行+飞书表单 |
| `hackathonweekly` | HackathonWeekly | ⚠️ `/events` 列表**有登录墙**，公开抓不到；走其公众号（经 `aihot` / 搜狗微信间接覆盖） | 深杭北高频周更社区，价值高但公开自动化受限 |
| `datawhale_baseline` | Datawhale competition-baseline | **GitHub API 监控** `datawhalechina/competition-baseline` 的 commit | Datawhale 不维护活动日历；该仓库更新 = 「哪些国内竞赛值得关注」的策展信号 |

### 📨 私域兜底（半自动，不追求全自动）

| ID | 途径 | 采集方式 | 备注 |
|----|------|---------|------|
| `sogou_weixin` | 搜狗微信搜索 | weixin.sogou.com 关键词检索（"黑客松 报名"/"AI 大赛 招募"） | **公众号内容唯一通用公开入口**，但反爬极强（验证码/时效 token/链接过期），只做人工触发的半自动巡检；日常靠 `aihot`（带公众号原文链接）间接覆盖 |

---

## 采集坑汇总（2026-07-07 实测）

- **403/风控，需真实浏览器 UA 或无头浏览器**：competehub.dev、aistudio.baidu.com、geekpark.net、miracleplus.com。带 Chrome UA 的 curl 通常即可（CompeteHub 已验证）。
- **JS SPA，直抓 HTML 拿不到数据，必须走各自 JSON 接口或无头浏览器**：天池、DataFountain、掘金、魔搭 ModelScope、华为云、阿里云开发者、hack2skill、dataagent。
- **登录墙**：HackathonWeekly `/events`。
- **重定向**：火山引擎 `/activity` → `/activities`（curl 加 `-L`）。
- **域名注意**：互动吧用 `hudongba.com`（`www.hdb.com` 证书不匹配）。

---

## 扫描时间预算分配

### 每日巡检（5 分钟，12-15 次工具调用）

| 步骤 | 调用次数 | 来源 |
|------|---------|------|
| 读取 seen 记录 | 1 | 本地 |
| 结构化端点直取 | 3-4 | agentdeadlines(JSON-LD) + devpost(JSON API) + competehub + aihot |
| Tier A 补充搜索 | 2-3 | hn_algolia + (lablab / tianchi / dorahacks 轮换) |
| Tier A 社区信号 | 1-2 | x_hackathon + (linuxdo / reddit 轮换) |
| Tier A 通用发现查询 | 0-1 | broad_en OR broad_zh 轮换（结构化源已覆盖大盘，仅捕漏网） |
| 提取详情页 | 2-3 | 候选活动的详情页 |
| 写入 seen 记录 | 1 | 本地 |
| **合计** | **12-15** | |

### 每周深扫（周日额外执行，8-10 分钟）

| 步骤 | 说明 |
|------|------|
| Tier B 结构化源 | dev_events(RSS) + openai_rss + tencent_hackathon + volcengine_activity + huodongxing |
| Tier B 聚合平台 | kaggle + cerebral_valley + (hackerearth / devfolio / datafountain 轮换) |
| Tier B 中文社区 | sfchina(events) + waytoagi + (juejin / csdn / infoq_cn 轮换) |
| Tier B 厂商活动页 | 每次选 2-3 个厂商（轮换覆盖） |
| Tier C 学术层 | 每月首个周日扫 neurips_comp + wikicfp |
| 已报名活动截止提醒 | 检查 seen 中状态为"已报名"的活动截止时间 |

---

## 信源质量追踪

发现新活动时，记录"首次出现源"。如果某个源持续产出独家信号，提升其优先级；如果某源连续 10 次巡检无新信号，降级或移除。

**反馈闭环**：每次"知道晚了"的活动 → 反推最早出现的源 → 加入注册表。
