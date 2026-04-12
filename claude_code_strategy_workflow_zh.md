# Claude Code 策略研发机制总结

> 历史说明：本文档分析的是仓库迁移前的 `lp + 本地 Lean` 架构。当前仓库已经切换为 `algorithms/ + Achieve + BuildForce + qc-mcp`，请以 [README.md](/Users/suyongyuan/Downloads/lean-playground-main/README.md) 和 [docs/qc-mcp-integration.md](/Users/suyongyuan/Downloads/lean-playground-main/docs/qc-mcp-integration.md) 为准。

## 1. 项目在做什么

这个仓库的核心目标，不是单纯提供一个 Lean 模板，而是把 `Claude Code` 变成一个可以持续研发交易策略的工作台。

它把整条链路拆成了 4 层：

1. `Claude Code` 负责理解用户目标、调用工具、读写文件、执行命令。
2. `Achieve` 插件负责把“做一个策略”变成一个可持续迭代的目标会话。
3. `BuildForce` 负责把研发过程结构化成 research / plan / build / complete 这类 workflow 和 artifact。
4. `lp` + `Lean` 负责真正创建策略项目、跑回测、生成分析结果。

从仓库定位上看，它更像是一个“AI 驱动的策略研发环境”，而不是单纯的回测脚手架。这个定位在 `README.md` 的开头就写得很明确：用 Claude Code 在可复现的 QuantConnect Lean 环境中写策略、回测、优化。

## 2. 整体架构

可以把当前项目理解成下面这条链：

```mermaid
flowchart LR
    A[用户自然语言目标] --> B[/achieve:goal]
    B --> C[Achieve Session]
    C --> D[research -> plan -> build -> validate]
    D --> E[Claude Code 读写仓库文件]
    E --> F[BuildForce commands / strategy-writer skill]
    F --> G[lp CLI]
    G --> H[Lean Engine]
    H --> I[results/.../main-summary.json]
    I --> J[lp analyze / tearsheet]
    J --> K[Achieve 判断是否达成 success criteria]
    K -->|未达成| D
    K -->|达成| L[结束会话]
```

但要注意一个很重要的边界：

- `Achieve` 和 `BuildForce` 在这个仓库里是并存关系。
- 从当前源码看，不存在“Achieve 内部直接调用 BuildForce CLI”的硬编码证据。
- 更准确的说法是：`Achieve` 负责 loop，`BuildForce` 负责结构化 workflow，`Claude` 在循环里按需使用它们。

## 3. Claude Code 在这里扮演什么角色

这个项目并不是自己实现了一个 agent runtime，它是直接借助 `Claude Code` 本身的能力来运作。

Claude Code 在这里主要负责：

- 执行 slash command
- 调用 plugin
- 调用 skill
- 读写本地文件
- 执行 shell 命令
- 在代码、文档、结果文件之间来回迭代

项目级配置在 `.claude/settings.json` 中。这个文件打开了项目允许的能力，比如 `Bash`、`Read`、`Write`、`Edit`、`WebFetch`、`WebSearch`、`Task`、`Skill` 和 `mcp__*`。同时，它还启用了项目插件 `achieve@claude-achieve-plugin`，并在 `SessionStart` 时执行 `.claude/scripts/auto-install-plugins.sh` 自动安装插件。

换句话说，这个仓库不是自己写了一个“代理框架”，而是把 `Claude Code` 当作现成 agent 宿主，再往上叠加自己的 workflow 和策略研发约束。

## 4. Achieve 插件的原理

### 4.1 它是什么

`Achieve` 是一个 Claude Code 插件。在当前仓库里，它通过 `.claude/settings.json` 开启，并通过 `.claude/scripts/auto-install-plugins.sh` 自动从仓库内 vendored marketplace 安装。

它最重要的命令是：

- `/achieve:goal`
- `/achieve:list-goals`
- `/achieve:cancel-goal`

当前仓库的 `README.md` 也是围绕 `/achieve:goal` 在介绍“自然语言发起策略研发”。

### 4.2 它不是普通提示词，而是真的在做 loop

Achieve 的关键价值，不是单纯替你生成一版计划，而是把目标变成“会自动继续推进”的 session。

`claude-achieve-plugin-main/plugins/achieve/commands/goal.md` 做了 4 件核心事情：

1. 解析用户 goal，提取 success criteria。
2. 估计复杂度，对应最大迭代次数。
3. 调用 `setup-session.sh` 创建会话目录和状态文件。
4. 输出 `ACHIEVE_SESSION: <id>` 标记，然后开始工作。

这个 `ACHIEVE_SESSION` 标记非常关键，因为后面的 stop hook 就靠它识别“当前这段对话是不是 Achieve 会话”。

### 4.3 它如何保存会话状态

`setup-session.sh` 会在 `.claude/achieve-sessions/<session_id>/` 下创建一组文件：

- `state.yaml`
- `loop.md`
- `research.md`
- `spec.yaml`
- `plan.yaml`

其中：

- `state.yaml` 记录 goal、success criteria、当前 phase、attempts 等状态。
- `loop.md` 记录当前 iteration、最大迭代次数、完成 promise 和下一轮提示词。
- `research.md`、`spec.yaml`、`plan.yaml` 是会话内的结构化研发产物。

默认初始 phase 是 `research`。

### 4.4 它的 loop 是怎么实现的

Achieve 真正的“自动循环”依赖 Claude Code 的 `Stop` hook。

在 `claude-achieve-plugin-main/plugins/achieve/hooks/hooks.json` 里，插件注册了一个 `Stop` hook，指向 `stop-hook.sh`。这个脚本的逻辑是：

1. 从 hook 输入里拿到 transcript 路径。
2. 在 transcript 里搜索最近一次 `ACHIEVE_SESSION: <id>`。
3. 找到对应 session 的 `loop.md` 和 `state.yaml`。
4. 检查当前 iteration 是否达到上限。
5. 检查最后一次 assistant 输出里有没有精确的 `<promise>ACHIEVED</promise>`。
6. 如果没有完成，就把 iteration 加 1，阻止 Claude 退出，并把下一轮 prompt 再塞回 Claude。

所以 Achieve 的本质机制是：

- 用文件保存 session 状态
- 用 transcript marker 绑定对话与 session
- 用 `Stop hook` 劫持结束动作
- 用 completion promise 判断是否真的完成

这就是它为什么能“持续往下做”，而不是回答一次就停。

### 4.5 Achieve 的 phase

Achieve 自己定义了一套 phase protocol，在 `claude-achieve-plugin-main/plugins/achieve/templates/protocol.md` 中：

- `research`
- `plan`
- `build`
- `validate`

其运行逻辑是：

- `research`：先理解代码库和上下文。
- `plan`：写规格和实现计划。
- `build`：真正改代码、跑命令、落文件。
- `validate`：对照 success criteria 验证。

如果验证失败，就退回 `build`，继续下一轮；如果全部满足，才允许输出 `<promise>ACHIEVED</promise>` 并结束。

### 4.6 Achieve 与 BuildForce 的关系

Achieve 的 README 明确写了：它的 phase-based workflow 是“受 BuildForce 启发”的。

但严格按当前源码：

- Achieve 有自己的 session 文件体系
- Achieve 有自己的 protocol
- Achieve 有自己的 stop hook loop

因此，Achieve 不是 BuildForce 的一个壳，也不是单纯把 `/buildforce.*` 封装了一层。它是一个独立插件，只是理念上借鉴了 BuildForce。

## 5. BuildForce 的原理

### 5.1 它是什么

`BuildForce` 在这个仓库里不是一个 Claude plugin，而是一个外部 CLI workflow 系统。

它在 `Dockerfile` 中被安装：

- `npm install -g @buildforce/cli`
- `buildforce init .`

安装后，仓库里出现了：

- `.claude/commands/buildforce.research.md`
- `.claude/commands/buildforce.plan.md`
- `.claude/commands/buildforce.build.md`
- `.claude/commands/buildforce.complete.md`
- `.buildforce/buildforce.json`
- `.buildforce/templates/*`
- `.buildforce/scripts/bash/*`
- `.buildforce/sessions/*`

### 5.2 它的核心思路

BuildForce 的核心，不是 hook loop，而是“把研发过程文件化”。

它的关键状态文件是 `.buildforce/buildforce.json`，其中有一个 `currentSession` 字段。围绕这个 session，它会维护一套 artifact：

- `research.yaml`
- `spec.yaml`
- `plan.yaml`

这些 artifact 存在 `.buildforce/sessions/<session>/` 下。

所以 BuildForce 的原理可以概括为：

- 用命令驱动 workflow
- 用模板约束产物结构
- 用 session 文件夹保存上下文
- 用 context / conventions / verification 等目录积累项目知识

### 5.3 它不是状态机，更像文件驱动 workflow

这个仓库里没有看到一个统一的、运行时级别的状态机实现，没有一个 central dispatcher 在根据状态转移表驱动全局行为。

BuildForce 更接近“工作流说明 + 产物模板 + 当前 session 指针”：

- `/buildforce.research` 负责收集背景，并把研究结果持久化到 session 或临时 cache。
- `/buildforce.plan` 负责创建或更新 `spec.yaml` 和 `plan.yaml`。
- `/buildforce.build` 负责按 plan 执行实现、更新任务状态、记录 deviation。
- `/buildforce.complete` 负责收尾、产出 context、清空 `currentSession`。

因此，BuildForce 是一个文件驱动的 workflow 系统，而不是形式化状态机。

### 5.4 它在策略研发里提供什么价值

对策略研发而言，BuildForce 最大的价值是让 Claude 不只是“随手改一下代码”，而是有了结构化产物：

- 策略要解决什么问题
- 功能性/非功能性要求是什么
- 接受标准是什么
- 具体要改哪些文件
- 分几阶段完成
- 如果实现偏离计划，为什么偏离

仓库里已经存在一个实际的 BuildForce session 样本：`.buildforce/sessions/sr-levels-20260128142300/`。从里面可以看到，它已经把“支撑阻力策略”的 research、spec、plan 做成了完整 artifact。

## 6. strategy-writer skill 的作用

除了插件和 workflow，这个仓库还有一个面向策略开发的 domain skill：`.claude/skills/strategy-writer/SKILL.md`。

它不是插件，也不是运行时，而是给 Claude 的“领域操作指南”。

它主要规定了：

- 什么时候自动触发：当用户要求写、创建、构建交易策略时。
- 项目结构应该长什么样。
- 如何先检查数据，再设计策略。
- 如何参考仓库里的 knowledge 文件。
- 如何创建策略项目。
- 如何运行回测并更新结果。

按当前仓库的现行契约，策略项目目录应包含：

- `main.py`
- `spec.md`
- `results/`
- `research.ipynb`（如果团队仍保留研究工作区）

并且要求策略变更后同步更新 `spec.md`，回测后更新 `results/` 工作区。

但这里有一个现实差异：

- `strategy-writer` skill 的理想输出是完整策略包。
- 当前仓库已经补上 `init-result-workspace.sh` 和 `check-result-workspace.sh`，用于初始化和自检结果层。

也就是说，skill 代表的是“理想研发流程”，而结果层现在已经有单独的工具化支撑。

## 7. lp 和 Lean 执行层的原理

### 7.1 `lp` 是什么

`scripts/lp` 是这个仓库自己的 CLI 入口，主要命令有：

- `lp create`
- `lp backtest`
- `lp analyze`
- `lp live`
- `lp browse`
- `lp download`
- `lp data list`
- `lp data info`
- `lp jupyter`
- `lp status`
- `lp update`

这说明项目真正的执行层，不是 BuildForce，也不是 Achieve，而是 `lp`。

### 7.2 回测是怎么跑的

`lp backtest` 最终调用 `scripts/lean_playground/backtest.py`。

这个模块不是走 QuantConnect Cloud，而是：

1. 找到策略目录里的 `main.py`
2. 生成 Lean 所需的 config
3. 直接执行 `dotnet QuantConnect.Lean.Launcher.dll --config ...`

也就是说，这个仓库当前默认走的是“本地 Lean 引擎回测”。

`scripts/lean_playground/config.py` 的注释写得很明确：这是为了在不依赖 Lean CLI 登录和认证的情况下，直接运行 Python backtest。

### 7.3 分析结果是怎么产出的

`lp analyze` 会调用 `scripts/lean_playground/analyze.py`：

- 找到最新一次回测输出目录
- 读取 `main-summary.json` 或 `main.json`
- 取出 equity curve 和统计指标
- 生成 `tearsheet.html`

因此，“策略研发结果”在当前仓库里最终落地为两类内容：

- `algorithms/{name}/main.py` 这类策略代码
- `results/{name}/{timestamp}/...` 这类回测结果和分析报告

### 7.4 实盘和数据层为什么也自己做了

这个仓库自己补了很多本地能力：

- `download.py`：直接下载 Binance 数据并转成 Lean 格式
- `brokerages.py`：从 Lean modules 解析券商配置
- `live.py`：直接启动 Lean live/paper trading
- `jupyter.py`：启动 QuantBook/Jupyter 研究环境

这些能力存在的原因很简单：

- 这个仓库设计时希望“即使没有 QuantConnect 账号，也能在本地完成策略研发和回测”

所以它自己补齐了很多原本 QC 平台或 Lean CLI 可以提供的东西。

## 8. 项目到底是如何用 Claude Code 生成策略的

把所有部分拼起来，当前项目的真实工作方式可以总结成下面这几步：

1. 用户给 Claude 一个自然语言目标，例如“做一个 Sharpe 大于 1.5 的动量策略”。
2. 用户通过 `/achieve:goal` 发起会话。
3. Achieve 解析 goal，创建 session 文件，并进入 `research` phase。
4. Claude 在研究阶段读取代码库、现有算法样例、skill 知识库和已有 session artifact。
5. Claude 在计划阶段形成结构化 spec / plan。
6. Claude 在构建阶段调用 `lp create`、写 `main.py`、可能更新 notebook、文档和配置。
7. Claude 调用 `lp backtest` 跑 Lean 引擎。
8. Claude 读取回测结果，必要时调用 `lp analyze` 生成 tearsheet。
9. Achieve 在 `validate` 阶段对照 success criteria 判断是否达成。
10. 若未达成，stop hook 会继续下一轮；若达成，输出 `<promise>ACHIEVED</promise>` 结束。

所以，这个仓库里“策略生成”的本质不是一次性生成代码，而是：

`Claude Code + domain skill + loop plugin + workflow artifact + local Lean execution`

## 9. 当前实现的特点与边界

### 9.1 已经实现得比较清楚的部分

- `Achieve` 的 loop 机制是完整的。
- `BuildForce` 的 workflow 和 artifact 体系是完整的。
- `lp` 的本地 Lean 回测/分析链路是完整的。
- `strategy-writer` skill 已经给出了明确的策略研发指引。

### 9.2 还没有完全收口的部分

- `strategy-writer` 想要的 `spec.md` 和 `results/` 工作区，现在已经有独立的 init/check 工具，但策略脚手架本身仍未自动生成完整策略包。
- 仓库没有看到显式的 subagent 编排。
- 仓库没有形式化状态机实现。
- Achieve 与 BuildForce 虽然理念一致，但没有看到 Achieve 直接调用 BuildForce 的硬编码集成。

### 9.3 当前更接近什么产品形态

它更接近一个“Claude Code 驱动的本地策略研发工作台”，而不是一个完全产品化、强约束、端到端封闭的策略平台。

换句话说：

- 它已经能跑通“目标 -> 策略代码 -> 回测 -> 分析 -> 再迭代”的主链路。
- 但在“统一 artifact 规范”“自动补全策略文档”“显式实验管理”“更强的结果归档”这些方面，还没有完全做完。

## 10. 一句话结论

这个项目的核心设计，不是让 Claude Code 一次性写出一段策略代码，而是通过：

- `Achieve` 提供目标驱动的自动 loop
- `BuildForce` 提供结构化 workflow 和 artifact
- `strategy-writer` 提供策略领域知识和操作规范
- `lp + Lean` 提供真实的本地执行与回测能力

把 Claude Code 变成一个可以持续推进、持续验证、持续优化策略的研发代理。

## 11. 关键源码入口

如果你后续要继续研究这个项目，最值得优先阅读的文件是下面这些：

- `README.md`：项目定位、用户入口、`lp` 命令说明。
- `.claude/settings.json`：Claude Code 项目权限、插件启用、MCP 开关。
- `.claude/scripts/auto-install-plugins.sh`：Achieve 插件自动安装逻辑。
- `.claude/skills/strategy-writer/SKILL.md`：策略研发的领域工作流说明。
- `.claude/commands/buildforce.research.md`：BuildForce research 阶段说明。
- `.claude/commands/buildforce.plan.md`：BuildForce plan 阶段说明。
- `.claude/commands/buildforce.build.md`：BuildForce build 阶段说明。
- `.claude/commands/buildforce.complete.md`：BuildForce complete 阶段说明。
- `.buildforce/buildforce.json`：BuildForce 当前 session 状态入口。
- `.buildforce/sessions/sr-levels-20260128142300/`：一个真实的策略研发 artifact 样本。
- `scripts/lp`：本仓库自定义 CLI 入口。
- `scripts/lean_playground/project.py`：策略项目脚手架创建逻辑。
- `scripts/lean_playground/backtest.py`：本地 Lean 回测执行逻辑。
- `scripts/lean_playground/analyze.py`：回测结果分析和 tearsheet 生成逻辑。
- `scripts/lean_playground/live.py`：本地 live/paper trading 执行逻辑。
- `claude-achieve-plugin-main/README.md`：Achieve 插件说明。
- `claude-achieve-plugin-main/plugins/achieve/commands/goal.md`：Achieve goal 命令入口。
- `claude-achieve-plugin-main/plugins/achieve/scripts/setup-session.sh`：Achieve session 创建逻辑。
- `claude-achieve-plugin-main/plugins/achieve/templates/protocol.md`：Achieve phase protocol。
- `claude-achieve-plugin-main/plugins/achieve/hooks/hooks.json`：Achieve hook 注册。
- `claude-achieve-plugin-main/plugins/achieve/hooks/stop-hook.sh`：Achieve 自动 loop 的核心实现。
