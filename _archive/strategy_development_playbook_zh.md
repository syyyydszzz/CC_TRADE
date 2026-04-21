# 新策略研发操作手册

## 目标

当前仓库的新策略研发流程已经统一为：

- `algorithms/<strategy>/` 是源码主位
- `openspec/changes/<change>/` 是 planning artifact 主位
- `qc-mcp` 是唯一执行层
- `algorithms/<strategy>/results/` 是结果证据主位

## 推荐入口

在 Claude Code 中优先使用：

```text
/strategy.init sma_probe_strategy_v1
/opsx:propose
/opsx:apply
/opsx:verify
/opsx:archive
```

如果你需要 QC 同步辅助命令：

```text
/strategy.sync-status sma_probe_strategy_v1
/strategy.sync sma_probe_strategy_v1
```

## 终端脚本

```bash
bash scripts/bootstrap-python-env.sh
bash scripts/init-strategy-dev.sh --strategy-name sma_probe_strategy_v1
bash scripts/prepare-qc-project.sh --strategy-path algorithms/sma_probe_strategy_v1
bash scripts/check-result-workspace.sh --strategy-path algorithms/sma_probe_strategy_v1
```

## 结果层写入顺序

1. raw artifacts -> `results/artifacts/runs/{run_id}/`
2. `bash scripts/record-result-run.sh ...`
3. `bash scripts/record-result-state.sh ...`
4. 更新 `results/report.md`
5. `bash scripts/check-result-workspace.sh --strategy-path algorithms/<strategy>`

## 可选薄 Loop

默认不需要 loop。

如果你已经有一个 OpenSpec change，并且想要 stop-hook 式续跑：

```bash
bash scripts/opsx-session-start.sh --change-id <change-id> --goal "<goal>"
```

## 说明

旧的 BuildForce / Achieve 方案已经从主流程移除；本文件只保留当前可执行流程。
