# 证据与对抗审查门

本文件用于给候选分配最终状态。先完成初步候选调查，再读取本文件；不要把它当全仓机械 checklist。

## 候选证据记录

每个候选使用以下最小记录：

```text
[id / proposed status / risk] exact location and candidate
scope: bound repo, HEAD, paths, entrypoints
current truth/owner: load-bearing representation and lifecycle owner
consumers: production / non-production / ambiguous / external
objections: strongest reasons the candidate may be load-bearing
evidence checked: code / dynamic / history / runtime / decisions
cut: declarations, behavior, tests, docs, config, dependencies, concepts
tradeoff: observable capability or compatibility lost
decisive check: smallest check expected to fail if the change is wrong
net reduction: truths, states, contracts, paths and owned machinery removed
unknowns: inaccessible or unverified evidence
```

缺少精确位置、scope、反对意见或 unknowns 的记录不能进入 `READY_TO_APPLY`。

## Gate A：消费者与可达性

搜索并检查：

- symbol、file path、package name、config key、event/wire string 和替代调用写法；
- production source、真实入口、运维脚本、shipped config、migration 和生成入口；
- test、doc、comment、snapshot 等非生产消费者是否只在给实现续命，还是在定义公开行为；
- plugin manifest、registry、DI token、reflection、lazy import、route、codegen、serializer、environment lookup；
- 发布包、SDK、CLI、HTTP API、插件生态、配置模板和仓库外消费者。

存在真实消费者不必自动 `KEEP`：继续判断能否让消费者直接依赖唯一事实。但只要外部或动态可达性无法排除，就不能以“仓内引用为零”进入 `READY_TO_APPLY`。

## Gate B：能力、兼容与保护边界

以下变化默认进入 `PRODUCT_DECISION` 或 `UNVERIFIED`，不能伪装成内部清理：

- 移除可达的用户能力、公开 API、CLI 参数、事件、配置或插件入口；
- 改变持久化格式、schema、migration、wire protocol、缓存兼容或回放能力；
- 弱化授权、安全、信任边界验证、无障碍、数据丢失防护或资源 quiescence；
- 替换独立 owner、进程、事务、失败域或后端之间有意存在的表示。

“尚未发现消费者”不是“没有兼容义务”。检查发布状态、版本策略、弃用承诺、调用日志和维护者决策。

## Gate C：历史与当前理由

回答：

1. 什么问题引入了这项维护面？
2. 原问题现在是否仍存在？
3. 哪项当前证据足以推翻原理由？

使用相关 commit、blame、PR/issue、ADR/RFC 和当前代码，但校准这些失真：shallow history、squash、rename、旧路径、迁仓、bot、弱 commit message 和过期决策文档。历史提供 rationale，不证明当前正确性；最终仍回到代码、运行行为和现行产品义务。

## Gate D：运行证据

当候选可能有仓库外使用或环境依赖时，优先检查用户已放入范围的 telemetry、日志、trace、analytics、feature-flag 统计、API access log、真实配置和目标环境。

- 运行证据证明观察窗口内发生或未发生什么，不证明窗口外永远没有消费者。
- 记录环境、版本、时间窗口、采样和缺失数据。
- 没有权限访问生产数据时标记 `UNVERIFIED`；不要自行扩权、上传日志或请求敏感数据。
- 测试、demo 和 mock 不能替代真实第三方、浏览器、设备、进程或持久化链路。

## Gate E：所有权与防御逻辑

对 mirrored fact 或 lifecycle candidate，画出：

```text
owner → authoritative state → transitions → observers → terminal outcome
```

只有同一 owner、同一失败域且能由一个承重事实可靠派生时才收敛。不同 owner 的独立确认、跨进程状态、事务提交状态或恢复标记不应仅因取值相似而合并。

删除 copy、freeze、validator、rollback 或 hostile-input test 前，证明：

- 输入已在真正边界验证；
- 下游无法通过 alias 或可变引用破坏上游所有权；
- 没有第三方、插件、反序列化、worker、process 或 wire 输入；
- 防御逻辑不承担并发、回退、审计或数据保护职责。

类型声明本身不证明运行时所有权和不可变性。

## Gate F：净维护收益

估算删除的：

- 独立事实、状态、契约、入口和配置维度；
- 专属实现、测试、文档、快照、生成物和依赖；
- 团队必须理解和保持同步的概念。

扣除新增的 adapter、wrapper、migration、依赖、配置和测试负担。如果只是把逻辑搬到新层、把两个事实包进同步器或引入等量 glue，状态为 `KEEP`。

LOC 只能作为结果旁证，不能覆盖行为、兼容或所有权风险。

## Gate G：决定性验证

写出一个最小可证伪问题：

> 如果化简判断是错的，哪个最小检查最可能暴露它？

例如：旧 serializer 的决定性检查是读取真实历史文件；动态 route 的检查是从真实入口分发；生命周期状态的检查是覆盖取消、失败和 terminal cleanup。全量测试可以是后续 Gate，但不能代替候选特有的 falsification check。

无法命名决定性检查，或检查所需环境当前不可用时，候选不能进入 `READY_TO_APPLY`。

## 对抗审查协议

初步候选形成后，审查者以“该候选承重、化简会失败”为工作假设：

1. 不复述支持删除的理由，先提出最强、具体、可证伪的反对意见。
2. 为每项反对意见记录：`objection / evidence checked / result / remaining uncertainty / status effect`。
3. 优先攻击最昂贵的失败：外部消费者、数据不可逆、权限绕过、异步竞态、资源泄漏和不可回放。
4. 检查候选证据是否循环引用、共享同一来源、把静态类型当运行事实，或把测试覆盖当不存在外部消费者。
5. 只有反对意见被当前直接证据关闭，才允许 `READY_TO_APPLY`；无法关闭不是低分，而是 `UNVERIFIED`。

使用独立 reviewer 时：

- 只提供 scope、候选和原始材料，不提供期望结论或实现方案；
- reviewer 保持只读，返回可审计证据和未知项；
- 主 Agent 重新打开关键代码/证据并独立裁决；
- reviewer 同意不等于通过，多个 reviewer 复述同一来源不算交叉验证。

没有独立 reviewer 时写明“单 Agent 反方审查”；不要称为独立审查。

## 状态裁决

| 状态 | 必要条件 | 下一步 |
| --- | --- | --- |
| `READY_TO_APPLY` | 关键 Gate 已关闭，净收益为正，有 decisive check | 请求或确认具体实施授权 |
| `KEEP` | 有当前承载理由，或替换不会减少维护义务 | 说明保留理由，停止该候选 |
| `PRODUCT_DECISION` | 改变能力、公开/持久化契约或需要迁移 | 呈现取舍，等待产品决定 |
| `UNVERIFIED` | 关键可达性、运行态、历史或验证证据缺失 | 写出精确缺口和下一验证动作 |

状态不是置信度形容词。新 commit、相关 dirty change、版本或环境变化影响证据时，重新打开对应 Gate。

