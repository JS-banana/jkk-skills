# AgentDeadlines.com — Content Structure & Extraction Guide

> Discovered 2026-06-21. AI Agent hackathon/competition deadline aggregator.
> Single `web_extract("https://agentdeadlines.com")` call returns structured content covering 31+ active events.

## Content Structure

The page organizes events into time-based buckets:

```
## This Week (N Events)
* **Event Name** (Deadline Date) — Format, **Prize**. Description. #tags

## This Month (N Events)
* ...

## Coming Up (N Events)
* ...

## Later (N Events)
* ...
```

## Fields Available Per Event

From the extracted markdown, each event entry typically contains:
- **Name**: Event title
- **Deadline**: Date in parentheses (Mon DD, YYYY format)
- **Format**: Online / Hybrid / In-person
- **Prize**: Dollar amount or description
- **Tags**: Hashtag-style tags (#hackathon#agent#MCP#Google-Cloud)
- **Brief description**: One-liner with key details

## 样本事件（快照，非实时）

> 以下为 2026-06-21 首次抓取时的部分事件，仅说明数据结构。**每次都应重新提取**，不要依赖此表。

| Event | Deadline | Prize | Format |
|-------|----------|-------|--------|
| KDD Cup 2026 — Tencent UNI-REC | Jul 31 | $885,000 | Online |
| ARC Prize 2026 | Nov 1 | $1,000,000+ | Online |
| Amazon Nova AI Challenge | Sep 30 | $700,000 | Hybrid |
| AGIBOT World Challenge | Jun 30 | $530,000 | Hybrid |
| RAISE Summit AI Hackathon | Jul 9 | €250,000+ | In-person (Paris) |
| Slack Agent Builder Challenge | Jul 13 | $42,000 | Online |
| AWS AI League 2026 | Sep 30 | $50,000 | Hybrid |

## Extraction Notes

- `web_extract` returns clean markdown — no JS rendering needed
- Content is well-structured for LLM parsing
- Page may update as events close/new ones appear — always re-extract fresh
- Pair with `web_search` for individual event details (registration links, rules, etc.)
- The page does NOT include registration URLs — only event names and deadlines. Follow up with targeted search to find actual registration links.

## endDate 字段语义注意事项（2026-06-26 实测踩坑）

AgentDeadlines JSON-LD 中的 `endDate` 字段含义因活动而异：

| 含义 | 举例 | 判断方法 |
|------|------|---------|
| **提交截止日**（最常见） | UiPath AgentHack: endDate=2026-06-29 = submission deadline | Devpost 页面确认 "Deadline: Jun 29" |
| **活动/赛事正式结束日**（非提交截止） | Berkeley AgentX: endDate=2026-06-30，但 Sprint 4 提交截止已于 6/2 过期 | description 中提到 "Sprint 4 grand finale" 已结束 |
| **长期活动结束日** | AWS AI League: endDate=2026-12-04，但分阶段（各 AWS Summit 资格赛） | 需看 description 了解分阶段结构 |

**实操影响**：
- `endDate < today` 的活动**可以安全剔除**（已结束）
- `endDate > today` 的活动**不一定还能报名** — 需要检查 description 是否提到提交截止日已过
- 多阶段活动（如 KDD Cup、ARC Prize）的 endDate 是赛事结束日，不代表最后提交窗口
- **安全做法**：过滤后对每个活动检查 description 中是否有 "submission deadline" 或 "submit by" 相关描述

## 补充信源发现

### ainave.com（2026-06-26 发现）
- 日本/亚太 DeepTech 活动聚合器，DDG 广撒网查询可发现其条目
- 示例：India × Japan DeepTech and AI Venture Challenge 2026
- 信号质量：⭐⭐⭐，偏日语/亚太市场，部分活动面向特定区域创始人
- 适合作为 Tier B 补充源，在 broad_en 查询中偶尔会命中

### hackmap.io（已知）
- curl 直连可达，含 devpost 活动镜像
- 适合 devpost 不可达时的降级替代

## ROI Assessment

- **2026-06-21 实测**：1 次 web_extract 调用 → 发现 4 个未见高价值活动（$885K + €250K + $2M + $50K）
- **2026-06-26 降级实测**：curl JSON-LD → 20 个活跃活动，其中 11 个已过期。与 seen 记录比对后 0 个新增，但确认了 1 个 P0 截止提醒（UiPath 4 天）
- **信号密度极高**：单页信息量相当于 3-4 次 web_search 的总和
- **推荐用法**：作为每日巡检第一步，快速获取全貌后再针对性搜索详情
- **降级模式效率**：完整 AgentDeadlines + 6 次 DDG + 5 次 curl 详情页 = ~18 次工具调用，约 3-4 分钟完成
