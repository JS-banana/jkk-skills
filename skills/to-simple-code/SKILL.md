---
name: to-simple-code
description: >-
  Manual-only evidence-driven simplification of existing code or the current
  diff: find and collapse duplicated facts, lifecycle state, dead compatibility
  paths, speculative abstractions, and unused surfaces. Default is a read-only
  audit; apply one proven candidate only after explicit authorization. Use only
  when the user explicitly invokes $to-simple-code. Do not use for ordinary
  feature work, formatting, performance or security audits, or any request that
  did not name this skill.
license: MIT
disable-model-invocation: true
---

# To Simple Code

把代码变简单，不是追求更少的行，而是减少团队必须长期保持一致的事实、状态、契约、路径和概念。静态工具只能提出候选；当前消费者、所有权、历史、运行证据、兼容义务和可证伪验证共同决定能否收敛。

跟随用户的语言交付。没有安全可做的化简是有效结论，不要为了完成任务强行寻找可删项。

## 仅手动触发

仅当用户显式调用本 skill 时进入下方流程。点名方式：`$to-simple-code`、
`/to-simple-code`。用户只是提到简化、重构、清理、过度设计，或让你看看
当前 diff 是否太复杂，不得自行启动。

## 1. 确认模式与范围

根据完整用户意图选择模式，不按 `simplify`、`refactor`、`clean up` 等单个词推断写入授权：

- **AUDIT**：默认只读，发现并排序候选。
- **INVESTIGATE**：只读地深入一个候选，优先寻找不能改的证据。
- **APPLY**：只有用户明确要求实施具体候选或明确授权化简时才修改。

用户提到“本轮改动”“这个 diff”或当前功能时，默认只检查相关 diff、调用链和 ownership boundary。只有用户明确要求仓库级审计时才扩大到整个仓库。范围不清但可以从当前上下文安全推断时直接继续；不同范围会显著改变结论时再请用户决定。

先读目标仓库的 `AGENTS.md`、`CLAUDE.md`、贡献指南、架构/决策文档和验证指引。仓库规则、用户边界和当前事实优先于本 Skill。

完成标准：模式、目标仓库、path scope 和修改权限均已明确。

## 2. 建立证据基线

记录：

- branch、HEAD、相关 dirty/untracked 文件和本轮已有 diff；
- 生产入口、公开包、生成物、vendor、migration、fixture 和持久化边界；
- 目标行为、当前事实源与已知消费者；
- 仓库已有的窄验证、广验证和真实运行入口；
- 已存在失败，以及哪些检查本轮不会或不能运行。

AUDIT/INVESTIGATE 可做文本、Git 和元数据检查。会执行仓库代码、加载项目配置、生成文件、安装依赖或访问外部环境的命令不等于“纯查看”；只有在用户授权、仓库可信且对结论必要时运行，并报告可能产生的工作区副作用。

完成标准：后续结论可绑定到具体 HEAD、scope 和证据能力，不把未知范围写成仓库级完整结论。

## 3. 发现维护面候选

优先沿真实入口、当前 diff、调用链、状态所有者和持久化路径检查：

1. **重复事实**：多个字段、缓存、事件、快照或 adapter 表达同一真相并需要同步。
2. **生命周期重复**：flags、sentinel、promise、queue、controller 或 disposer 重复表达 ready、stopping、settled、flushed、disposed 等转换。
3. **无消费者表面**：API、export、event、config、hook、package 或 protocol field 没有当前生产消费者。
4. **推测性结构**：单实现 interface、未设置开关、未使用 fallback、无 owner 扩展点或转发层。
5. **废弃义务残留**：实现已退出，但兼容分支、schema、测试、文档、配置或生成清单仍在续命。
6. **错位实现**：同一 owner 内重复防御，或标准库、平台和既有依赖已可靠覆盖的自建基础设施。

编译器、linter、dead-code 工具、依赖分析和搜索结果都只是 leads。检查调用者和被调用者、动态入口、字符串分发、插件/DI/registry、序列化、环境变量、发布表面和仓库外消费者。

不要把合理独立性误判为重复。不同 owner、失败域、进程、事务、信任边界或可替换实现可能需要各自的状态与适配层。

## 4. 通过对抗审查决定状态

为每个具体候选形成初步删除/收敛假设后，冻结该结论并进入反方阶段：

> 假设候选是承重的，当前化简建议是错的；寻找能够推翻它的最强证据。

在给候选最终状态前，读取 [证据与对抗审查门](references/evidence-gates.md)。不得用初步结论、搜索数量、删除行数或绿测本身支持候选。

对抗审查至少检查消费者、动态/外部可达性、历史问题、当前 owner、运行证据、公开/持久化义务、失败边界和 decisive check。每项反对意见必须记录检查过的证据、结果、剩余未知和它如何改变候选状态。

如果用户明确允许多 Agent，且候选涉及公开 API、持久化、并发、异步生命周期、安全或跨进程边界，可让独立 reviewer 只读取候选范围和原始证据进行审查；不要告诉它期望结论。主 Agent 必须复核实际证据。没有独立 reviewer 时执行单 Agent 的独立反方 pass，并明确标记，不能声称完成了独立审查。

候选只能进入四种状态：

- **READY_TO_APPLY**：反对意见已被当前证据关闭，有明确净减少和决定性验证；仍需用户授权修改。
- **KEEP**：真实消费者无法由收敛后的唯一事实满足，或存在独立 owner、现行理由，或替换只会搬运复杂度。
- **PRODUCT_DECISION**：会移除用户能力、公开 API、持久化格式、兼容承诺或需要迁移策略。
- **UNVERIFIED**：动态、外部、历史、运行态或验证证据不足，不能安全推进。

只在 `READY_TO_APPLY` 内按证据强度、风险和净维护收益排序。不要把几个主观序数相乘成伪精确总分。

## 5. 交付审计结果

AUDIT/INVESTIGATE 按以下结构回答：

1. **Baseline**：repo、branch、HEAD、scope、dirty state、实际执行权限和已有失败。
2. **Coverage**：检查过的入口、动态/外部/持久化边界，以及未覆盖范围。
3. **READY_TO_APPLY**：最多列出 5 个最强候选，给位置、事实源/owner、消费者、反证、净减少和 decisive check。
4. **KEEP / PRODUCT_DECISION / UNVERIFIED**：只列高价值项及决定状态的证据或缺口。
5. **Decision**：明确 Go / No-Go、下一步和哪些检查本轮未运行。

不要把“没有发现”写成“仓库不存在”；不要把静态检查、自动测试、真实运行或他方报告混成同一种证据。

## 6. 实施一个获批候选

进入 APPLY 前：

1. 锁定用户批准的候选与范围；未指定时只选一个最高证据候选，不顺带处理其他项。
2. 重新检查 HEAD、相关代码和 dirty state。证据绑定的代码已变化时，先重做受影响证明。
3. 涉及 `PRODUCT_DECISION` 的候选必须先得到明确产品决定；涉及迁移时先有可执行迁移与回退边界。

实施时：

- 在一个 ownership boundary 内处理共享熵源，不给每个 caller 打补丁；
- 端到端移除旧契约：声明、实现、分支、导出、配置、专属测试、文档、快照、生成物和依赖；
- 保留幸存的可观察行为测试，不为了减少行数删除信任边界、授权、安全、无障碍、数据保护、持久化兼容或资源可靠停止与释放所需逻辑；
- 把镜像状态收敛到承重事实并由其派生，不增加同步 wrapper；
- 优先删除，其次使用标准库/平台，再考虑既有依赖；新增依赖必须真正减少自有实现、测试和供应链总负担；
- 不修改无关脏文件，不提交、push、发布或清理用户工作区，除非用户另有明确授权。

## 7. 验证并报告

每个非平凡批次：

1. 重新搜索被删符号、字符串、路径、配置和过期文档。
2. 先运行候选的 decisive check，再运行仓库相关的 type、lint、test、build、codegen 或 smoke gate。
3. 对公开、持久化、wire 或用户可见边界做对应的真实行为比较；自动检查不能替代目标环境验收。
4. 检查完整 diff、scope 和格式问题，确认没有新事实、兼容层或维护义务替代旧复杂度。

失败时判断是候选本来承重、实施不完整还是 baseline 已红。不要削弱有意义的检查来迫使删除通过；不要用宽范围 reset/checkout 覆盖用户改动。只精确修复或逆转本轮自己的 patch，无法安全收口时保留现场并报告。

最终区分：本轮实际运行、静态核对、他方 reported evidence 和未验证项。报告删除的事实/状态/契约与净维护收益，而不只报告 LOC。
