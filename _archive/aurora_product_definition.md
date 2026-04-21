# Aurora Product Definition

## 文档目的

这份文档定义 Aurora 作为一个产品到底是什么，不讨论具体代码实现细节，不替代 runtime architecture / contracts 文档。

它主要回答 8 个问题：

1. Aurora 是什么产品
2. Aurora 不是什产品
3. Aurora 面向谁
4. 用户为什么要用它
5. Aurora 的核心产品表面是什么
6. Aurora 的核心对象和交付物是什么
7. Aurora 的自动化、审批、预算边界是什么
8. Aurora 与底层 agent framework / worker / provider 的关系是什么

相关文档：

- `external_architecture_notes.md`
- `native_runtime_architecture.md`
- `runtime_state_and_contracts.md`

## 一句话定义

Aurora 是一个 `AI-native trading strategy operating system`：

- 它不是单纯的聊天机器人
- 它不是单纯的回测工具
- 它不是单纯的交易执行 bot
- 它是一个把“策略研究、验证、优化、交付、部署衔接”统一起来的 agent 产品入口

更具体地说：

`Aurora 是一个以主研究 agent 为核心、以异步 worker/provider 为执行引擎、以 artifact 为主要交付物的自主单策略研究与优化产品。`

## 产品定位

Aurora 的核心定位是：

- 一个 `strategy research agent`
- 一个 `single-strategy operating assistant`
- 一个 `AI entrypoint`，连接用户意图、策略研究、平台工具和后续执行链路

更具体地说，Aurora 当前的主目标不是“自动发现全新 alpha 因子”，而是：

- 把用户的交易想法、约束和偏好转成结构化策略研究任务
- 生成一个可测试、可执行的交易策略方案
- 将该方案编译成可执行规则或策略规范
- 调用回测和优化工具验证并改进它
- 输出一份可审阅、可追踪、可继续迭代的策略 artifact

Aurora 解决的不是“帮用户回答市场问题”，而是：

- 把模糊目标转成结构化研究任务
- 把研究任务转成可验证的实验和可迭代的策略方案
- 把结果转成可审阅、可追踪、可落地的 artifact
- 在需要时继续衔接优化、策略编辑、部署、触发器等产品能力

## 非目标

Aurora 当前不是：

- 一个高频自动交易引擎
- 一个裸策略生成器
- 一个纯聊天问答助手
- 一个完全自由发挥、没有审批和预算边界的 autonomous swarm
- 一个只输出一句“买/卖/持有”建议的投顾 bot
- 一个以因子发现、横截面 alpha 挖掘和统计显著性研究为核心目标的量化科研平台

Aurora 不应被定义为：

- “大模型帮我写一点策略”
- “自动帮我下单的黑盒”
- “把回测结果包成一段自然语言说明”
- “让 LLM 自动挖出神奇新因子并直接证明有效”

## 目标用户

Aurora 主要面向以下用户：

- 想做策略研究但不想手写大量代码的量化用户
- 想快速把交易想法转成可验证方案的主动投资者
- 想通过 agent 统一完成研究、验证、优化和交付的高级用户
- 想把策略触发、研究分析和部署动作接进同一产品面的平台用户

次级用户包括：

- 需要快速生成研究草案和策略初版的研究员
- 需要审阅 agent 产出并做人类最终判断的策略负责人
- 需要把 AI 研究结果接进产品工作流的运营方

## 核心用户任务

Aurora 的核心 jobs-to-be-done 是：

- “我有一个交易想法，你把它变成研究计划和一个可测试的策略。”
- “我不想只听建议，我要看这个策略测试过什么、改过什么、现在为什么值得继续。”
- “我想让 agent 自动研究，但在关键点停下来让我确认。”
- “我想让平台里的策略、watchlist、触发器都能调用这个 agent。”
- “我想让研究结果成为后续优化、部署或管理动作的起点。”

Aurora 当前最核心的产品任务应聚焦在：

- `strategy ideation`
- `strategy validation`
- `strategy optimization`
- `artifact generation`

而不是优先聚焦在：

- `factor mining`
- `feature discovery`
- `large-scale quant research infrastructure`

## 核心产品形态

Aurora 不是单一界面，而是一个多入口产品能力。

Aurora 至少应有以下产品表面：

- `Chat Mode`
- `Agent Mode`
- `Semi-Automated Mode`
- `Automated Mode`
- `Platform-triggered Agent Launch`
- `Artifact Review Surface`

### Chat Mode

Chat Mode 用于：

- 快速问答
- 市场解释
- 策略想法澄清
- 轻量研究准备
- 用户意图补全

Chat Mode 不是主研究执行模式。

### Agent Mode

Agent Mode 用于：

- 启动完整研究任务
- 自动推进研究与验证步骤
- 调用工具、provider、subagents
- 生成 artifact
- 在命中策略边界时停下

Agent Mode 是 Aurora 的主产品模式。

### Semi-Automated Mode

默认模式建议为 `semi_automated`：

- 计划审批是稳定停点
- 最终 artifact 审批是稳定停点
- 研究和验证在预算内自动推进
- provider wait 和异常会中断并等待恢复

### Automated Mode

Automated Mode 用于：

- 最大化自动推进
- 减少中间人工停点
- 仅在高风险条件、失败条件或明确升级条件下停住

### Manual Mode

Manual Mode 用于：

- 更强的人审和流程可见性
- 更高要求的风控或实验审查场景
- 更适合早期调试、审计和敏感策略实验

## Aurora 的核心产品对象

Aurora 的产品对象不只是消息，而是结构化研究对象。

核心对象包括：

- `ResearchSession`
- `ResearchRequest`
- `ResearchPlan`
- `StrategyHypothesis`
- `StrategySpec`
- `ValidationReport`
- `OptimizationReport`
- `StrategyArtifact`
- `ApprovalDecision`
- `ProviderRunRef`

其中最重要的用户可感知对象是：

- `ResearchPlan`
- `StrategySpec`
- `Validation Record`
- `Final Artifact`

## 核心交付物

Aurora 的主要交付不是一句自然语言，而是 `artifact-first` 结果。

Aurora 的核心交付物应包括：

- 用户目标的规范化表达
- 研究计划
- 当前策略假设
- 策略修订与优化记录
- 编译后的策略规范
- 回测与优化结果引用
- 风险说明
- 推荐理由
- 运行轨迹摘要
- 外部 handoff 引用

一句话说：

`Aurora 交付的是研究结果包，而不是聊天答案。`

## 产品能力边界

Aurora 的产品能力至少包括：

- 解释用户目标
- 生成研究计划
- 设计单个策略方案
- 调用研究工具和 provider
- 执行回测和优化
- 汇总验证与优化结果
- 输出 artifact
- 支持审批与恢复
- 在平台内触发后续动作

Aurora 不应直接承担的能力包括：

- 数值回测本身
- 优化算法本身
- broker execution engine 本身
- 底层市场数据真源本身
- 全自动因子发现流水线
- 复杂统计检验平台本体
- 大规模 feature store / factor lab 基础设施

这些能力应由 worker/provider/platform services 承担。

## Agent、Subagent、Worker 的产品定义

### Main Agent

Aurora 的主 agent 是：

- 研究 conductor
- 用户目标解释器
- 研究 agenda 管理者
- 结果综合者
- artifact narrative 组织者

主 agent 不是：

- 业务真状态 owner
- 数值执行引擎
- 直接写底层持久化的组件

### Cognitive Child Agents

Aurora 的 child agents 用于：

- ideation
- critique
- revision
- validation synthesis
- artifact drafting/review

它们是受控的认知子任务执行者，不是平台主控。

### Workers / Providers

Aurora 的 workers/providers 用于：

- screen
- full backtest
- optimization
- remote long-running experiment execution

它们不负责开放式推理，只负责结构化执行和结构化结果返回。

## 产品运行模型

Aurora 的运行模型应被定义为：

`User Goal -> Planner -> Research Episode -> Provider/Worker Execution -> Strategy Revision -> Final Artifact`

它不是：

`User Chat -> One-shot LLM Answer`

Aurora 的默认运行逻辑应包括：

- planner-led 任务启动
- ReAct-style phase execution
- provider-backed long-running jobs
- policy-controlled approvals
- persistent state and resume
- artifact-first delivery

## 自动化、审批与预算表面

Aurora 必须把这些能力作为产品配置面，而不是隐藏实现细节：

- `automation_mode`
- `approval_policy`
- `planning_model`
- `execution_model`
- `child_agent_budget`
- `episode_step_budget`
- `provider escalation policy`
- `risk escalation policy`

### 默认策略

建议默认值：

- `automation_mode = semi_automated`
- `approval_policy = risk_based`
- `plan review` 为稳定停点
- `final artifact review` 为稳定停点

### 为什么这是产品能力

因为用户在产品里实际感知到的是：

- Aurora 能跑多远
- Aurora 什么时候会停下来问我
- Aurora 会不会自动优化
- Aurora 是否会因为风险或 provider 条件升级审批

## 与平台的关系

Aurora 不是孤立 agent，而是平台能力入口。

Aurora 应与以下平台对象互通：

- watchlists
- screeners
- strategies
- actions / triggers
- deployment targets
- research reports

Aurora 不应只是“在一个聊天框里研究”，而应成为平台内的智能操作层。

## 典型用户路径

### 路径 1：从想法到研究 artifact

- 用户输入一个模糊策略目标
- Aurora 生成研究计划
- 用户审阅计划
- Aurora 自动推进研究与验证
- Aurora 输出 artifact
- 用户决定接受、修改、继续优化

### 路径 2：从平台触发器到策略分析

- 某个 strategy/action 触发 Aurora
- Aurora 获取平台上下文
- Aurora 执行定向研究或策略调整建议
- Aurora 返回结构化建议或触发后续流程

### 路径 3：从已生成 artifact 到继续优化

- 用户查看 artifact
- Aurora 判断是否仍值得优化
- 如果需要，Aurora 回到验证/优化流程
- 如果足够成熟，再进入最终审批或 handoff

## 成功标准

Aurora 的产品成功不只看模型回答是否流畅，还看：

- 用户是否能把模糊目标成功转成研究 artifact
- 单个策略的验证和优化轨迹是否清晰、可追踪
- 回测和优化结果是否能稳定接入研究流程
- 审批和恢复是否自然、明确、可解释
- artifact 是否足够支持后续部署或人工决策
- 用户是否把 Aurora 当作“研究和策略入口”，而不是临时聊天工具

## 设计原则

Aurora 的产品设计应坚持以下原则：

- `artifact-first`
- `planner-led`
- `agentic inside, guardrailed outside`
- `workers for execution, agents for reasoning`
- `persistent and resumable`
- `platform-native, not chat-only`
- `human review where it matters`
- `structured state over prompt-only state`

## Aurora 与底层框架的关系

Aurora 不等于底层 agent framework。

底层框架负责：

- agent loop
- tool integration
- MCP
- hooks
- subagent delegation
- session/memory plumbing

Aurora 自己负责：

- 量化研究产品定义
- 研究状态与 artifact contracts
- worker/provider orchestration
- approval/risk/product policy
- strategy research and platform integration

因此，Aurora 应被实现为：

`一个建立在成熟 agent harness 之上的领域产品层`

而不是：

`重新发明一个通用 agent framework`

## 当前开放问题

以下问题需要在产品层继续明确：

- Aurora 是否默认严格聚焦单策略研究，还是后续扩展到更广的平台运营
- 哪些平台动作允许 Aurora 直接触发
- 哪些条件触发自动升级审批
- final artifact review 后是否允许 machine-led re-entry
- child agents 的默认预算和并发策略是什么
- research token / cost budget 应如何对用户暴露
- Aurora 的部署和 broker 边界应如何定义

## 当前结论

Aurora 应被定义为：

- 一个 AI-native trading strategy operating system
- 一个 planner-led、tool-using、worker-backed 的研究 agent 产品
- 一个把用户意图、研究、验证、artifact 和平台动作接起来的统一入口
- 一个以“交易策略生成、验证、优化、交付”为主目标的 agent，而不是以“因子挖掘”为主目标的科研系统

Aurora 不应被缩减理解为：

- 聊天机器人
- 回测包装器
- 自动交易黑盒
- 纯工作流引擎
