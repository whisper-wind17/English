# Klose Vocabulary System

> 本文定义 Klose 长期英语词汇学习系统的核心架构。动态状态、blocker 和下一步不写死在本文，统一读取根目录 `NEXT.md`。

相关 SOP：

```text
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
docs/LEARNER_REVIEW_REGISTRY.md
docs/ANKI_FIRST_IMPORT.md
docs/ANKI_SYNC_WORKFLOW.md
docs/ANKI_MIGRATION.md
```

## 1. 五个必须分离的维度

### 1.1 Source Fact

描述教材事实：

```text
SourceID
SourceEdition / Revision
SourceBook
Grade
Semester
Unit
Raw Entry / Meaning / Position
```

`Source Grade` 只回答“教材在哪里出现”。

当前部分物理 schema 尚未显式包含 Edition 字段；一旦发现版本冲突，应先完成 Source Edition 建模，再继续 merge provenance，不能把不同版本静默混入同一 `SourceBook`。

### 1.2 Vocabulary Identity

描述长期 learning unit：

```text
NoteID
CanonicalWord
MatchKey
SenseLabel
```

一个 Note 对应一个明确 target sense，不等于一个字符串。

### 1.3 Learner Presentation

描述 Klose 今天怎么学：

```text
LearnerProfile
LearnerLevel
MeaningPrimary
ExampleSentence
ExampleTranslation
```

核心原则：

```text
Source Grade ≠ LearnerLevel
```

Klose 完全可以在 `LearnerLevel=4` 下学习 Grade 5 / Grade 6 来源词汇。学习更高年级 source 不要求同步提升 LearnerLevel。

### 1.4 Learning Object Type

至少区分：

```text
Vocabulary
Expressions / Patterns
```

Vocabulary 是 word / phrase / target sense；Expression 是 communicative pattern / reusable structure。二者不共享同一 Note 语义。

### 1.5 Release / Scheduling State

GitHub 管发布；Anki 管记忆状态。

```text
GitHub: Source / Identity / Learner / Review / Release
Anki:   FSRS / Review History / Due / Interval / Card State
```

repo 不重建 Anki scheduling；Anki 也不是词汇事实真源。

---

## 2. 数据流

```text
Raw Source / Actual Textbook Reference
→ Source Adapter / Reconciliation / Curation
→ Identity Registry + Source Identity Map + Source Occurrences
→ Vocabulary Master
→ Learner Presentation
→ Learner Review Registry
→ Release Registry
→ study.csv            # generated internal snapshot
→ anki-import.csv      # generated formal Anki artifact
→ Release Gate
→ Anki
```

长期数据区：

```text
anki/klose/
├── config/
├── master/
├── learner/
├── source_reference/
├── anki/
├── publish/
└── review/
```

---

## 3. Source Truth 与教材版本

现有第三方 XLSX 只是 Source Adapter 输入，不自动等于 Klose 实际教材。

当 Klose 手中教材与 repo 数据冲突时：

```text
实际教材照片/扫描件
→ source_reference capture
→ Edition / Revision 判断
→ actual vs source occurrences vs Master/Identity 三方 reconciliation
→ 修正上游
```

不要直接覆盖第三方原始 XLSX，也不要把两个 Edition 误当成同一个 Source Fact 集合。

详细 SOP：`docs/SOURCE_RECONCILIATION.md`。

---

## 4. Stable NoteID 与 Identity

NoteID 是长期业务主键：

```text
KV000001
KV000002
...
```

新增 learning unit：

```text
读取 committed Registry
→ 确认真正新 unit
→ append next NoteID
```

禁止根据 Master 当前排序重新 enumerate。

匹配规则：

1. `MatchKey` 只产生 candidate；
2. 相同 surface + 相同 target sense 通常可复用 NoteID；
3. 固定短语可以是独立 learning unit；
4. 相同 surface 但词性/核心义项不同，可以有多个 NoteID；
5. 大小写、词形、短语边界存在语义差异时必须 review；
6. substring / morphology 不能作为自动 merge 依据。

例如：

```text
worker        ≠ office worker
football      ≠ play football
fly           ≠ fly a kite
cook(noun)    ≠ cook(verb)
```

Identity split / merge 属于 migration，不是普通清洗。

---

## 5. Source Occurrence / Provenance

每次教材出现独立记录。逻辑上至少需要：

```text
NoteID
SourceID
SourceEdition / Revision
SourceBook
Grade
Semester
Unit
SourceWord
SourceFile / Page / Row
```

同一 Note 可以出现在多个来源、多个年级、多个版本；新增 occurrence 不覆盖旧事实。

`FirstGrade` 只能作为便利汇总字段，不能作为学习资格或 LearnerLevel 的依据。

---

## 6. Learner Presentation 与 Review

Learner Presentation：

```text
LearnerProfile
LearnerLevel
NoteID
MeaningPrimary
ExampleSentence
ExampleTranslation
PresentationStatus
```

例句要求：自然、目标义项清晰、难度低于当前阅读上限，不机械追求复杂。

Review 唯一键：

```text
LearnerProfile + LearnerLevel + NoteID
```

`ContentFingerprint` 至少绑定：

```text
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
```

受审内容变化后，旧 approval 必须失效为 `pending`。详细机制见 `docs/LEARNER_REVIEW_REGISTRY.md`。

升 LearnerLevel 时，只升级 presentation；Source Fact、NoteID 和 Anki Review History 不变。

---

## 7. Vocabulary 与 Expressions

### Vocabulary

```text
word / phrase / target sense
```

长期 Note Type：

```text
Klose Vocabulary
```

### Expressions

教材 Useful Expressions 先完整保存为 Source Fact：

```text
Raw Expression
→ Pattern Candidate
→ optional Released Expression
```

禁止“一条教材原句 = 一张 Anki Card”。只有高频、可迁移、适合当前 LearnerLevel 的 pattern 才可能进入正式 Expressions 学习系统。

Expression 中出现但未列入 Core Vocabulary 的词属于 Context Vocabulary 证据，可用于例句难度和教材暴露范围判断，但不能自动 release 成 Vocabulary Note。

详细设计见 `docs/EXPRESSIONS_SYSTEM.md`。

---

## 8. Inventory / Released Set / Anki Import

### `all.csv`

```text
anki/klose/publish/all.csv
```

完整 Vocabulary inventory，用于审计，不是默认导入入口。

### `study.csv`

```text
anki/klose/publish/study.csv
```

Generated Released Set 内部标准快照，用于构建、审计、diff，不直接导入 Anki。

### `anki-import.csv`

```text
anki/klose/publish/anki-import.csv
```

唯一正式 Anki 发布文件。数据必须与 `study.csv` 一致，使用 Anki file headers，UTF-8 无 BOM，第一数据字段为 `NoteID`。

严禁手工修改 `study.csv` 或 `anki-import.csv`。正确链路：

```text
修改上游
→ rebuild
→ review / approval
→ release gate
→ anki-import.csv
→ 原 Note Type Update Existing Notes
```

---

## 9. Anki Contract

主 Deck：

```text
Klose-English::Vocabulary
```

Vocabulary Note Type：

```text
Klose Vocabulary
```

字段：

```text
NoteID
CanonicalWord
Word
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
Sources
SourceBooks
UserMemo
```

只保留一个 Card Type：

```text
Recognition
```

因此：

```text
1 Note = 1 Card
```

当前 Card 逻辑：

```text
Front: Word only
Back: FrontSide + Word TTS + UK/US IPA + Meaning + Example + Translation
```

Card Template / CSS 在 `anki/klose/anki/`。显示变化不改变 NoteID 或 FSRS state。

Suspend 只用于尚未学习的 New Cards 准入控制；一旦进入 Learning/Review，后续 source/stage 变化不能随意重新 Suspend。

---

## 10. Quality Gates

发布前至少验证：

- Registry / Source Identity Map / Release Registry 存在且一致；
- NoteID 唯一稳定；
- Source Edition / provenance 不混淆；
- identity 歧义已显式处理；
- released Notes 的当前 Learner Presentation 完整；
- review status 与 ContentFingerprint current；
- `pending=0`；
- `study.csv` 与 Released Set 一致；
- `anki-import.csv` 与 `study.csv` 数据一致且 headers/encoding 正确；
- staging 分区有效；
- deterministic build；
- CI / release readiness 成功。

执行入口：

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
```

---

## 11. 当前状态与历史 baseline

不要在本架构文档中把某个历史 baseline 永久写成“当前正式状态”。

- 当前 blocker / work order：根目录 `NEXT.md`；
- Klose 实际教材 reconciliation：`anki/klose/source_reference/`；
- 首次 Anki 导入的历史实操记录：`docs/ANKI_FIRST_IMPORT_GUIDE.md`。

过去已经完成的 baseline 和导入结果仍可作为审计历史，但如果后续发现 Source Fact 错误，应按 reconciliation / migration 修正，而不是因为“曾通过旧 release gate”就继续视为当前可学习状态。

详细执行规则以根目录 `AGENTS.md` 为准。
