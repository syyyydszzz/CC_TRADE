# QC Strategy Template Repo

用 AI 辅助开发 QuantConnect 量化交易策略的工程化框架。本 repo 是脚手架生成器，不是某个具体策略的家。

## 快速开始

在 Claude Code 里直接用自然语言描述策略意图：

```
/strategy.init 做一个 QQQ 的动量策略，日线级别
/strategy.init NVDA 趋势跟踪，周线，保守风控
/strategy.init 多标的轮动策略，SPY/QQQ/IWM，月度再平衡
```

或者用脚本直接生成（`--asset` 默认 SPY，`--resolution` 支持 daily / hourly / minute）：

```bash
bash scripts/new-strategy-repo.sh \
  --project-name my-strategy-v1 \
  --target-dir ~/strategy-repos \
  --asset QQQ \
  --resolution daily
```

## 生成的仓库结构

```
main.py          # 策略源码（唯一真相）
spec.md          # 策略规格说明
results/         # 回测结果层
openspec/        # 变更管理工作流
.claude/         # Claude 技能和命令
scripts/         # 工具脚本
```

## 策略迭代工作流

### 完整流程

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 0: 探索                                                  │
│                                                                 │
│  触发: /opsx.explore                                            │
│  ├── 读 AGENTS.md, openspec/specs/, spec.md, results/           │
│  └── 输出: 范围摘要 / 关键文件 / 前置条件 / 开放问题 (纯对话)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: 提案                                                  │
│                                                                 │
│  触发: /opsx.propose <change-id>                                │
│  └── 产出 openspec/changes/{change}/                            │
│      ├── proposal.md                                            │
│      ├── specs/strategy-project/spec.md                         │
│      ├── research.md                                            │
│      ├── design.md                                              │
│      └── tasks.md                                               │
│                                                                 │
│  可选预检: /opsx.review <change-id>                             │
│  └── 召唤 review-pre subagent → READY / NOT_READY              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: 执行                                                  │
│                                                                 │
│  触发: /opsx.apply <change-id>                                  │
│  │                                                              │
│  │  [自动] SUBAGENT 1: qc-implementer                          │
│  │  ├── 读 tasks.md / specs / design.md                        │
│  │  ├── 写 main.py + spec.md                                   │
│  │  └── 追加 execution-log.md                                  │
│  │              ↓ GATE (BLOCKED → 停止)                        │
│  │  [自动] SUBAGENT 2: qc-executor                             │
│  │  ├── qc-mcp: compile → backtest                             │
│  │  └── 写 results/: compile.json → backtest.json              │
│  │      → run.yaml → state.yaml → report.md                    │
│  │              ↓ GATE (BLOCKED → 停止)                        │
│  │  [自动] SUBAGENT 3: review-result  ← 冷读，无上下文传递     │
│  │  ├── 读 proposal.md / report.md / state.yaml / main.py      │
│  │  └── 输出: APPROVE / REVISE / BLOCKED                       │
│                                                                 │
│  也可单独触发: /opsx.review-result <change-id> [run-id]        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ APPROVE
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: 验证                                                  │
│                                                                 │
│  触发: /opsx.verify <change-id>                                 │
│  ├── opsx.sh validate + check-result-workspace.sh               │
│  └── 逐条核对 proposal.md success criteria                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: 归档                                                  │
│                                                                 │
│  触发: /opsx.archive <change-id>                                │
│  ├── delta specs 合并入 openspec/specs/                         │
│  └── change 目录移至 openspec/changes/archive/                  │
│                                                                 │
│  可选复盘: /reflect <change-id>                                 │
│  └── 召唤 opsx-reflector → 写经验到 skill knowledge            │
└─────────────────────────────────────────────────────────────────┘
```

### 命令速查

| 命令 | 阶段 | 产出文件 |
|------|------|----------|
| `/opsx.explore` | 探索 | 无（纯对话） |
| `/opsx.propose <id>` | 提案 | openspec/changes/{id}/ |
| `/opsx.review <id>` | 提案预检（可选） | 无 |
| `/opsx.apply <id>` | 执行（编排 3 个 subagent） | main.py + results/ |
| `/opsx.review-result <id>` | 结果独立评审（可单独触发） | 无 |
| `/opsx.verify <id>` | 验证 | 无 |
| `/opsx.archive <id>` | 归档 | openspec/changes/archive/ |
| `/reflect <id>` | 复盘（可选） | skill knowledge 文件 |

> 提示：可以在 `/opsx.explore` 之前用 Claude Code 的 Plan 模式做更高层的策略方向讨论，对齐思路后再进入工作流。

QC 同步：

```
/qc.sync-status  # 检查本地与 QC 云端是否同步
/qc.sync         # 推送代码到 QC 云端
```

## 环境依赖

| 组件 | 说明 |
|------|------|
| `qc-mcp` | QuantConnect MCP 服务，运行在 `localhost:3001`，配置在 `~/.claude.json` |
| `context7` | 文档查询 MCP，通过 `npx` 按需启动 |
| `chrome-devtools` | 浏览器调试 MCP，配置在 `~/.claude.json` |
| Python venv | `.venv/`，Python 3.9，含 numpy 等基础依赖 |

启动前检查：

```bash
bash scripts/check-qc-mcp.sh
```

## 目录说明

```
template/single-strategy-repo/   # 单策略仓库骨架
scripts/new-strategy-repo.sh     # 脚手架生成脚本
openspec/                        # OpenSpec 变更管理合约
workflow/                        # 结果层合约模板
.claude/                         # Claude 命令、技能、Agent 定义
examples/strategies/             # 示例策略（仅供参考）
docs/                            # qc-mcp 集成文档
external/                        # 外部技能包
```
