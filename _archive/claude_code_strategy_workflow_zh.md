# Claude Code 策略研发机制总结

## 当前机制

当前仓库的策略研发链路已经简化为：

1. Claude Code 负责读写代码、调用脚本和 MCP
2. OpenSpec 负责 proposal / research / design / tasks
3. `qc-mcp` 负责 compile / backtest / optimization / validation
4. `results/` 负责机器可读结果和原始工件落盘

## 默认入口

- `/strategy.init`
- `/opsx:explore`
- `/opsx:propose`
- `/opsx:apply`
- `/opsx:verify`
- `/opsx:archive`

## 可选能力

- `scripts/prepare-qc-project.sh` / `scripts/sync-qc-project.sh`：QC 镜像同步
- `scripts/opsx-session-start.sh`：可选薄 loop

## 说明

旧的 `BuildForce` workflow 和 `.buildforce/` 目录已移除；本文件只保留当前架构摘要。
