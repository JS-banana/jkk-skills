<div align="center">
  <h1>🍌 banana-skills</h1>
  <p><b>小帅的 AI 资产库：skills 插件 + prompts 沉淀</b></p>
</div>

## 🗂️ 仓库结构

| 目录 | 内容 |
|------|------|
| `plugins/banana/` | 可安装的 Claude Code 插件（技能见下方列表） |
| `prompts/` | 收藏的提示词与 AI 使用沉淀（[索引](prompts/README.md)） |
| `docs/` | 技能的 specs / ADR / 研究资料 |

## 📦 安装

```bash
# 安装全部技能
npx skills add JS-banana/banana-skills

# 或按需安装单个技能
npx skills add JS-banana/banana-skills --skill demand-radar
```

<details>
<summary>Claude Code 插件方式安装</summary>

```bash
/plugin marketplace add JS-banana/banana-skills
/plugin install banana
```

</details>

安装后无需配置，在 Claude Code 对话中直接描述任务即可自动触发，
如「帮我写 README」「优化 AGENTS.md」「跑一次需求雷达」。

---

## ✨ 技能列表

| 技能 | 功能 |
|------|------|
| [ai-vendor-campaign-radar](plugins/banana/skills/ai-vendor-campaign-radar/) | 发现、筛选、提醒并记录 AI/编程活动机会 |
| [demand-radar](plugins/banana/skills/demand-radar/) | 采集、筛选、验证真实用户需求信号，并准备飞书多维表格记录 |
| [dream](plugins/banana/skills/dream/) | 记忆巩固：扫描各项目会话记录与 memory，报告先行地沉淀、合并、清理长期记忆 |
| [give-name](plugins/banana/skills/give-name/) | 为公司、品牌、项目、仓库、网站、社区等创作、比较并验证有品味的名称 |
| [handdrawn-illustrator](plugins/banana/skills/handdrawn-illustrator/) | 将文章或概念设计成构图统一、角色一致的铅笔编辑插图、手写批注图与简单解释图 |
| [r2-asset-publisher](plugins/banana/skills/r2-asset-publisher/) | 压缩图片、发布到 Cloudflare R2，并维护 Markdown 图床 URL 与资产台账 |
| [to-goal](plugins/banana/skills/to-goal/) | 把 agent-ready ticket 编译成可粘贴执行的 goal 契约：快照绑定、证据三态、机器可验证完成标准 |
| [writer-readme-md](plugins/banana/skills/writer-readme-md/) | 基于项目证据生成/审查 README，含排版、徽章与双语规范 |
| [writer-context-md](plugins/banana/skills/writer-context-md/) | 创建和审查 AGENTS.md/CLAUDE.md 等 agent 上下文文件 |
