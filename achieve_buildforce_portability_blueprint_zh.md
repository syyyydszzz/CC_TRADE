# Achieve / BuildForce 可移植集成蓝图

> 历史说明：本文档包含基于旧执行层的拆解与迁移分析。当前仓库的执行契约已经收敛到 `qc-mcp`，请结合 [README.md](/Users/suyongyuan/Downloads/lean-playground-main/README.md) 和 [docs/qc-mcp-integration.md](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-integration.md) 一起阅读。

## 1. 总览

- `Achieve`：Claude Code 的 goal loop 插件，负责把一个目标变成可持续推进的 session。
- `BuildForce`：结构化 workflow / artifact 系统，负责把研发过程沉淀为 research / spec / plan / context。

在当前仓库里，它们是并存关系：

- `Achieve` 解决“自动继续做”
- `BuildForce` 解决“做的时候有结构和产物”
- 它们都服务于 Claude Code，但没有看到 Achieve 直接调用 BuildForce 的硬编码证据

## 2. Achieve 可迁移能力

### 核心能力

- session 创建：[`goal.md`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/commands/goal.md#L57)
- success criteria 提取：[`goal.md`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/commands/goal.md#L14)
- phase protocol：`research -> plan -> build -> validate`，见 [`protocol.md`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/templates/protocol.md#L15)
- state files：`state.yaml / loop.md / research.md / spec.yaml / plan.yaml`，见 [`setup-session.sh`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/scripts/setup-session.sh#L124)
- stop hook loop：[`hooks.json`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/hooks/hooks.json#L4)、[`stop-hook.sh`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/hooks/stop-hook.sh#L128)
- completion 判定：精确匹配 `<promise>ACHIEVED</promise>`，见 [`stop-hook.sh`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/hooks/stop-hook.sh#L114)

### Claude Code 侧依赖

- plugin
- slash commands
- `Stop` hook
- transcript marker：`ACHIEVE_SESSION: <id>`
- file-based state

### 最小可移植子集

- [`plugins/achieve/.claude-plugin/plugin.json`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/.claude-plugin/plugin.json)
- [`plugins/achieve/commands/goal.md`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/commands/goal.md)
- [`plugins/achieve/scripts/setup-session.sh`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/scripts/setup-session.sh)
- [`plugins/achieve/templates/protocol.md`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/templates/protocol.md)
- [`plugins/achieve/hooks/hooks.json`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/hooks/hooks.json)
- [`plugins/achieve/hooks/stop-hook.sh`](/Users/suyongyuan/Downloads/lean-playground-main/claude-achieve-plugin-main/plugins/achieve/hooks/stop-hook.sh)

## 3. BuildForce 可迁移能力

### 核心能力

- commands workflow：
  - [`buildforce.research.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.research.md)
  - [`buildforce.plan.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.plan.md)
  - [`buildforce.build.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.build.md)
  - [`buildforce.complete.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.complete.md)
- session 状态入口：[`buildforce.json`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/buildforce.json#L1)
- session 创建脚本：[`create-session-files.sh`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/scripts/bash/create-session-files.sh#L65)
- root / currentSession 管理：[`common.sh`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/scripts/bash/common.sh#L4)
- artifact 模板：
  - [`spec-template.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/templates/spec-template.yaml#L1)
  - [`plan-template.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/templates/plan-template.yaml#L1)
  - [`research-template.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/templates/research-template.yaml#L1)
- context 骨架：[`context/_index.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/context/_index.yaml#L1)

### 在非交易项目里还能保留什么

几乎都能保留。  
BuildForce 的模板本身是通用研发模板，不依赖 Lean / 策略 / QuantConnect。

### 最小可移植子集

- [`.buildforce/buildforce.json`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/buildforce.json)
- [`.buildforce/scripts/bash/common.sh`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/scripts/bash/common.sh)
- [`.buildforce/scripts/bash/create-session-files.sh`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/scripts/bash/create-session-files.sh)
- [`.buildforce/templates/spec-template.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/templates/spec-template.yaml)
- [`.buildforce/templates/plan-template.yaml`](/Users/suyongyuan/Downloads/lean-playground-main/.buildforce/templates/plan-template.yaml)
- [`.claude/commands/buildforce.plan.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.plan.md)
- [`.claude/commands/buildforce.build.md`](/Users/suyongyuan/Downloads/lean-playground-main/.claude/commands/buildforce.build.md)

## 4. 通用层 vs 领域层

### 通用可复用层

- Achieve 的 goal session + stop hook loop
- BuildForce 的 spec / plan / research artifact
- Claude Code 项目级 commands / hooks / file-state 驱动方式

### 不应默认迁移的领域层

- `lp` CLI：[scripts/lp](/Users/suyongyuan/Downloads/lean-playground-main/scripts/lp)
- Lean 执行层：[backtest.py](/Users/suyongyuan/Downloads/lean-playground-main/scripts/lean_playground/backtest.py#L1)
- QuantConnect / brokerage / live / data 下载层：
  - [live.py](/Users/suyongyuan/Downloads/lean-playground-main/scripts/lean_playground/live.py#L1)
  - [brokerages.py](/Users/suyongyuan/Downloads/lean-playground-main/scripts/lean_playground/brokerages.py#L1)
  - [download.py](/Users/suyongyuan/Downloads/lean-playground-main/scripts/lean_playground/download.py#L1)
- 策略 skill：[strategy-writer/SKILL.md](/Users/suyongyuan/Downloads/lean-playground-main/.claude/skills/strategy-writer/SKILL.md#L1)
- `algorithms/`、`research/`、样本 session、Lean Dockerfile

## 5. 迁移清单

### 必须迁移

- Achieve plugin 或其等价实现
- `.claude/settings.json` 中的 plugin / hook 启用逻辑
- `.buildforce/buildforce.json`
- `.buildforce/scripts/bash/common.sh`
- `.buildforce/scripts/bash/create-session-files.sh`
- `.buildforce/templates/spec-template.yaml`
- `.buildforce/templates/plan-template.yaml`
- `.claude/commands/buildforce.plan.md`
- `.claude/commands/buildforce.build.md`

### 建议迁移

- `.claude/commands/buildforce.research.md`
- `.claude/commands/buildforce.complete.md`
- `.buildforce/templates/research-template.yaml`
- `.buildforce/context/_index.yaml`
- `.claude/scripts/auto-install-plugins.sh`
- `list-goals.md` / `cancel-goal.md`

### 可以重写替代

- shell 脚本可改成 Python / Node
- YAML 模板可换成你自己的字段
- `/buildforce.*` 命令名可重命名
- plugin 安装方式可改为手动 bootstrap

### 不建议迁移

- `scripts/lean_playground/*`
- `scripts/lp`
- `.claude/skills/strategy-writer/`
- `algorithms/`
- `.buildforce/sessions/sr-levels-20260128142300/`

## 6. 集成契约

Achieve / BuildForce 在 Claude Code 中主要依赖这些能力：

- slash commands
- plugin
- hooks
- session transcript marker
- file-based state
- skills
- shell scripts

目标项目中的替代方式：

- 没有 plugin：改成 repo 内脚本 + 固定命令入口
- 没有 hooks：改成手动 `/continue`，但会失去自动 loop
- 没有 transcript marker：改成 `active_session` 文件或环境变量
- 没有 skills：用 `AGENTS.md` 或项目说明文档代替
- 不想用 shell：重写成 Python / Node

## 7. 最小移植方案

### 最小目录结构

```text
your-project/
  .claude/
    settings.json
    scripts/
      auto-install-plugins.sh
    commands/
      buildforce.plan.md
      buildforce.build.md
  .buildforce/
    buildforce.json
    scripts/
      bash/
        common.sh
        create-session-files.sh
    templates/
      spec-template.yaml
      plan-template.yaml
```

### 最小状态文件集合

- `.claude/achieve-sessions/index.yaml`
- `.claude/achieve-sessions/<id>/state.yaml`
- `.claude/achieve-sessions/<id>/loop.md`
- `.buildforce/buildforce.json`
- `.buildforce/sessions/<session>/spec.yaml`
- `.buildforce/sessions/<session>/plan.yaml`

### 最小 phase 设计

- `research`
- `plan`
- `build`
- `validate`

### 最小 hook 机制

- 只保留 `Stop hook`
- 只保留 transcript marker + completion promise + iteration 计数

### 最小 commands / skills

- `/achieve:goal`
- `/buildforce.plan`
- `/buildforce.build`
- skills 可以先不迁，后面按领域再加

### 建议集成顺序

1. 先移植 Achieve loop
2. 再移植 BuildForce artifact
3. 最后再加 research / complete / context / skills

## 8. 实施路线图

### Phase 1: 只移植 loop 能力

- 迁 Achieve plugin
- 打通 `/achieve:goal`
- 打通 session files + stop hook

### Phase 2: 加入 artifact/workflow 能力

- 迁 `.buildforce/`
- 打通 `/buildforce.plan`
- 打通 `/buildforce.build`

### Phase 3: 做成可复用模板

- 加 `research-template.yaml`
- 加 `/buildforce.research` 和 `/buildforce.complete`
- 加 `context/`
- 抽成 repo template / bootstrap 脚本

## 9. 风险与限制

- Achieve 强依赖 Claude Code 的 plugin + hook + transcript 机制，离开这个宿主不能原样工作。
- BuildForce 当前仓库里是“初始化后的项目文件”，不是 `@buildforce/cli` 源码本体。
- Achieve 和 BuildForce 当前并没有硬集成，照搬后不要期待自动联动。
- 当前 repo 中的交易 skill、Lean 执行层、样本 session 很容易把目标项目带偏到量化语境。

## 精简架构图

```mermaid
flowchart LR
    A[User Goal] --> B[/achieve:goal]
    B --> C[Achieve Session Files]
    C --> D[research]
    D --> E[/buildforce.plan]
    E --> F[spec.yaml + plan.yaml]
    F --> G[/buildforce.build]
    G --> H[Project Code / Tests]
    H --> I[validate]
    I --> J{Criteria Met?}
    J -->|No| K[Stop Hook blocks exit and loops]
    K --> D
    J -->|Yes| L[Emit completion promise]
```
