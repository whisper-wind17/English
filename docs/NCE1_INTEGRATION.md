# NCE1 Integration — Klose Learning

状态：全册906条来源已完成显式义项映射，889个学习目标；新增续批230个身份并完成模型内容审校。最终发布须通过完整门禁并随验证事务提交；设备导入状态独立。全册记录见 [NCE1_FULL_BOOK_RELEASE.md](NCE1_FULL_BOOK_RELEASE.md)。

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

## Phase B / Batch 001

首批来源范围：CurriculumOrder 0001–0150，150条实物照片记录。显式义项决策保存在 `anki/klose/nce1/identity_decisions/batch_001.csv`，绑定SourceFingerprint与IdentityFingerprint。41条新增身份KV003016–KV003056；109条复用，其中Mr.复用Mr，11组同拼写不同学习目标明确分开。

已有Japanese和clean的展示原本混写两义，但例句分别只教授日语和打扫。本批保留Stable Identity和历史Source Fact，明确将原展示收窄至原例句目标，再以新ID教授来源中的形容词义；没有删除旧卡。too原有也义例句不符，按原ID修正并重新审校。

52条变化呈现有显式模型审核凭据，新Note的LearnerLevel仍为4，不把新概念课次或教材来源当作Source Grade。6个旧held词汇准入，其他held目标不变。总发布由2953增至2995；新增41个身份及1个已存在库存身份Danish。实际设备新增数量须以其已有ID为准。

共享发布课程推导已同步支持NCE1；历史第三方计划保留为冻结交易审计输入，当前顺序独立重算。同一目标在第三方和NCE1均出现时只使用更早NCE1位置；四年级出现者仍保留更早四年级位置。第三方来源限制仅放行具有本批明确指纹凭据的真实教材映射，不按SourceID字符串无限放行。

`apply_nce1_reviewed_batch.py`是一次性显式事务工具，不在日常pipeline中运行。身份/来源/发布注册表仅追加，复跑遇到preimage变化拒绝；审核凭据由已完成的模型审校封存，远端只校验当前内容hash后应用，不自动生成审批。

校验包括完整pipeline、确定性重建、既有回归、新增反向状态测试、独立旧ID/旧展示/四年级前缀/旧暂停集合/Expressions及模板字节对账。报告在 `anki/klose/review/nce1_reconciliation/batch_001_transaction_validation.json`。

[首批导入说明](NCE1_BATCH001_IMPORT.md)。本批已生成导入内容不代表Anki设备已更新。全册剩余756条维持待核对，不因首批通过而自动准入。

## 全册续批

本次完成此前756条待核对记录，冻结首批不变。详见 [全册处理与验证](NCE1_FULL_BOOK_RELEASE.md)、[全册导入说明](NCE1_FULL_BOOK_IMPORT.md)。上文“剩余756条”等描述仅记录首批历史检查点，不是当前状态。
