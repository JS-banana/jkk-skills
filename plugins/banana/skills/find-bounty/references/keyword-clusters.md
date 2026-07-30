# AI 活动雷达 — 关键词簇参考

> 按场景分组的搜索关键词，用于构造 `web_search` 查询。
> 不要一次全用，按扫描策略轮换组合。

---

## 一、活动类型词（核心）

### 英文
```
"AI hackathon"
"agent hackathon"
"developer challenge"
"AI developer competition"
"build with AI"
"coding challenge"
"innovation challenge"
"startup competition"
"AI app challenge"
"generative AI challenge"
"MCP hackathon"
"RAG challenge"
"AI agents challenge"
```

### 中文
```
"AI 大赛"
"AI 创造力大赛"
"AI 开发者大赛"
"智能体开发者激励"
"开发者激励计划"
"编程马拉松"
"黑客松"
"Hackathon"
"挑战赛"
"创新赛"
"应用创新大赛"
"Agent 大赛"
"智能体大赛"
"开发者挑战赛"
```

---

## 二、奖励/激励信号词

### 英文
```
"cash prize"
"API credits"
"submissions open"
"registration open"
"application deadline"
"$50K" OR "$100K" OR "$1M"  （金额梯度）
"prize pool"
"free credits"
"beta program"
"developer program"
"early access"
```

### 中文
```
"算力券"
"API credits"
"奖金"
"报名开启"
"征集令"
"作品提交"
"初赛报名"
"开发者扶持计划"
"免费额度"
"赠金"
"内测招募"
"体验官"
```

---

## 三、技术方向词（提升相关性）

```
"AI Agent"
"智能体"
"MCP"
"RAG"
"AI 编程"
"Vibe Coding"
"多智能体"
"multi-agent"
"Gemini"
"Claude"
"GPT"
"鸿蒙智能体"
"Trae"
"Cursor"
"Windsurf"
"cloud-native AI"
"端侧 AI"
"具身智能"
"AI safety"
"AI CTF"
```

---

## 四、组合搜索表达式（直接可用）

### 广撒网（每日轮换使用 1-2 个）

```bash
# 英文通用发现（最高 ROI 单条查询）
"AI hackathon" OR "agent hackathon" OR "developer challenge" prize deadline 2026

# 中文通用发现
"AI 大赛" OR "智能体大赛" OR "编程马拉松" OR "开发者挑战赛" 报名 2026

# Agent 专项
"AI agent" OR "agentic AI" hackathon OR challenge submissions open 2026
```

### 平台限定搜索

```bash
# Devpost
site:devpost.com AI agent hackathon 2026

# LabLab
site:lablab.ai AI hackathon 2026

# 天池
site:tianchi.aliyun.com AI 大赛 2026

# 掘金（AI赛事通聚合帖）
site:juejin.cn "AI赛事通" OR "AI 大赛" OR hackathon 2026

# 华为
site:developer.huawei.com 鸿蒙 智能体 激励 OR 大赛

# Slack
site:slack.dev challenge OR "agent builder"
```

### 厂商定向搜索

```bash
# Google / Gemini
site:developers.google.com events Gemini hackathon 2026

# Anthropic
site:anthropic.com hackathon OR competition OR "developer program" 2026

# 字节/Trae
"Trae" OR "豆包" AI 大赛 OR 创造力大赛 OR hackathon 2026

# 华为
华为 天工计划 OR 鸿蒙智能体 OR 开发者大赛 2026

# 通义/Qwen
"Qwen" OR "通义" hackathon OR 大赛 OR developer challenge 2026
```

---

## 五、使用建议

1. **每日巡检**用 1 个广撒网 + 2-3 个平台限定，总搜索量控制在 6-8 组
2. **每周深扫**补上厂商定向搜索，每次覆盖 2-3 个厂商
3. **中英文各搜一轮**覆盖面更广，很多中文活动不出现在英文搜索中
4. **`2026` 后缀**帮助过滤过期结果，每年年初需更新为当前年份
5. **不要同时用太多关键词**，单次搜索 3-5 个关键词组合效果最好
6. 发现新活动后，**反推其关键词**，如果当前簇未覆盖则补充
