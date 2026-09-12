# NEXT — Klose Learning

更新：2026-09-12。本轮：全面体检后的七项维护整改。

## 当前检查点

七项整改已完成 `IMPLEMENTED / VALIDATED / CHECKPOINTED`。完整 pipeline、内置重复重建和 16 项隔离回归通过；独立身份/来源/历史发布对账通过。逐项前后对比与证据见 [整改记录](docs/MAINTENANCE_20260912.md)。

当前发布数量、allowed/held、LearningOrder、审核分布、artifact SHA-256 和模板指纹统一读取 [current.json](anki/klose/releases/current.json)。历史一次性交易保存在 [releases/history](anki/klose/releases/history/)。

本轮保留全部稳定 ID、来源事实与历史发布记录。重复目标通过 Admission 暂缓新增；题面消歧和例句修正属于 Presentation。模型审校不冒充人工确认。

## 设备与学习状态

[设备凭据](anki/klose/releases/device_receipts.json) 保留上一版 Vocabulary 与 Expressions 的用户导入/同步确认；它们不代表本次内容已更新。当前包等待设备实际导入和同步，repo 不操作 Collection。

学习试点状态为 `awaiting-observation`；没有虚构开始日期、记忆效果或学习成绩。填写方式见 [学习反馈](docs/LEARNING_FEEDBACK.md)。

## 下一步

1. 按 [当前导入 SOP](docs/ANKI_CURRENT_RELEASE_IMPORT.md) 更新两类卡；核对旧 Review History、Due、UserMemo 与稳定 ID。
2. 仅调整仍为 New 的卡的准入和顺序；五条重复目标的 hold 不重置已学习卡。
3. 用户确认 Desktop / iPad 同步后，记录确切 release_id 的设备凭据。
4. 从首个有记录的学习周开始收集反馈，再据证据调整每日新增、例句支撑或准入。

后续代码任务使用 [统一变更流程](docs/CHANGE_WORKFLOW.md)。本次整改前的完整 NEXT 已归档至 [历史检查点](docs/archive/checkpoints/2026-09-12-before-maintenance/NEXT.md)。
