# NEXT — Klose Learning

更新：2026-11-01。本轮：New Concept English 1 Source / Reconciliation / Curriculum 接入。

## 当前检查点

NCE1 接入 Phase A 已完成 `IMPLEMENTED / VALIDATED / CHECKPOINTED`，任务文档见 [NCE1 Integration](docs/NCE1_INTEGRATION.md)。

Klose 实际教材已锁定为外研社《新概念英语 1：英语初阶（智慧版）》，`SourceID=new_concept_english_1`，`SourceEdition=2022-smart-isbn-9787521336702`，ISBN `9787521336702`。当前 source reference 共 906 条 occurrence：

- Lesson 1–17：150 条来自 Klose 实物教材照片，`verified-actual`；
- Lesson 19–144：756 条基于仓库既有《新概念英语第一册（新版）》数据、旧新版顺序基线、外研社版本说明及抽样核验，显式标记 `baseline-reconciled`；
- 已知 `South Korean / Italian / Daewoo / Fiat` 等 Edition delta 已单独记录，不把旧版数据冒充智慧版逐页实物事实。

NCE1 source/reconciliation gate 已进入统一 pipeline。课程段顺序已经显式建模为：

```text
Grade 4 Upper
→ Grade 4 Lower
→ New Concept English 1
→ Grade 5 Upper
→ Grade 5 Lower
→ Grade 6 Upper
→ Grade 6 Lower
→ Third-party vocabulary
```

同一 Stable Note 在多个来源重复出现时取最早 curriculum coordinate；已进入 Anki Learning/Review 的卡不因新顺序改写 FSRS / Due。

Phase A 验证证据：完整 `klose_pipeline.py all` 通过；内置重复重建 `byte drift=0`；19 项回归通过；新增测试验证 NCE1 必须位于 Grade 4 与 Grade 5 之间，并验证 NCE1 与 Grade 5 重复 NoteID 只保留更早 curriculum position。

当前正式 Vocabulary / Expressions 发布内容和设备学习状态没有因 Phase A 改变。当前发布数量、allowed/held、LearningOrder、审核分布、artifact SHA-256 和模板指纹仍统一读取 [current.json](anki/klose/releases/current.json)。

## NCE1 尚未完成的学习层工作

906 条 Source occurrence 不能直接等同于 906 张卡。下一阶段必须完成 sense-aware identity reconciliation：

1. 对 exact-single / multi-sense / new-candidate 逐项确认 target sense；
2. 相同 learning unit 复用 Stable NoteID；真正新义项才 append 新 NoteID；
3. 区分 Vocabulary 与可迁移 Expression，不把教材 `New words and expressions` 机械一行一张 Vocabulary Card；
4. 建立 durable Source Identity / occurrence provenance；
5. 新 Note 生成 LearnerLevel=4 的 Meaning / IPA / Example / Translation，并走显式 review；
6. 只有 confirmed identity + review 通过的 NCE1 learning units 才进入 Admission / Release；
7. 正式发布后，只对仍为 New 的 Anki Cards 按新 LearningOrder Reposition。

在这些 gate 完成前，不把 NCE1 解释为已经进入当前 Anki 学习队列。

## 设备与学习状态

上一正式发布对应 release `35b833e58397e5f0f4df36e65e63bbf7aaffe3561f0e68c80de51ce2898bfaad`：

- Vocabulary：2,953 条；用户已确认 Desktop 导入并同步 AnkiWeb。
- Expressions：176 条；用户已确认 Desktop 导入并同步 AnkiWeb。
- 五条重复目标 KV001461、KV001481、KV001808、KV002569、KV002636 仍按 Admission held / New 卡暂停。
- 2,864 张未暂停 Vocabulary New Cards 已按当时 LearningOrder 完成 Reposition。
- iPad 未实际确认同步或抽查，不记为已验收。
- 学习试点仍为 `awaiting-observation`，没有记录实际学习周、学习效果或成绩。

## 下一步

优先完成 NCE1 identity reconciliation 与 Learner Presentation / Review，达到正式 Learning Admission / Release gate 后再生成新的 Anki 导入包和 New-card Reposition 范围。设备历史确认与学习反馈继续按既有 SOP 保留，不重复执行旧版全量迁移。
