# TQQQ 新仓测试指引

这份文档用于验证当前模板仓修复后的新仓链路是否可用。

测试目标：

- 用模板仓生成一个全新的 TQQQ 单策略仓
- 在新仓里完成 bootstrap 检查
- 跑一遍 `/opsx.propose -> /opsx.apply -> /opsx.verify -> /opsx.archive`
- 重点确认 OpenSpec CLI 对齐、`specs/` 产物、以及 `results/` 结果真源一致性

建议本次测试仓名：

- `tqqq-ema-daily-v1`

建议本次测试策略：

- `TQQQ daily EMA crossover`

## 1. 开始前先检查

在模板仓里开始之前，先确认这些前置条件：

1. 你现在所在目录是模板仓根目录，也就是当前这个仓。
2. 你准备把新仓生成到一个新的目录，不要复用旧测试仓。
3. QuantConnect Local Platform 已启动。
4. `qc-mcp` 已按官方方式注册在 `~/.claude.json`。
5. 你知道自己要测试的 QC 项目名，并且后面会在 Local Platform 里打开同名项目。

建议先手动检查：

```bash
pwd
bash scripts/opsx.sh list --specs
```

如果 `list --specs` 都跑不通，先不要继续新仓测试。

## 2. 生成新的 TQQQ 策略仓

在模板仓根目录执行：

```bash
bash scripts/new-strategy-repo.sh \
  --project-name tqqq-ema-daily-v1 \
  --target-dir /Users/suyongyuan/strategy-repos \
  --asset TQQQ \
  --resolution daily \
  --git-init
```

预期结果：

- 生成目录：`/Users/suyongyuan/strategy-repos/tqqq-ema-daily-v1`
- 仓内已有这些核心资产：
  - `main.py`
  - `spec.md`
  - `results/`
  - `openspec/`
  - `.claude/`
  - `scripts/`
  - `workflow/`

## 3. 进入新仓并做 bootstrap 检查

进入新仓：

```bash
cd /Users/suyongyuan/strategy-repos/tqqq-ema-daily-v1
```

执行 bootstrap：

```bash
bash scripts/bootstrap-python-env.sh --with-openspec
```

然后检查：

```bash
bash scripts/check-qc-mcp.sh
bash scripts/opsx.sh list --specs
ls
ls results
```

这一阶段你要确认：

1. `.venv` 创建成功。
2. repo-local OpenSpec CLI 安装成功。
3. `check-qc-mcp.sh` 返回 OK。
4. `openspec` 能列出长期 specs。
5. `results/` 目录已存在。

如果这里失败，不要进入 propose。

## 4. 在 Claude 里跑 propose

在新仓里启动 Claude：

```bash
claude
```

建议直接用这条：

```text
/opsx.propose 为当前仓库创建一个新的 qc-change，目标是研发一个 TQQQ daily EMA crossover 策略。请按本仓 OpenSpec contract 生成 proposal、specs、research、design、tasks。
```

建议 change id：

- `ema-crossover-v1`

propose 完成后，你要额外检查这些命令：

```bash
bash scripts/opsx.sh show ema-crossover-v1
bash scripts/opsx.sh validate ema-crossover-v1
find openspec/changes/ema-crossover-v1 -maxdepth 3 -type f | sort
```

这一阶段你要确认：

1. 生成了 `openspec/changes/ema-crossover-v1/`
2. 里面至少有：
   - `proposal.md`
   - `specs/strategy-project/spec.md`
   - `research.md`
   - `design.md`
   - `tasks.md`
3. `show` 不再报：
   - `Change must have a Why section`
   - `No deltas found`
4. `validate` 退出 0

如果 `validate` 没过，不要继续 apply。

## 5. 跑 apply

在 Claude 里执行：

```text
/opsx.apply ema-crossover-v1
```

apply 跑完后，建议你在 shell 里补查：

```bash
find results -maxdepth 4 -type f | sort
cat results/state.yaml
cat results/report.md
find results/artifacts/runs -maxdepth 2 -type f | sort
bash scripts/check-result-workspace.sh
```

这一阶段你要确认：

1. 代码确实改到了 repo-root `main.py`
2. 如果跑了 backtest，则 run 目录里同时存在：
   - `compile.json`
   - `backtest.json`
   - `run.yaml`
3. `results/state.yaml.status` 只使用这几个值：
   - `not_run`
   - `passed`
   - `failed`
   - `blocked`
   - `needs_iteration`
4. `run.yaml.compile.status` 不应该在 backtest 已执行时仍然是 `not_run`
5. `bash scripts/check-result-workspace.sh` 返回 OK

如果这里结果真源不完整，不要继续 verify。

## 6. 跑 verify

在 Claude 里执行：

```text
/opsx.verify ema-crossover-v1
```

这一阶段重点不是看它“说成功”，而是看它是不是按硬 gate 验收。

你要确认：

1. 它先跑了：

```bash
bash scripts/opsx.sh validate ema-crossover-v1
```

2. 它没有把内部异常吞掉后继续给绿灯。
3. 它检查了：
   - `compile.json`
   - `backtest.json`
   - `run.yaml`
   - `results/state.yaml`
   - `results/report.md`
   - `bash scripts/check-result-workspace.sh`
4. 它是按当前 `proposal.md` 动态核对 success criteria，不是写死数字。
5. 如果结果真源缺 compile 证据，verify 应该失败，而不是继续说 ready to archive。

如果 verify 失败，先修 blocker，不要 archive。

## 7. 跑 archive

只有 verify 全绿时，才执行：

```text
/opsx.archive ema-crossover-v1
```

你要确认：

1. archive 前重新跑了：

```bash
bash scripts/opsx.sh validate ema-crossover-v1
bash scripts/check-result-workspace.sh
```

2. 如果 validate 或 result workspace 失败，它应该阻塞 archive，而不是强行收口。

## 8. 这次测试的关键观察点

这次不是普通策略测试，重点是验证修复后的链路有没有真正生效。

优先观察这些点：

1. `propose` 是否真的生成了 `specs/`，而不是只写 `proposal/research/design/tasks`
2. `proposal.md` 是否包含 `Why`
3. `openspec validate <change>` 是否首次通过
4. `apply` 是否先落 `compile.json`，再落 `backtest.json`
5. `results/state.yaml` 是否只用 canonical status
6. `verify` 是否严格 fail-fast
7. `archive` 是否真正依赖 validate 和 result workspace 绿灯

## 9. 推荐记录方式

建议你把这次测试记录成一张表，至少记这些字段：

- 新仓路径
- change id
- propose 是否通过
- validate 是否通过
- apply 是否有 compile/backtest
- `results/state.yaml.status`
- `run.yaml.compile.status`
- verify 是否通过
- archive 是否通过
- 暴露的问题

## 10. 如果你想做最小复测

如果你只想先测最关键的一段，最小闭环是：

1. 生成新仓
2. bootstrap
3. `/opsx.propose`
4. `bash scripts/opsx.sh validate <change>`
5. `/opsx.apply`
6. `bash scripts/check-result-workspace.sh`

这一套过了，再继续跑 verify 和 archive。
