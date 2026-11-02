# NCE1 首批发布后的历史 workflow 恢复

## 已核实的事件

NCE1 首批发布在 `cd4bee9e9f3337569ecbf940c8b6d13c32ff3d69` 合入 main；其完整 pipeline、26 项回归、独立事务对账均通过。发布文件 SHA-256 为 `1a31b649e0266a7bca7e4d073956170726b85e98220886a7e21bd9e6b94ac6b8`。

该次新增合法 NoteID 同时触发了仍留在 `.github/workflows/` 的旧 Grade 5–6 / Third-party 一次性摄取任务。三个 github-actions[bot] 提交将 main 推进到 `88bfe2a7ad331a6fdd77175c07394291871ac0fc`，重建旧候选并使历史复核决策退出队列。两提交边界的 diff 仅包含下述10个历史 review/premerge 文件；Stable NoteID、学习呈现、发布和设备状态没有被这些 bot 提交改写。

主发布 workflow 在自己的检出提交上再次通过完整构建、26项回归与重复构建，但最后的持久化因 `Remote main changed after checkout` 正确拒绝了覆盖。没有移除这项并发保护，也没有 force push。

## 精确恢复范围

将以下10个文件恢复为已通过首批验证的 `cd4bee9e` 中的原始 blob；其余 NCE1 数据、身份、审核和发布内容保留：

- `anki/klose/review/grade5_6_reconciliation/vocabulary_candidates.csv`
- `anki/klose/review/grade5_6_reconciliation/vocabulary_decisions.csv`
- `anki/klose/review/grade5_6_reconciliation/vocabulary_next_batch.csv`
- `anki/klose/review/grade5_6_reconciliation/vocabulary_status.json`
- `anki/klose/third_party_vocabulary/premerge/identity_candidates.csv`
- `anki/klose/third_party_vocabulary/premerge/readiness.json`
- `anki/klose/third_party_vocabulary/premerge/reconciliation_next_batch.json`
- `anki/klose/third_party_vocabulary/premerge/reconciliation_review_queue.csv`
- `anki/klose/third_party_vocabulary/premerge/reconciliation_selected_view.csv`
- `anki/klose/third_party_vocabulary/reconciliation/reconciliation_decisions.csv`

## 生命周期修正

以下五项已完成交易的 workflow 原始 YAML 按 blob 原样归档至 `docs/archive/workflows/nce1-20261102/`，不再作为日常 push/workflow_run 任务执行：

- Grade 5–6 vocabulary reconciliation；
- Third-party Stage-B premerge readiness；
- Third-party Stage-B identity reconciliation；
- Third-party allocation plan validation（其旧检查要求全仓永远等于历史 allocation commit）；
- Grade 5–6 premerge dedup audit（其旧生成器要求历史901个 pre-existing identities）。

这是执行 AGENTS 中“一次性历史交易不能锁死日常合法状态变化”的规则。历史脚本、计划、决策、审批、快照和 workflow 原文均未删除；如确需重放，必须在冻结边界和隔离工作区显式进行，不能重新挂到当前 main 的新增词汇事件。

当前统一 pipeline、Stable ID/审批/发布历史保护、Grade 5–6 已审核闭合检查、当前 Third-party release contract、内容审核门禁、确定性构建和回归步骤均保留。增加两项回归，检查旧任务不得被意外重新启用、当前发布门禁必须继续存在。

## 验证边界

恢复提交须通过完整 `klose_pipeline.py all`、28项回归及 PR 检查才合入。恢复后正式导入文件应仍逐字节等于 `cd4bee9e` 的已验证文件；此修复不新增/删除卡片、不改变首批150条处理结果，也不意味着其余756条已完成。
