<div align="center">
  <img src="assets/logo.svg" width="120" alt="jkk-skills logo">
  <h1>jkk-skills</h1>
  <p><b>小帅的 Agent Skills 技能库</b></p>
</div>

## 📦 安装

```bash
# 交互选择要装的技能（CLI 会自动识别你装了哪些 agent）
npx skills add JS-banana/jkk-skills

# 装单个技能，并全局可用
npx skills add JS-banana/jkk-skills --skill deep-learn -g

# 只想看有哪些技能，不安装
npx skills add JS-banana/jkk-skills --list
```

技能遵循 [Agent Skills 规范](https://agentskills.io)，Claude Code、Cursor、Codex、
Copilot 等均可使用。

指定目标 agent 用 `-a`，例如 `-a claude-code -a cursor`；

安装后无需配置，在对话中直接描述任务即可自动触发，
如「帮我写 README」「优化 AGENTS.md」。

---

## ✨ 技能列表

| 技能 | 触发 | 功能 |
|------|------|------|
| [deep-learn](skills/deep-learn/) | 仅用户 | 深度研究：多路线独立探索、一手证据与对抗验证，产出可迁移的知识模型 |
| [deep-analysis](skills/deep-analysis/) | 用户 + 模型 | 有边界的证据分析：默认检索、可选横纵镜头，并给出带限制的暂定判断 |
| [deep-memory](skills/deep-memory/) | 仅用户 | 记忆巩固：扫描各项目会话记录与 memory，报告先行地沉淀、合并、清理长期记忆 |
| [find-bounty](skills/find-bounty/) | 仅用户 | 发现、筛选、提醒并记录 AI/编程活动机会 |
| [find-gap](skills/find-gap/) | 仅用户 | 采集、筛选、验证真实用户需求信号，并准备飞书多维表格记录 |
| [give-name](skills/give-name/) | 用户 + 模型 | 为公司、品牌、项目、仓库、网站、社区等创作、比较并验证有品味的名称 |
| [to-html](skills/to-html/) | 用户 + 模型 | 将 Markdown 研究、技术报告和实施指南编排为友好、可离线分享的 HTML 阅读预览页 |
| [to-illustration](skills/to-illustration/) | 用户 + 模型 | 将文章或概念设计成构图统一、角色一致的铅笔编辑插图、手写批注图与简单解释图 |
| [to-r2-image](skills/to-r2-image/) | 用户 + 模型 | 压缩图片、发布到 Cloudflare R2，并维护 Markdown 图床 URL 与资产台账 |
| [to-simple-code](skills/to-simple-code/) | 仅用户 | 证据驱动化简：以对抗审查收敛重复事实、状态、契约和过度设计 |
| [write-agent-context](skills/write-agent-context/) | 用户 + 模型 | 创建和审查 AGENTS.md/CLAUDE.md 等 agent 上下文文件 |
| [write-readme](skills/write-readme/) | 用户 + 模型 | 基于项目证据生成/审查 README，含排版、徽章与双语规范 |