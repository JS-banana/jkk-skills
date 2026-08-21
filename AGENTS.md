# AGENTS.md

个人 Agent Skills 库：`skills/`（Agent Skills，跨 agent 通用）
+ `docs/`（specs / ADR / 调研，**已 gitignore，仅本地**）。
纯 Markdown/JSON/Python 脚本仓库，无构建系统、无测试套件。

## 命名

- 仓库 `JS-banana/jkk-skills`。曾用名 `banana-skills`，安装命令与文档一律用 `jkk-skills`，勿再引入旧拼写。

## 结构约定

- 新 skill 放 `skills/<name>/`，含 `SKILL.md`（frontmatter 必须有 `name` +
  `description`，本仓统一带 `license: MIT`）。`skills/` 是 `npx skills add` 的
  标准发现路径，不要再引入 `plugins/` 之类的中间层。
- **skill 目录必须自包含**：内部只用相对本 skill 根的路径（`scripts/x.py`、
  `references/y.md`）。安装时只拷贝单个 skill 目录，任何跨目录引用在用户机器上必然失效。
- `docs/<skill>/` 是该 skill 的开发工作区（需求 / 设计 / ADR），`docs/research/` 放调研素材。
  仓库根目录不放散落脚本或运行数据。
- 新增或改名 skill 后，同步更新 README 的技能列表。
- 仅 Claude Code 支持的 frontmatter 字段（如 `disable-model-invocation`）在其他
  agent 上会被忽略，别把「只能手动触发」当作跨 agent 的硬保证。

## 事实源（易踩坑）

- **find-gap 的 schema 权威源是用户的活飞书 Base**（`lark-cli base +field-list` 查询），
  skill 内 `scripts/run.py` + `references/feishu-schema.md` 应镜像活库。
  `docs/find-gap/design.md` 已废弃且枚举值有错——任何 schema 改动前先查活库，别信它。
- skill 的运行知识以 `SKILL.md` 和其直接引用的 `references/` 为准；
  开发期需求、设计和调研留在 `docs/`，不得作为安装后的运行时依赖。
- skill 的规范类内容（写作规则、最佳实践）需有实证来源，调研素材存 `docs/research/`；
  但 skill 文件内不得引用该目录（见上方自包含规则）。
- 雷达类 skill 写入飞书只走既定通道（Hermes 机器人或 lark-cli），不要新写保存逻辑。

## 边界

### Ask First

- 改动 `skills/` 顶层布局或 skill 目录名（影响已安装用户和安装命令）。
- 重新引入 Claude Code 插件形态（`.claude-plugin/`）——2026-08 已明确只保留 skills 形态。
- 改动飞书 Base 已有字段结构。

### Never

- 把飞书 token / base-token 硬编码进 skill（依赖 lark-cli 登录态）。
- 提交运行产物（`demand_radar_data/`、`__pycache__/` 已 gitignore，数据写 /tmp）。

## 验证

- 改过 skill 目录结构或 frontmatter 后，确认 14 个 skill 都能被发现：
  `npx -y skills@latest add . --list`（须列出全部，无重复、无遗漏）
- 改过 write-readme skill 后：
  `python3 skills/write-readme/scripts/validate.py --skill skills/write-readme`
- 提交信息用 gitmoji + Conventional Commits（中文描述），一次提交只含一件事。
