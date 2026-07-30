# AI 活动雷达 — Feishu Base Contract

The live Feishu Base is the source of truth. This file is a cache of the
verified write contract, not a replacement for `lark-cli base +field-list`.

Do not store Base tokens, wiki URLs, cookies, app IDs, or app secrets in this
skill. The table ID can be public in this package; use the current `lark-cli`
user auth and pass the Base token at runtime.

Verified with `lark-cli` on 2026-06-30:

- Base token: user-provided at runtime
- Table ID: `tblYhMRh3fJ0FDfW`
- Time zone: `Asia/Shanghai`

## Read Live State

Use user identity by default. The caller provides the target Base:

```bash
export AI_CAMPAIGN_BASE_TOKEN="..."

lark-cli base +base-get \
  --base-token "$AI_CAMPAIGN_BASE_TOKEN" \
  --as user --format json

lark-cli base +field-list \
  --base-token "$AI_CAMPAIGN_BASE_TOKEN" \
  --table-id tblYhMRh3fJ0FDfW \
  --as user --format json

lark-cli base +view-list \
  --base-token "$AI_CAMPAIGN_BASE_TOKEN" \
  --table-id tblYhMRh3fJ0FDfW \
  --as user --format json
```

## Live Fields

There are 22 fields in the live table.

| Field | Type | Write shape |
|---|---|---|
| 活动名称 | text | string |
| 厂商 | select | existing option, or `其他` |
| 活动类型 | select | whitelist option |
| 难度评级 | select | existing option |
| 推荐指数 | select | star string: `⭐` to `⭐⭐⭐⭐⭐` |
| 难度说明 | text | string |
| 奖励详情 | text | string |
| 活动形式 | text | string |
| 参与方式 | text | string |
| 获奖条件 | text | string |
| 时间节点备注 | text | string |
| 状态 | select | existing option |
| 报名入口 | URL-style text | bare URL through sync script |
| 官方确认 | select | existing option |
| 开始时间 | datetime | ms timestamp through sync script |
| 截止时间 | datetime | ms timestamp through sync script |
| 地区 | select | existing option |
| 奖励类型 | select with `multiple=true` | JSON array of existing options |
| 发现日期 | datetime | ms timestamp through sync script |
| 来源渠道 | select | existing option |
| 预计投入 | select | existing option |
| 建议 | select | `立即行动` / `值得做` / `观望` / `跳过` |

No live `活动详情链接` field exists. Put a secondary details URL in `奖励详情`,
`时间节点备注`, or `我的备注` only if such a field is later added and verified.

## Canonical Options

Use canonical options unless the live field list proves a better exact match.

- `活动类型`: `Hackathon`, `开发者挑战赛`, `开发者激励`, `AI竞赛`, `内测体验`,
  `福利发放`, `内容创作`, `其他`
- `状态`: `新发现`, `已报名`, `进行中`, `已完成`, `已跳过`, `已过期`
- `官方确认`: `✅ 官方确认`, `⚠️ 疑似`, `❌ 非官方`
- `奖励类型`: `现金`, `API Credits`, `会员权益`, `实物`, `证书`, `其他`
- `地区`: `全球`, `中国`, `北美`, `亚太`, `欧洲`, `日本`, `其他`
- `预计投入`: `1小时内`, `半天`, `1-3天`, `2-3天`, `3-7天`, `1周+`,
  `1-2周`, `7天+`, `长期投入`
- `推荐指数`: `⭐`, `⭐⭐`, `⭐⭐⭐`, `⭐⭐⭐⭐`, `⭐⭐⭐⭐⭐`

The live `难度评级` field has many historical duplicate options. Prefer these
five unless an exact live option is needed:

- `⭐ 轻松领取`
- `⭐⭐ 简单参与`
- `⭐⭐⭐ 需花时间`
- `⭐⭐⭐⭐ 需技术能力`
- `⭐⭐⭐⭐⭐ 专业挑战`

## Write Contract

Write new records through `campaign_bitable_sync.py --write`.

Minimum JSON:

```bash
python3 scripts/campaign_bitable_sync.py \
  --base-token "$AI_CAMPAIGN_BASE_TOKEN" \
  --write '{
  "vendor": "OpenAI",
  "campaign": "Example AI Challenge",
  "seen_at": "2026-06-30",
  "score": 4,
  "url": "https://example.com/register",
  "活动类型": "开发者挑战赛",
  "来源渠道": "官网",
  "奖励类型": ["API Credits"],
  "官方确认": "✅ 官方确认"
}'
```

In Hermes, the deployed script may live at
`~/.hermes/scripts/campaign_bitable_sync.py`. In this repo, use
`plugins/banana/skills/find-bounty/scripts/campaign_bitable_sync.py`.
Both paths require `--base-token` or `AI_CAMPAIGN_BASE_TOKEN`; `--table-id` or
`AI_CAMPAIGN_TABLE_ID` is only needed when overriding the bundled default table.

Rules:

- `score` may be `1-5`, a legacy `5-25` score, or a star string. The script
  writes `推荐指数` as a star select value.
- Date overrides such as `截止时间` and `开始时间` must be integer millisecond
  timestamps when using the sync script.
- `奖励类型` must be an array, even for one value; lark-cli reports it as
  `type=select` with `multiple=true`.
- Do not pass `活动详情链接`.
- Do not create unknown select options unless the user explicitly wants schema
  changes. Prefer `其他` for uncertain vendor/source values.
- The sync script skips a write when the normalized `报名入口` URL (lowercase
  host + path + query) already exists in the table — cross-source duplicates
  carry different titles but the same entry URL. Because of this, `报名入口`
  must be the campaign-specific page, never a portal homepage (e.g.
  `challenge.xfyun.cn` hosts many campaigns; a homepage URL collides with the
  next campaign from the same portal and gets dropped as a duplicate).

## Views

| View | How to resolve | Current filter note |
|---|---|---|
| 全部活动 | resolve live | no filter |
| 高价值 | resolve live | do not rely on the name without checking filters |
| 按厂商 | resolve live | grouped by 厂商 |
| 看板 | resolve live | usually grouped by 状态 or 厂商; inspect live config |
| 即将截止 | resolve live | check rolling date filter before relying on it |
| 甘特图 | resolve live | timebar should use 开始时间 / 截止时间 / 活动名称 |

Check filters before relying on a view:

```bash
lark-cli base +view-get-filter \
  --base-token "$AI_CAMPAIGN_BASE_TOKEN" \
  --table-id tblYhMRh3fJ0FDfW \
  --view-id "即将截止" \
  --as user --format json
```

## Common Failures

- `推荐指数` is a select field in the live Base, not a Number. Direct writes
  must use star strings.
- `活动详情链接` is absent in the live table and will cause `FieldNameNotFound`.
- Feishu date fields require millisecond timestamps through the sync script.
- Multiselect values must be arrays.
- View names can drift from filters; inspect filters before treating a view as
  a rule.
- Select fields reject unknown option values (`800030005 not_found`); this
  table does NOT auto-create options. A new vendor/channel needs its option
  added first via `lark-cli base +field-update`.
- ⚠️ **Option-append incident (2026-07-08)**: `+field-search-options` defaults
  to `--limit 30` — reading "all" options without `--limit 200` and then doing
  a full-PUT `+field-update` truncated `厂商` from 60 to 33 options and wiped
  the cell values of 35 records (restored from the website's snapshot.json).
  Before ANY `+field-update` on a select field: read options with
  `--limit 200`, append to the complete list, and read back verifying every
  pre-existing option name survived. Readback can lag a second or two; retry
  before concluding failure.
- `+record-list` in lark-cli 1.0.5x returns columnar `{fields: [名...],
  data: [[行]...]}`, not `items[].fields` dicts. `list_existing_campaigns` in
  the sync script handles both shapes; if dedupe suddenly reports 0 existing
  records against a non-empty table, suspect a response-shape change first.
