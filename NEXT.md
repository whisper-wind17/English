# NEXT — Klose Learning

Last updated: 2026-09-05

新对话启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/SOURCE_RECONCILIATION.md
→ anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md
```

## Current objective

先修复 **Klose 实际四年级上教材与当前第三方 `rj_start1::4年级上` 的版本冲突**，再接收四年级下实际教材，之后才继续 Grade 5/6 扩展。

核心不变量：

```text
Source Grade ≠ LearnerLevel
```

Klose 当前仍使用 `LearnerLevel=4`；未来学习 Grade 5/6 来源词汇也不自动提升 LearnerLevel。

## Critical blocker

当前 repo 第三方四上 source 从 `running / basketball / roller skating / ...` 开始，主题包含运动、交通、文具、安全等；Klose 手中实际四上 6 Units 则为：

1. jobs / chores
2. personal traits
3. places / community
4. jobs
5. weather
6. clothes / seasons

这是 **Source Edition / Revision mismatch**，不是少量漏词。

当前专项诊断：

```text
anki/klose/source_reference/rj_start1-grade4-upper-reconciliation.md
```

状态：**BLOCKED FOR SOURCE RECONCILIATION**。

## 已采集的 Klose 实际四上资料

Core Vocabulary：

```text
anki/klose/source_reference/rj_start1-grade4-upper-klose-actual.csv
6 Units
110 occurrence rows
109 unique surface entries
```

Useful Expressions：

```text
anki/klose/source_reference/rj_start1-grade4-upper-klose-expressions.csv
41 raw textbook expression rows
```

Pattern Candidates：

```text
anki/klose/source_reference/rj_start1-grade4-upper-pattern-candidates.csv
```

规则：Vocabulary 与 Expressions 分离。Useful Expressions 原文是 Source Fact，但不机械做到“一句 = 一张卡”。详细见 `docs/EXPRESSIONS_SYSTEM.md`。

## Identity blocker: cook

Klose 实际教材：

```text
Unit 1 cook = 烹饪；煮  # verb
Unit 4 cook = 厨师      # noun
```

当前 released `KV000424` 把两个 sense 合并为 `厨师；做饭`，违反一个 Note = 一个 target sense。

预期 migration：

```text
保留 KV000424 -> cook noun / 厨师
append 新 NoteID -> cook verb / 烹饪；煮
```

不得重编号旧 NoteID。

## Current Anki state

第一次 Desktop 导入与 AnkiWeb Upload 已完成，历史结果：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Cards             = 518
Suspended         = 343
Unsuspended       = 175
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

Card contract：Front 只显示 Word；Back 含 `{{tts en_US:Word}}`、UK/US IPA、Meaning、Example、Translation；例句暂不自动 TTS。

### Temporary safety rule

**不要让 Klose 开始正式学习。**

当前 175 active cards 的 staging 基于版本不匹配的旧四上 source。Klose 尚未产生真实 Review History，现在是修复 Source / Identity / staging 成本最低的窗口。

禁止：

```text
删除/重编号已有 NoteID
手工修改 study.csv / anki-import.csv
让错误 staging 先形成 FSRS history
```

## Next work order

1. 按 `docs/SOURCE_RECONCILIATION.md` 完成四上三方核对：actual textbook vs source occurrences vs Master/Identity。
2. 110 条 Core Vocabulary occurrence 全部得到明确 identity decision：
   - 同一 sense -> 复用 NoteID + 补 actual-textbook provenance；
   - 其他年级已有 -> 复用 NoteID + 新增四上 occurrence；
   - phrase/morphology candidate -> sense-aware review；
   - 新 learning unit -> append NoteID；
   - same surface/different sense -> split migration。
3. 明确当前第三方数据是否属于另一 Edition；不能直接覆盖原 XLSX。
4. 完成 `cook` noun/verb migration。
5. 保持 `LearnerLevel=4`，重新审校新增/变化的 Meaning / Example / Translation。
6. rebuild staging、review registry、approval、release gate，生成纠正后的 `anki-import.csv`。
7. 用同一 Note Type 原地更新 Anki，保护 NoteID 和未来 FSRS history。
8. 四上稳定后，接收用户提供的四年级下 Core Vocabulary + Useful Expressions，沿用 `source_reference` 结构。
9. 四上下实际 Edition 建立完成后，再处理 Grade 5/6；仍按当前 LearnerLevel=4 准备。

## Grade 4 upper Definition of Done

- [ ] 110 条实际 Core Vocabulary occurrence 均有明确 identity decision
- [ ] existing same-sense Notes 复用稳定 NoteID并补正确 provenance
- [ ] phrase/morphology candidates 均做 sense-aware decision
- [ ] genuine new learning units append NoteID
- [ ] `cook` noun/verb split 完成
- [ ] Source Edition / Revision 不再混淆
- [ ] LearnerLevel 保持 4
- [ ] changed/new learner content review + fingerprint current
- [ ] corrected staging 重建完成
- [ ] release readiness gate 通过
- [ ] corrected `anki-import.csv` 生成并可安全原地更新 Anki
- [ ] blocker 解除后 Klose 才开始正式学习

## Relevant docs

```text
docs/KLOSE_VOCABULARY_SYSTEM.md
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
docs/LEARNER_REVIEW_REGISTRY.md
docs/ANKI_FIRST_IMPORT.md
docs/ANKI_FIRST_IMPORT_GUIDE.md
docs/ANKI_SYNC_WORKFLOW.md
anki/klose/source_reference/README.md
```

第一次 Anki setup 已完成，新对话不要重复配置；当前优先级是 **source reconciliation before study**。
