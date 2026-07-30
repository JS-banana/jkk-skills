# Find Bounty - MCP Enhancement Guide

## 当前状态
✅ Exa MCP — 已配置（远程 HTTP 端点）
✅ Firecrawl MCP — 已配置（stdio npx）
✅ Tavily MCP — 已配置（远程 HTTP 端点）

然后重启 Hermes：`hermes restart` 或重启 gateway 进程。

## ⚠️ 配置踩坑

### API Key 管理
所有 key 一律从环境变量读取（如 `FIRECRAWL_API_KEY`），**不要把 key 明文写进本仓库任何文件**——
本文档曾内嵌过一个 Firecrawl key，已移除；需在 Hermes 服务器和本机各自配置环境变量。

Hermes 的工具输出 redaction 系统会截断 API key 模式串。用工具写 config.yaml 时，不要把完整 key 放在单个 Python 字符串中：
```python
# ❌ 会被截断
key = "fc-<完整key>"
# ✅ 从环境变量读取（同时规避 redaction）
key = os.environ["FIRECRAWL_API_KEY"]
```

### hermes mcp add 交互式提示
`hermes mcp add` 在非 TTY 环境下会卡在交互式确认。直接编辑 config.yaml 更可靠。

详见 `native-mcp` skill 的 Pitfalls 章节。

## 增强方案：接入 MCP 服务器

### 1. Exa MCP（推荐优先接入）

**能力**：语义搜索，比关键词搜索更精准，能找到语义相关但关键词不同的内容
**免费额度**：1,000 requests/月
**工具**：`web_search_exa`（语义搜索）、`web_fetch_exa`（页面抓取）

```bash
# 方式 A：使用远程端点（推荐，无需 npx）
hermes mcp add exa --url https://mcp.exa.ai/mcp

# 需要在 config.yaml 中添加 env:
# mcp_servers:
#   exa:
#     url: https://mcp.exa.ai/mcp
#     env:
#       EXA_API_KEY: "your-key-here"
```

**申请 API key**：https://dashboard.exa.ai/api-keys （注册即送 1k/月）

**对巡检的价值**：
- 用语义搜索替代关键词搜索，召回率更高
- 例如搜索 "AI companies offering free credits or beta programs" 能找到关键词搜不到的内容
- `web_fetch_exa` 可以抓取 JS 渲染页面

### 2. Firecrawl MCP

**能力**：专业网页爬取、批量抓取、变化监控、结构化提取
**免费额度**：1,000 pages/月
**工具**：`firecrawl_scrape`、`firecrawl_batch_scrape`、`firecrawl_search`、`firecrawl_monitor_*`

```bash
# 安装
hermes mcp add firecrawl --command npx --args '-y firecrawl-mcp'

# 需要在 config.yaml 中添加 env:
# mcp_servers:
#   firecrawl:
#     command: npx
#     args: ['-y', 'firecrawl-mcp']
#     env:
#       FIRECRAWL_API_KEY: "your-key-here"
```

**申请 API key**：https://www.firecrawl.dev/app/api-keys （注册即送 1k/月）

**对巡检的价值**：
- `firecrawl_search` 可以直接搜索+抓取一体化
- `firecrawl_monitor` 可以监控厂商活动页面变化
- 能处理 JS 重度渲染的页面（小红书等）

### 3. Tavily MCP（增强版）

**能力**：在内置 tavily 基础上增加 crawl（整站爬取）和 map（站点地图）能力
**工具**：`tavily-search`、`tavily-extract`、`tavily-map`、`tavily-crawl`

```bash
# 方式 A：远程端点
hermes mcp add tavily --url "https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_KEY"

# 方式 B：stdio
hermes mcp add tavily --command npx --args '-y tavily-mcp@latest'
```

**对巡检的价值**：
- `tavily-map` 可以发现厂商网站的所有活动页面
- `tavily-crawl` 可以整站爬取厂商博客/news

## 接入优先级
1. **Exa** - 投入最小（远程端点），收益最大（语义搜索）
2. **Firecrawl** - 解决 JS 渲染页面和变化监控
3. **Tavily MCP** - 内置 tavily 已够用，增强版锦上添花

## 一键配置模板

拿到 API key 后，在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  exa:
    url: https://mcp.exa.ai/mcp
    headers:
      x-api-key: "YOUR_EXA_API_KEY"
    timeout: 60
  firecrawl:
    command: npx
    args: ['-y', 'firecrawl-mcp']
    env:
      FIRECRAWL_API_KEY: "YOUR_FIRECRAWL_API_KEY"
    timeout: 120
```

然后重启 Hermes：`hermes restart` 或 `/reload-mcp`
