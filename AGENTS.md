# AGENTS.md

## 1. Project Mission

本仓库除保存原始英语词库外，还维护一个长期演进的 **Klose Vocabulary System**。

目标不是生成一次性 Anki 牌组，而是长期维护：

- 多教材/阅读来源统一的 Vocabulary Knowledge Base；
- 稳定且不可重分配的 Vocabulary Identity / NoteID；
- 可随 Klose 能力升级的 Learner Presentation；
- 与 Anki FSRS / Review History 向后兼容的发布数据。

完整机制见：`docs/KLOSE_VOCABULARY_SYSTEM.md`。Anki 一次性迁移见：`docs/ANKI_MIGRATION.md`。

---

## 2. Non-negotiable Rules

1. **Stable NoteID 是最高优先级不变量。** 已分配 NoteID 不得因排序、重建、教材增加、释义修改而重新编号、复用或漂移。
2. **NoteID 必须来自持久化 Registry，不得每次从 Master 排序重新生成。**
3. **一个 Note 表示一个明确的 learning unit / target sense，而不是简单表示一个字符串。** 同形异义词不得因 `CanonicalWord` 相同而静默合并。
4. **CanonicalWord / MatchKey 只用于候选匹配，不是业务主键。** 存在词性、义项、大小写或短语边界歧义时进入 review。
5. **同一个已学 learning unit 不创建第二套 FSRS 记忆状态。** 新来源出现相同 target sense 时扩展 Source/Provenance。
6. **FirstGrade 与 LearnerLevel 分离。** FirstGrade 是来源事实；LearnerLevel 决定当前学习呈现。
7. **学习范围必须按 source-scoped occurrence 判断。** 不得用全局 `FirstGrade` 推导“当前允许学习哪些词”。
8. **原始 Source 保留且可追溯。** 不覆盖原始 XLSX/来源文件来修复生成结果。
9. **生成文件不可作为长期手工维护入口。** 修改 source / identity registry / curation / learner config 后重新构建。
10. **任何 identity merge/split 都是高风险迁移。** 在评估已有 Anki history 前不得直接改 NoteID 映射。
11. **不得把自动检查通过表述成“人工老师逐词确认”。** 明确区分规则检查、模型审校、人工确认、教材原文核对。
12. **任何架构优化优先保护已有 Anki Review History / FSRS state。**
13. **不要无质疑接受需求假设。** 发现 Anki 行为、数据模型或学习机制前提错误时先指出并验证。

---

## 3. Source of Truth

### 内容侧

```text
Raw Source
    ↓
Normalize / Source Adapter
    ↓
Identity Registry + Source Occurrences
    ↓
Vocabulary Master
    ↓
Learner Layer
    ↓
Publish
```

- Raw Source：教材/词书原始文件，负责 provenance。
- Identity Registry：NoteID 与 learning unit 的长期身份真源；是**持久化状态**，不是普通生成物。
- Source Occurrences：每个 Note 在每个来源/册次/Unit/行号的出现记录。
- Vocabulary Master：跨来源事实汇总。
- Learner Layer：当前 LearnerLevel 对应的例句等呈现。
- Publish：可重建的 Anki 输入。

### 学习侧

Anki 是以下状态的唯一真源：

- Review History / FSRS memory state
- Due / Interval
- New / Learning / Review / Suspended
- Card-level scheduling

repo 不重建这些状态。

---

## 4. Current Data Areas

当前首批来源：

```text
anki/人教版一年级起点/          # source-specific staging / curation
```

长期统一层：

```text
anki/klose/
├── config/                    # learner/scope configuration
├── master/                    # registry + global master + occurrences
├── learner/                   # Klose 当前 presentation layer
├── publish/                   # Anki 发布文件
└── review/                    # identity / semantic / learner review queues
```

原始教材文件仍位于：

```text
1.全国各大教材版本中小学同步/人教版/
```

---

## 5. Build Entry Points

Source-specific：

```text
tools/build_anki_rj_start1.py
tools/check_anki_example_vocab.py
tools/export_anki_review_input.py
```

Global Klose Vocabulary：

```text
tools/build_klose_vocabulary.py
```

CI：

```text
.github/workflows/build-anki-rj-start1.yml
.github/workflows/build-klose-vocabulary.yml
```

修改数据/规则后，必须保证相关构建和 CI 成功，并检查 review queue 与全量统计。

---

## 6. Identity Model

长期至少区分：

```text
NoteID              # 永久业务主键
CanonicalWord       # 标准显示/规范词形
MatchKey            # 仅用于候选匹配的规范化 key
SenseLabel          # target sense 的可读锚点
```

规则：

- `NoteID` 永久稳定。
- `CanonicalWord` / `MatchKey` 变化不应自动触发 NoteID 变化。
- 固定短语是独立 learning unit。
- 同形异义（如未来出现不同义项）允许多个 NoteID。
- 新来源匹配已有 Note 时，必须同时考虑词形、词性/义项和学习目标；不能只比较字符串。
- 模糊匹配只能产生 review candidate，不得自动 merge。

---

## 7. Source / Scope Model

Source provenance 必须保持来源作用域，例如：

```text
source::rj_start1::grade::4::上
source::beijing::grade::3::下
source::newconcept::book::1
```

`FirstSource` / `FirstGrade` 只作为便利汇总字段，**不能**用于判断当前学习资格。

当前学习资格由 learner config 的 source-scoped rule 决定；已释放进入 Anki 的 Note 应继续获得后续内容更新。

---

## 8. Learner Model

```text
LearnerProfile
LearnerLevel
ExampleSentence
ExampleTranslation
PresentationStatus
```

核心原则：

> `FirstGrade` 描述“教材什么时候教”；`LearnerLevel` 描述“Klose 今天怎么学”。

升年级更新例句时不得修改 NoteID、Source occurrences 或 Anki scheduling。

简单句并非自动不合格；判断标准是自然、目标义项清晰、对当前 LearnerLevel 有效，而不是机械增加复杂度。

---

## 9. Publish / Anki Contract

长期 Note Type：`Klose Vocabulary`。

稳定发布字段至少包含：

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
Tags
```

规则：

- `NoteID` 必须是 Note Type 第一字段。
- 重新导入必须使用同一 Note Type，并选择 Update Existing Notes。
- Duplicate match scope 使用 Note Type，不依赖 Deck。
- repo 生成的 Tags 视为 system-managed；不要在这些 Notes 上手工维护需要永久保留的自定义 Tags。
- 如需本地个人备注，使用不参与 CSV 映射的 Anki 本地字段（例如 `UserMemo`）或 Card Flag。

默认发布入口：

```text
publish/study.csv   # 推荐日常导入：已释放/当前学习范围
publish/all.csv     # 完整库存，不是默认日常导入入口
```

原因：新增一个尚未开放的教材时，直接导入 `all.csv` 会把其新 Note 作为普通 New Cards 加入 Anki；`study.csv` 避免这种意外释放。

---

## 10. Change Workflow

### 新增教材/词书

1. 保留 Raw Source。
2. 解析为 source-scoped occurrences。
3. 生成 identity candidates。
4. 与 Registry 做 sense-aware matching。
5. 明确已有 unit → 绑定原 NoteID、扩展 provenance。
6. 明确新 unit → 追加新 NoteID；不得重排旧 ID。
7. 模糊项 → review，阻止静默合并。
8. 更新 Learner Layer。
9. 根据 learner scope 决定哪些新 Note 可进入 `study.csv`。
10. 重建并运行 CI。

### 升级 Learner Level

1. NoteID / identity / source facts 不变。
2. 更新 LearnerLevel 与 presentation。
3. 运行 learner quality checks。
4. 重建 `study.csv`。
5. Anki Update Existing Notes；保留 scheduling。

### Identity merge/split

必须单独设计 migration；不得作为普通“数据清洗”直接执行。

---

## 11. Quality Gates

至少检查：

### Identity
- NoteID 唯一且 Registry 稳定；
- Registry 不因排序重建；
- canonical collision / case collision / homograph candidate；
- publish 不出现重复 NoteID。

### Provenance
- 每条 Master 至少一个 Source；
- 每个 source occurrence 可追溯至原文件/册次/行号（有数据时包括 Unit）；
- source-scoped grade/level 不被全局 grade 覆盖。

### Learner
- LearnerLevel / MeaningPrimary / Example / Translation 完整；
- 目标义项清晰、句子自然；
- 难度按 LearnerLevel 判断，不机械跟随 FirstGrade；
- 语义无法自动保证的内容进入 review，不用 `0 issues` 冒充“语义完全正确”。

### Publish
- `study.csv ⊆ all.csv`；
- by-source/by-grade 文件仅为视图；
- deterministic build；
- 不静默 fallback 到未经审校的成人词典首义。

---

## 12. Working Style

- 开始任务先读取 `AGENTS.md` 与相关 docs，再检查 repo 当前状态。
- 先判断变更属于 Source / Identity / Fact / Learner / Publish / Anki Migration 哪一层。
- 大批量处理前先验证样本与边界案例。
- 修改后 re-check 代表性词、统计、review queue、CI。
- 能通过脚本/CI 固化的规则，不只写在 Prompt/文档里。
- `AGENTS.md` 只维护规则和能力地图；详细机制放 `docs/`。