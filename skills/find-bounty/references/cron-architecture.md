# Cron 执行架构问题与解决方案

## 问题背景

2026-06-19 巡检 cron job 运行时，脚本 `vendor_campaign_scan.py` 失败：

```
ModuleNotFoundError: No module named 'hermes_tools'
```

脚本在 line 14 尝试 `from hermes_tools import web_search, web_extract`，但 `hermes_tools` 不是一个可安装的 Python 包——它是 Hermes 的 `execute_code` 工具在运行时注入到子进程的命名空间。

## 失败路径分析

### 路径 1：Cron script 模式（失败）
- Cron job 配置 `script: vendor_campaign_scan.py`
- Cron executor 直接调用 `python3 vendor_campaign_scan.py`
- `hermes_tools` 不在 `sys.path` 中 → `ModuleNotFoundError`

### 路径 2：execute_code 代理模式（失败）
- Agent 尝试用 `execute_code` 包裹数据收集逻辑
- Cron 模式下 `execute_code` 被 BLOCKED
- 错误信息：`"execute_code runs arbitrary local Python (including subprocess calls that bypass shell-string approval checks). Cron jobs run without a user present to approve it."`

### 路径 3：Agent 直接扫描（✅ 成功）
- Cron job 不配置 script，prompt 指示 agent 加载 skill 并直接调用 `web_search` / `web_extract`
- 这些是 Hermes 内置工具，agent 在任何模式下均可直接调用
- 16 组搜索 + 10 页面提取，5 分钟内完成

## 推荐 Cron Job 配置

```yaml
# cron job 配置示例
schedule: "0 10,20 * * *"
prompt: |
  加载 find-bounty skill，执行巡检。
  直接用 web_search 工具跑 Tier 1 + Tier 2 + 厂商轮换搜索。
  读取 ~/.hermes/scripts/vendor_campaign_seen.jsonl 去重。
  输出活动卡片或 [SILENT]。
  新活动写入 seen 记录。
```

## 备选修复方向

如果需要脚本预处理（搜索量大、需要复杂过滤），有两种方案：

### 方案 A：替换 hermes_tools 为原始 HTTP 调用
```python
import os, requests
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
def web_search(query, limit=5):
    resp = requests.post("https://api.tavily.com/search", json={
        "api_key": TAVILY_API_KEY, "query": query, "max_results": limit
    })
    return resp.json()
```
- 优点：脚本可独立运行
- 缺点：需要 TAVILY_API_KEY 环境变量，且需 `pip install requests`

### 方案 B：用 Hermes CLI 子命令
```bash
hermes search "site:linux.do AI credits" --limit 5
```
- 待验证：hermes CLI 是否有搜索子命令
- 如果有，脚本可用 `subprocess.run` 调用

## 关键结论

**在 cron 模式下，agent 直接使用内置工具是最可靠的路径。** 脚本预处理增加了复杂度但不增加可靠性。除非搜索量大到必须预过滤（>50 组搜索），否则不需要脚本。
