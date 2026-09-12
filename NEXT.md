# NEXT — Klose Learning

更新：2026-09-12。本轮：七项维护整改及 Desktop 导入 / AnkiWeb 同步收尾。

## 当前检查点

七项整改已完成 `IMPLEMENTED / VALIDATED / CHECKPOINTED`。完整 pipeline、内置重复重建和 16 项隔离回归通过；独立身份/来源/历史发布对账通过。逐项前后对比与证据见 [整改记录](docs/MAINTENANCE_20260912.md)。

当前发布数量、allowed/held、LearningOrder、审核分布、artifact SHA-256 和模板指纹统一读取 [current.json](anki/klose/releases/current.json)。历史一次性交易保存在 [releases/history](anki/klose/releases/history/)。

本轮保留全部稳定 ID、来源事实与历史发布记录。重复目标通过 Admission 暂缓新增；题面消歧和例句修正属于 Presentation。模型审校不冒充人工确认。

## 设备与学习状态

本次会话中用户已确认完成以下操作，对应发布 `35b833e58397e5f0f4df36e65e63bbf7aaffe3561f0e68c80de51ce2898bfaad`：

- 导入前已导出 Collection 备份。
- Vocabulary：2,953 条，更新 2,246 条、未变 707 条，无新增或错误提示。
- Expressions：176 条，更新 5 条、未变 171 条，无新增或错误提示。相对设备旧内容的额外 3 条更新未还原字段差异，不将其解释为本轮新增内容修正。
- 五条重复目标 KV001461、KV001481、KV001808、KV002569、KV002636 均仍为 New，已暂停；追加 `-is:suspended` 后搜索结果为零。
- 2,864 张未暂停的 Vocabulary 新卡按 LearningOrder 升序完成 Reposition；Start=1、Step=1、Randomize=OFF、Shift existing=ON。002889 是 LearningOrder 最大值，不是本次新卡数量。
- 已抽查 KV000075 sure 和 KE000147 的更新内容；用户确认旧复习记录仍在。
- 用户确认 Desktop 已同步至 AnkiWeb。本次桌面导入流程已结束。

iPad 未实际确认同步或抽查，不记为已验收；Due/Interval、UserMemo 和模板的完整验收也不由复习记录仍在这一确认推定。[结构化设备凭据](anki/klose/releases/device_receipts.json) 仍为上一版历史记录，本次确认暂记录于本检查点，尚未回填该文件。

学习试点状态仍为 `awaiting-observation`；没有记录实际学习周、学习效果或成绩。填写方式见 [学习反馈](docs/LEARNING_FEEDBACK.md)。

## 下一步

1. 将本检查点已确认的 Desktop / AnkiWeb 结果回填结构化设备凭据，保留历史，并明确 iPad 未验收。
2. 待用户实际确认 iPad 同步与抽查后补记设备验收；不重复要求 Desktop 导入。
3. 从首个有记录的学习周开始收集反馈，再据证据调整每日新增、例句支撑或准入。

本轮代码整改无未完成项。后续代码任务使用 [统一变更流程](docs/CHANGE_WORKFLOW.md)。本次整改前的完整 NEXT 已归档至 [历史检查点](docs/archive/checkpoints/2026-09-12-before-maintenance/NEXT.md)。
