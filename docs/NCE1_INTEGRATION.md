# NCE1 Integration — Klose Learning

状态：Phase A（Source / reconciliation / curriculum architecture）已完成 `IMPLEMENTED / VALIDATED / CHECKPOINTED`；Stable Identity 分配与 Learner Presentation 属于 Phase B，尚未进入 Anki 发布。

## 目标

把 Klose 实际使用的外研社《新概念英语 1：英语初阶（智慧版）》纳入长期学习系统，目标新卡顺序：

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

已进入 Learning / Review 的 Anki Card 不因该顺序变化重排 FSRS / Due。

## Source truth

实际教材：

```text
SourceID      = new_concept_english_1
SourceEdition = 2022-smart-isbn-9787521336702
ISBN          = 9787521336702
```

Source Reference：

```text
anki/klose/source_reference/new_concept_english_1_staging/
├── vocabulary.csv                 # Lesson 1–17 实物照片转录，150 rows
├── vocabulary-smart-2022.csv      # 当前 reconciliation source，906 occurrence rows
└── source_provenance.json
```

证据优先级仍遵守 `SOURCE_RECONCILIATION.md`：Klose 实物教材 > 同 Edition 官方证据 > 第三方词表。

### 已知 Edition delta

1997 新版在线/历史基线与 Klose 2022 智慧版实物在前段已经确认存在差异：

- `Korean` → 智慧版照片为 `South Korean`；
- 旧版 Lesson 5–6 grouping 中的 `Italian`，智慧版照片出现在 Lesson 7；
- 旧版 `Daewoo`、`Fiat` 不在智慧版 Lesson 6 实物词表。

因此 Lesson 19–144 的在线基线只能标为 `baseline-reconciled`，不能伪装成逐页实物确认。

## Existing source adapter

仓库已有：

```text
8.新概念英语/新概念英语第一册（新版）.xlsx
```

它保留英音、美音和通用词典释义，作为 reconciliation 辅助证据，不覆盖 actual-textbook Source Fact。解析器使用 Python 标准库 `zipfile + ElementTree`，不引入新的 spreadsheet runtime dependency。

## Identity gate

`prepare_klose_nce1_reconciliation.py` 对 906 个 occurrence 生成候选队列：

- exact single surface：仍需确认 target sense；
- multi-sense surface：必须显式选择既有 NoteID 或创建新 sense；
- no exact identity：检查拼写变体/形态后才能分配新 NoteID。

任何字符串匹配都只是 candidate。没有 confirmed mapping 的 NCE1 item 不进入 Learning Admission。

## Curriculum model

课程顺序不再依赖单一 `grade` 数值硬编码，显式配置在：

```text
anki/klose/config/curriculum_segments.json
```

当前 rank：

```text
grade4                = 10
new_concept_english_1 = 20
grade5                = 30
grade6                = 40
third_party            = 90
```

同一 Stable Note 如果在多个来源重复出现，取最早 curriculum coordinate；因此 Grade 4 已学词不会在 NCE1 重复造卡，NCE1 已覆盖的词也不会在 Grade 5/6 再造一张学习卡。

## Phase A validation

验证基线为本次 NCE1 integration PR 的 main base `461780edf86dc266bd40abee0cfc01d41576d8ec`。

已完成：

- `check_klose_nce1_source.py`：906 条 source occurrence、150 条实物 prefix、Edition delta 与 provenance gate；
- `prepare_klose_nce1_reconciliation.py`：生成 sense-aware identity candidate queue，不自动批准；
- `build_klose_learning_admission.py`：课程段 rank 化，并支持 confirmed NCE1 identity 插入 Grade 4 与 Grade 5 之间；
- 合成回归验证同一 NoteID 同时出现在 NCE1 / Grade 5 时只采用更早 NCE1 coordinate；
- 完整 `klose_pipeline.py all` 通过；
- deterministic rebuild：`byte drift=0`；
- 19 项回归测试全部通过。

独立边界检查确认：Phase A 没有分配新的 Stable NoteID，没有把 NCE1 写入当前 Learning Admission，没有改变现有正式 Vocabulary / Expressions release，也没有改写任何 Anki FSRS / Review History。

## Phase B completion gate

NCE1 真正进入正式 Anki 发布前仍需完成：

1. 906 occurrence 的 sense-aware identity decisions；
2. 真正新 learning units 追加 Stable NoteID；
3. Source Identity / occurrence provenance 写入 durable master；
4. 新 Note 的 LearnerLevel 4 Meaning / IPA / Example / Translation；
5. explicit learner review receipts；
6. Learning Admission 重建，确认 NCE1 位于 Grade 4 与 Grade 5 之间；
7. 完整 `klose_pipeline.py all`、回归和反向检查；
8. 只对仍为 New 的 Anki cards 按新 LearningOrder Reposition。

当前 checkpoint 明确停在 Phase A：Source 已正式纳入系统治理，Learning Object 尚未发布。
