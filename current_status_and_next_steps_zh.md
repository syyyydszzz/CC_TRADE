# 当前状态与下一步

> 校正版，基于 2026-04-12 的仓库现状、Claude Code 项目配置、以及本机 `qc-mcp` 执行记录，并已反映本次结果层契约改造后的规范层状态。

## 已确认成立

### 1. 仓库级架构边界已经明确

- `algorithms/`：本地策略源码与本地结果工作区主位
- `qc-mcp`：唯一执行层，负责 compile / backtest / optimization / live
- `Achieve`：goal loop 与 stop-hook 驱动的 runtime workflow 层
- `BuildForce`：research / spec / plan artifact 层

仓库正式契约已经明确不再走：

- `lp`
- 本地 Lean fallback
- `QuantBook`
- 本地数据下载执行路线

### 2. Achieve 和 BuildForce 的接入方式已经搞清楚

#### Achieve

- 通过 Claude Code plugin 接入
- 插件 marketplace 已 vendored 到仓库内的 `claude-achieve-plugin-main/`
- 项目通过 [`.claude/settings.json`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/settings.json) 启用插件
- 通过 [`.claude/scripts/auto-install-plugins.sh`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/scripts/auto-install-plugins.sh) 在 SessionStart 时从本地 marketplace 自动安装
- 通过 `/achieve:*` 命令调用
- runtime state 仍由 `.claude/achieve-sessions/**` 承载

当前仓库快照中仍未保留 Achieve session 文件，所以更准确的说法是：

- Achieve runtime state 机制已经明确
- Achieve 已补上对 `results/` 工作区契约的读取和写回约束
- 但当前仓库里没有活动中的 runtime state 快照

#### BuildForce

- 通过 [`.claude/commands/buildforce.*.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.plan.md) 这类命令驱动
- 通过 [`.buildforce/buildforce.json`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/buildforce.json) 管理当前 session
- 通过 `.buildforce/sessions/<session>/` 下的 `research.yaml / spec.yaml / plan.yaml` 保存 artifact

当前 BuildForce 的真实状态是：

- 历史 session artifact 已存在
- `currentSession` 当前是 `null`
- 说明 artifact 体系已落地，但没有激活中的 BuildForce session

### 3. `qc-mcp` 已经真实打通

截至 2026-04-12，已经确认以下事实：

- 用户级 [`.claude.json`](/Users/suyongyuan/.claude.json) 已配置 `qc-mcp`
- `read_open_project` 成功
- 当前 open project 确认为 `sample_sma_crossover`
- `create_compile` 成功
- `create_backtest` 成功
- `read_backtest` 成功

这说明当前已经具备：

- 本地写策略
- QuantConnect 执行
- Claude Code 回读结果

这条基础闭环能力。

### 4. 结果层契约已经从单文件升级为 `results/` 工作区

当前仓库已不再把 `results.md` 作为结果主文件，而是把结果层正式定义为：

```text
algorithms/{strategy}/
  main.py
  spec.md
  results/
    state.yaml
    report.md
    artifacts/
      runs/{run_id}/...
```

这套契约当前已经被固化到规范层：

- 仓库主文档与 guideline
- `strategy-writer` skill
- `.buildforce/templates/result-*.{yaml,md}`
- `.buildforce/context/result-workspace-contract.yaml`
- `buildforce.plan / buildforce.build` 的执行说明

各层职责已经明确：

- `results/state.yaml`：唯一 authoritative result state
- `results/report.md`：给人和 LLM 共读的当前结果报告
- `results/artifacts/runs/{run_id}/...`：原始结果归档与长分析

这意味着结果层现在已经与：

- Achieve runtime state
- BuildForce artifact state

做了更清晰的边界拆分。

### 5. `strategy-writer` 已经写入新结果工作区协议

[`.claude/skills/strategy-writer/SKILL.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/skills/strategy-writer/SKILL.md) 当前已经按新契约要求：

- 保持 `main.py`、`spec.md`、`results/` 工作区同步
- 先 `read_open_project`
- 再 `create_compile` / `read_compile`
- 再 `create_backtest` / `read_backtest`
- 必要时再做 optimization
- 先写 `results/artifacts/runs/{run_id}/`
- 再更新 `results/state.yaml`
- 最后刷新 `results/report.md`

所以结果写回协议已经从“写单个 `results.md`”切换为“写 `results/` 工作区”。

## 当前状态分层

项目里现在可以清楚地区分三类状态：

### 1. runtime state

由 Achieve 管理，理论落点为：

- `.claude/achieve-sessions/**`

用于表示：

- 当前 phase
- 当前 iteration
- success criteria
- achieved / continue 判定

当前情况：

- 机制已明确
- 当前仓库快照中未见已落地的 runtime state 文件

### 2. artifact state

由 BuildForce 管理，主要在：

- `.buildforce/buildforce.json`
- `.buildforce/sessions/**`

用于表示：

- 当前 session
- research / spec / plan
- workflow 进度

当前情况：

- artifact 已落地
- 但 `currentSession` 当前为 `null`

### 3. result state

由本地策略目录内的 `results/` 工作区管理，主要在：

- `results/state.yaml`
- `results/report.md`
- `results/artifacts/runs/**`

用于表示：

- 最新 compile / backtest / optimization / validation 状态
- 当前策略判断
- 下一步动作
- 原始执行结果与分析归档

当前情况：

- result contract 已正式落到规范层
- 结果层已经补上初始化和自检工具

## 当前已经补上的缺口

### 1. 结果读取顺序已经固定下来

当前仓库的结果读取顺序已经明确为：

1. 读本地 `spec.md`
2. 读 `results/state.yaml`
3. 读 `results/report.md`
4. 如需细看最新结果，读 `results/artifacts/runs/{latest_run_id}/run.yaml`
5. 只有在排错或深分析时，再读原始 `*.json`
6. 如果存在 Achieve session，再补读 runtime state
7. 如果存在 BuildForce session，再补读对应 artifact

这条顺序现在已经写入仓库契约和 skill，而不是只停留在讨论层。

## 当前仍然存在的遗留问题

### 1. 历史 BuildForce artifact 里仍有旧执行链痕迹

虽然仓库正式契约已经切到 `qc-mcp + results/`，但历史 BuildForce artifact 里仍然保留旧路线痕迹。

例如某个历史 `plan.yaml` 里仍然出现：

- `lp backtest algorithms/sr_levels`

这说明：

- 新架构契约已经稳定
- 但历史 artifact 还没有完全清理

### 2. 新结果工作区已经补上基础工具化

当前结果契约除了规范层之外，已经补上两类仓库内工具：

- `init-result-workspace.sh`：初始化 `results/` 工作区
- `check-result-workspace.sh`：对结果层 contract 做轻量自检

这意味着结果层现在已经从“只有文档约束”升级为“文档 + 模板 + 工具脚本”的组合。

## 当前判断

项目现在已经完成了三件关键事情：

- `qc-mcp` 执行链路已经真实打通
- 仓库级架构边界已经澄清
- 结果层契约已经从 `results.md` 升级为 `results/` 工作区

因此，当前项目已经从“能跑”进入“能稳定沉淀结果”的阶段。

换句话说，当前处于：

- 连通性验证基本完成
- 结果写回协议已经在规范层稳定
- 剩余工作主要是自动化和历史清理

## 下一步

### 第一优先级：把 `results/` 工作区变成默认脚手架

让后续新策略目录默认生成：

- `spec.md`
- `results/state.yaml`
- `results/report.md`
- `results/artifacts/runs/.gitkeep` 或等价初始化结构

### 第二优先级：补自动化写回能力

让后续策略工作流在跑完 `qc-mcp` 后稳定执行：

1. 写原始 artifact
2. 更新 `state.yaml`
3. 刷新 `report.md`

而不是依赖人工手工整理。

### 第三优先级：清理历史 BuildForce artifact 中的 `lp` / Lean 痕迹

重点不是重写历史，而是避免后续 agent 被旧 artifact 误导。

建议至少清理：

- `.buildforce/sessions/**` 中仍然保留的 `lp` 指令
- 任何仍把本地 Lean 当执行路径的 testing guidance 或 plan 内容

### 第四优先级：再考虑轻量 skills

如果继续补技能层，优先级可以放在下面两个：

- `qc-results-analyst`
- `qc-project-checker`

用途分别是：

- 结构化分析 compile / backtest / optimization 输出
- 检查 open project 是否和本地策略目录匹配

### 第五优先级：最后再做 subagents

建议顺序仍然是：

1. 先把 result contract 的自动化补齐
2. 再把历史 artifact 清理掉
3. 再把 skill 映射成 subagent
4. 最后再补 `.claude/agents/*.md`

## 建议的最近落地顺序

1. 为新策略提供统一的 `results/` 初始化模板
2. 把 artifact -> state -> report 的写回顺序做成稳定流程
3. 清理历史 BuildForce artifact 中的 `lp` / Lean 痕迹
4. 如仍有必要，再新增 `qc-results-analyst` 和 `qc-project-checker`
5. 最后再规划 lead agent + subagents

## 一句话总结

现在已经完成了“`qc-mcp` 跑通 + 仓库级边界澄清 + 结果层契约升级”；下一步最重要的不是再争论结果该写成什么，而是把 `results/` 工作区的初始化和自动回写做成默认能力。
