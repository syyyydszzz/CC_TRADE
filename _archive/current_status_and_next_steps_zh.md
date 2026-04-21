# 当前状态与下一步

## 当前状态

当前仓库已经完成这几个切换：

- `.buildforce/` 已删除
- `OpenSpec` 成为唯一 planning authority
- `/opsx:*` 成为默认 workflow 入口
- `scripts/*` 成为唯一 repo helper 入口
- `results/` 保持为策略结果真源
- `Achieve` 仅保留为可选薄 loop 兼容层

## 下一步

1. 安装 Node `20.19+`
2. 运行 `bash scripts/bootstrap-openspec.sh`
3. 在 Claude Code 里用 `/opsx:propose` 做一次真实 smoke test
4. 如需 loop，再启用 `bash scripts/opsx-session-start.sh --change-id <change-id>`

## 说明

本文件不再记录旧 BuildForce session 状态；那套状态层已经被移除。
