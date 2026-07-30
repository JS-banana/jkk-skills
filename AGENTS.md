# AGENTS.md

个人 AI 资产库：`plugins/banana/`（可安装的 Claude Code 插件）+ `prompts/`（提示词沉淀）
+ `docs/`（specs / ADR / 调研）。纯 Markdown/JSON/Python 脚本仓库，无构建系统、无测试套件。

## 命名

- 插件名 `banana`、marketplace 名 `banana-skills`、仓库 `JS-banana/banana-skills`。
  2026-07 前曾用名 `jkk` / `jjk-skills`，勿再引入旧拼写。

## 结构约定

- 新 skill 放 `plugins/banana/skills/<name>/`。`plugin.json` 靠 `skills/` 目录自动发现，
  不要往里加 `skills` 字段。
- skill 内部不得引用 `plugins/banana/` 之外的路径：插件安装时只拷贝插件目录，
  跨界引用在用户机器上必然失效。
- `docs/<skill>/` 是该 skill 的开发工作区（需求 / 设计 / ADR），`docs/research/` 放调研素材。
  仓库根目录不放散落脚本或运行数据。
- 新增或改名 skill 后，同步更新 README 的技能列表；新增 prompt 后，
  同步更新 `prompts/README.md` 的索引。

## 事实源（易踩坑）

- **find-gap 的 schema 权威源是用户的活飞书 Base**（`lark-cli base +field-list` 查询），
  skill 内 `scripts/run.py` + `references/feishu-schema.md` 应镜像活库。
  `docs/find-gap/design.md` 已废弃且枚举值有错——任何 schema 改动前先查活库，别信它。
- skill 的运行知识以 `SKILL.md` 和其直接引用的 `references/` 为准；
  开发期需求、设计和调研留在 `docs/`，不得作为安装后的运行时依赖。
- skill 的规范类内容（写作规则、最佳实践）需有实证来源，调研素材存 `docs/research/`；
  但 skill 文件内不得引用该目录（见上方跨界引用规则）。
- 雷达类 skill 写入飞书只走既定通道（Hermes 机器人或 lark-cli），不要新写保存逻辑。

## 边界

### Ask First

- 修改 `marketplace.json` / `plugin.json` 中的名称类字段（影响分发身份和已安装用户）。
- 改动飞书 Base 已有字段结构。

### Never

- 把飞书 token / base-token 硬编码进 skill（依赖 lark-cli 登录态）。
- 提交运行产物（`demand_radar_data/`、`__pycache__/` 已 gitignore，数据写 /tmp）。

## 验证

- 改过 manifest 后校验 JSON：
  `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/banana/.claude-plugin/plugin.json'))"`
- 改过 write-readme skill 后：
  `python3 plugins/banana/skills/write-readme/scripts/validate.py --skill plugins/banana/skills/write-readme`
- 提交信息用 gitmoji + Conventional Commits（中文描述），一次提交只含一件事。
