---
name: to-goal
description: 把一个 agent-ready ticket 编译成可粘贴到任意新会话执行的 goal 契约。在 /to-tickets 之后、开执行会话之前使用。
disable-model-invocation: true
license: MIT
---

# To Goal

把稳定的 ticket 和易变的仓库快照，在派发瞬间**编译**成一次性执行契约。产物两份：**契约**给执行者，**执行推荐**给编排者。

编译器语义约束全程：只读无副作用——不改文件、不动 ticket、不建分支；不发明输入里没有的东西；拒绝不合法输入。

**何时不用**：ticket 琐碎或你已在执行会话中——直接实现更便宜；要传递的是对话上下文——用 /handoff；需求还没落 ticket——先 /to-tickets。调用时口头追加的需求同理：先落 ticket 再编译。

## 1. 选定 ticket

有参数：按本地路径或 GitHub issue 号/URL 读 ticket 全文，含 comments。

无参数：选当前 frontier——

1. tracker 路由：读 `docs/agents/issue-tracker.md`；缺失时探索降级（存在 `.scratch/*/issues/` → 本地文件 tracker；GitHub remote → `gh` 查 `ready-for-agent` 标签）；都没有 → 请用户指明 ticket。
2. frontier ＝ Status 为 ready-for-agent（或仓库对应标签）、Blocked by 全部完成、编号最小。blocker 完成与否信其文件/issue 自身状态；含糊时报告而非猜测。
3. 多个 frontier（多 feature 并行）→ 列出请用户选。被阻塞 → 报告 blocker 并停止。

**质检门**：ticket 缺可执行的验收标准、或大到一个新会话装不下 → 拒绝编译，路由回 /to-tickets（补标准或再切）或 /grill-me。

完成标准：锁定唯一一个 agent-ready ticket，或已停止并说明原因。

## 2. 取证（只读）

1. 读 ticket 全文与所属 spec（若有）。
2. 记录分支、HEAD、工作区状态、近期相关提交。
3. **证据三态**：逐条验收标准对照仓库现状，归类为「有证据完成 / 明确未完成 / 未验证」。commit message 不算证据；测试通过、行为可复现才算。全新 ticket 即「全部未验证」的退化情形。
4. 记录 baseline 已有失败——执行者需要知道哪些红不是它弄红的。
5. 从仓库自身发现验证命令（package.json scripts / Makefile / CI 配置 / 既有测试），逐条带出处；发现不了就写「未发现，请执行者确认」。

三态只对选中的 ticket 做；上游票信其状态即可。

完成标准：每条验收标准有三态归类，每条验证命令有出处或标注缺失。

## 3. 编译

**契约**，按下方模板产出：

- 产品性验收标准**逐字继承**——改写等于改产品决策。
- 工程 gate（全量测试、类型检查、diff 纯净、绿后提交）可追加，每条必须带仓库出处。
- 契约精瘦：仓库规则以指针指向 AGENTS.md / CLAUDE.md；goal 只带 ticket 特有排除项与下游 ticket 点名。
- 正文语言跟随 ticket。

<goal-template>

> 这是预编译的执行契约 — compiled at <ISO 时间> against <HEAD 短哈希>，source: <ticket 路径/URL>。
> 按契约执行：不重新访谈需求；逐条自查 Completion criteria；任何一条被证明错误或不可能时，停下报告，不要自行改释。

## Goal

<一句话：本 ticket 范围内的端到端结果>

## Current state

- 分支 <branch>，HEAD <短哈希>；相关脏文件：<列出，或「无」>
- 验收标准现状：已验证完成 <条目＋证据> ／ 明确未完成 <条目> ／ 未验证 <条目>
- baseline 已有失败：<列出，或「无」>

## Completion criteria

- [ ] <ticket 验收标准，逐字继承>
- [ ] <工程 gate，带出处：如 `npm test` 全过 — 出处 package.json scripts.test>
- [ ] diff 只含本 ticket 相关改动；全部标准通过、工作区干净后提交

## Constraints

- 不 push、不开 PR、不动 parent issue
- 不改与本 ticket 无关的脏文件/未跟踪文件
- 不提前实现下游 ticket：<编号/标题，或「无下游」>
- 环境里有 /tdd、/code-review 之类流程技能就用；没有则以 Completion criteria 自查
- 仓库规则读 AGENTS.md / CLAUDE.md

## Context

- 源 ticket：<路径/URL>；spec：<路径，或「无」>
- 首读文件：<取证中确认的相关文件>
- 验证命令：<命令＋出处，或「未发现，请自行确认」>

</goal-template>

**执行推荐**，独立于契约——契约对派发保持中立，路由权在编排者：

- 能力档：**轻量**（机械修改、照既有模式、失败成本低）／**标准**（常规特性与修复，默认）／**高阶**（跨模块设计、安全边界、schema 迁移、并发、根因难题）。
- 推理强度：**低**（确定性工作、验证便宜）／**中**（默认）／**高**（歧义行为、交互不变量、昂贵失败）。
- 推荐能可靠完成的**最低**档位，附一句取证得来的理由；不点名具体模型——两轴映射到哪个 agent、哪个模型由编排者定。

完成标准：契约五节齐备，每条 Completion criterion 独立可检且可溯源（ticket 逐字，或带仓库出处）；推荐两轴齐备且有证据理由。

## 4. 交付

1. 对话中完整打印契约。
2. 写入 `/tmp/goals/<repo>-<NN>-<slug>.md`。
3. readiness note：编译自哪个 ticket、三态摘要、执行推荐、建议开新会话粘贴执行——本会话到此为止，不继续实现。

完成标准：文件路径已给出，契约整段可直接粘贴。
