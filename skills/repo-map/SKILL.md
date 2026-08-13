---
name: repo-map
description: 用 Git 历史为陌生代码库建立证据地图与优先阅读路线。当用户接手、总览或评估新仓库，询问活跃区域、反复修复点、贡献者、维护节奏或应该先读哪些文件时使用。
license: MIT
---

# Repo Map

把提交历史当作考古层：先收集可复核的演化证据，再进入当前代码。历史用于缩小阅读范围；结论仍由代码、文档和运行链路验证。

## 1. 锁定证据边界

确认目标仓库与用户关心的子目录。默认分析当前 `HEAD` 可达历史和最近一年；用户指定时间或目录时，以用户范围为准。

完成标准：目标仓库、当前 HEAD、时间窗口和 path scope 均已明确。

## 2. 采集历史

把当前 `SKILL.md` 所在目录记为 `<skill-dir>`，运行其中的脚本：

```bash
python3 <skill-dir>/scripts/inspect.py --repo <repo-path>
```

常用收窄方式：

```bash
python3 <skill-dir>/scripts/inspect.py --repo <repo-path> --since "6 months ago" --path src --path app
```

脚本只读目标仓库，输出 JSON。保留输出中的 `repository`、`scope`、`warnings` 与各项原始计数；复现命令使用脚本的实际绝对路径。

完成标准：脚本成功输出 JSON，其中的 `repository.head` 与目标 HEAD 一致，实际绝对路径命令已记录。

## 3. 校准信号

逐条处理 `warnings`。浅克隆意味着结论只覆盖现有历史；噪声候选意味着 lockfile、生成物或 vendored 路径可能主导结果；历史旧路径已排除时，在报告中说明其触碰次数。必要时用 `--path` 显式重跑并保留原始结果。

把统计视为线索：

- `change_hotspots` 表示提交触碰频率；代码质量和按行 churn 需要独立证据。
- `contributors` 表示提交归属；实际所有权和 bus factor 需要独立证据。
- `fix_signal` 与 `crisis_signal` 只匹配 commit subject，受提交规范和语言影响。
- `activity_by_month` 描述提交节奏；团队健康、人员变化和发布质量需要独立证据。

完成标准：每个非空 warning 都已进入报告，所有推断均与原始计数分开。

## 4. 回到当前代码

优先检查 `fix_signal.overlap_with_change_hotspots`，再看其余 change hotspots 与 directory hotspots。对候选路径读取当前文件、相邻模块、仓库规则和相关提交；确认路径仍存在且承担什么职责。贡献者数据用于定位可追溯的历史；个人评价需要另行授权和证据。

完成标准：每个推荐阅读项都对应当前存在的代码或文档，并写明历史证据和要验证的问题。

## 5. 交付阅读地图

按以下结构回答：

1. **Baseline**：仓库、branch、HEAD、scope、时间窗口、是否 shallow。
2. **Facts**：热点文件/目录、贡献者分布、fix overlap、活动节奏、危机关键词提交。
3. **Hypotheses**：需要靠当前代码或团队背景验证的解释。
4. **Reading route**：按顺序列出文件或目录、入选证据、阅读时要回答的问题。
5. **Blind spots**：提交规范、squash、重命名、生成文件、浅历史等限制。

完成标准：事实均可回溯到脚本字段；假设均带验证动作；统计相关性保持为假设，因果结论均有独立证据。
