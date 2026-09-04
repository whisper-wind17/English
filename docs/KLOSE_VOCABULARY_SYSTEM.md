# Klose Vocabulary System

> 本文定义本仓库面向 Klose 的长期英语词汇学习系统。目标不是制作一次性 Anki 牌组，而是建立一个可持续多年扩展、可追溯、可升级、不会破坏既有记忆历史的 Vocabulary Knowledge Base；Anki 只承担 SRS/FSRS 执行与学习状态管理。

## 1. 两条长期演进轴

### 1.1 Vocabulary Expansion

随着学习推进不断接入新来源：

```text
人教版一年级起点
    + 北京版
    + 沪教版
    + 新概念
    + 分级阅读
    + 其他材料
```

规则：已有 learning unit 只扩展 provenance；真正的新 learning unit 才获得新的 NoteID。

### 1.2 Learner Presentation Evolution

随着 Klose 能力提升：

```text
Grade 4 presentation
    ↓
Grade 5 presentation
    ↓
Grade 6 presentation
```

升级的是例句、解释方式、必要时的提示，不是 Vocabulary Identity，也不是 Anki Review History。

---

## 2. GitHub 与 Anki 的职责边界

### GitHub Repository：内容与身份真源

负责：

- learning unit 的长期 NoteID；
- 标准词形、目标义项、音标和核心释义；
- 来源教材、册次、年级、Unit、原始行号等 provenance；
- 当前 LearnerLevel 的例句与译文；
- review queue 与质量检查；
- 可重复生成的 Anki 发布 CSV。

### Anki：学习状态真源

负责：

- Review History；
- FSRS memory state；
- Due / Interval；
- New / Learning / Review / Suspended；
- Card-level scheduling。

GitHub 不重建 Anki scheduling；Anki 也不作为词汇事实数据的唯一真源。

---

## 3. 核心数据模型：四层分离

## 3.1 Identity Registry

这是系统最重要的持久化状态。

推荐字段：

```text
NoteID
CanonicalWord
MatchKey
SenseLabel
PrimaryOrigin
Status
```

含义：

- `NoteID`：永久业务主键，一旦发布原则上永不修改、永不复用。
- `CanonicalWord`：规范显示词形。
- `MatchKey`：用于发现候选重复的规范化索引，例如 Unicode/空格/apostrophe 规范化后再 casefold。
- `SenseLabel`：target sense 的可读锚点，不作为唯一键。
- `PrimaryOrigin`：最早建立该 identity 的来源记录。

关键规则：

> Registry 不是普通生成物。不能根据 Master 排序重新生成 `KV000001...`；新增词只能追加新 ID。

## 3.2 Source Occurrence / Provenance Layer

每个来源中的每次出现都独立记录，例如：

```text
NoteID
SourceID
SourceBook
Grade
Semester
Unit
SourceWord
SourceFile
SourceRow
```

示例：

```text
KV000001 | rj_start1 | 1年级上 | 1 | 上 | ... | apple
KV000001 | beijing   | 2年级上 | 2 | 上 | ... | apple
```

这样新增来源不会覆盖旧 provenance。

`FirstSource` / `FirstGrade` 可以作为 Master 的便利汇总字段，但不能替代 occurrence 数据。

## 3.3 Vocabulary Fact / Master Layer

这是跨来源汇总后的事实层。

推荐字段：

```text
NoteID
CanonicalWord
Word
British
American
MeaningPrimary
FirstSource
FirstSourceBook
FirstGrade
Sources
SourceBooks
```

注意：`MeaningPrimary` 当前表示这个 learning unit 的核心学习义项。若未来同一个 surface word 出现明显不同义项，应优先考虑建立另一个 NoteID，而不是把所有义项塞进同一张卡。

## 3.4 Learner Presentation Layer

```text
LearnerProfile
LearnerLevel
NoteID
ExampleSentence
ExampleTranslation
PresentationStatus
```

关键原则：

> `FirstGrade` 描述“教材什么时候教”；`LearnerLevel` 描述“Klose 今天怎么学”。

例如：

```text
NoteID: KV000001
Word: apple
FirstGrade: 1
LearnerLevel: 4
ExampleSentence: I usually eat an apple after lunch.
```

到了五年级，可以更新例句，但 NoteID 和 Anki scheduling 不变。

---

## 4. “同一个词”必须定义为 learning unit，而不是字符串

不能使用“字符串相同 = 同一个 Note”的规则。

默认策略：

1. `MatchKey` 只用于产生 candidate。
2. 固定短语（`look at`、`go fishing`、`ice cream`）是独立 learning unit。
3. 相同词形 + 相同 target sense 通常可合并来源。
4. 相同词形但词性/核心义项不同，可以拥有不同 NoteID。
5. 大小写可能携带语义，例如 `May` 与 `may`，不得因 casefold 后相同就自动合并。
6. 歧义项进入 review queue；自动流程不得静默 merge。

因此：

```text
CanonicalWord / MatchKey = 匹配索引
NoteID                  = 业务身份
```

---

## 5. Stable NoteID 的分配规则

推荐格式：

```text
KV000001
KV000002
...
```

但编号必须来自 committed Registry：

```text
已有 Registry
    ↓
发现真正新 learning unit
    ↓
next_id = max(existing) + 1
    ↓
append registry row
```

禁止：

```text
每次把 Master 排序
    ↓
重新 enumerate
    ↓
KV000001...
```

后者会随着新教材插入、排序变化而破坏所有已有 Anki identity。

---

## 6. Source-scoped Grade，而不是全局 Grade

多教材以后，“三年级词”不是一个全局事实。

例如：

```text
apple
人教版一年级起点：1年级出现
北京版：2年级出现
```

因此 provenance / tags 应保留来源作用域：

```text
source::rj_start1
source::rj_start1::grade::1
source::rj_start1::grade::1::上

source::beijing
source::beijing::grade::2
```

`FirstGrade` 只是便利字段；当前学习范围必须按 `SourceID + SourceGrade/Level` 判断。

这也适用于非年级制材料：

```text
source::newconcept::book::1
source::graded_reader::level::3
```

---

## 7. Learner Scope 与“库存”分离

### 7.1 all.csv：完整库存

```text
anki/klose/publish/all.csv
```

包含已经进入 Master 的全部 Note，用于审计、备份、完整同步。

### 7.2 study.csv：默认 Anki 发布入口

```text
anki/klose/publish/study.csv
```

只包含已经释放给 Klose 学习、需要持续在 Anki 中维护的 Notes。

当前四年级示例：

```text
Master inventory:
人教版 1–6 年级全部词

Released / study:
人教版 1–4 年级
```

这样下周即使把北京版加入 Master，只要北京版没有被 release，新北京版独有词不会因为导入 `all.csv` 而突然成为普通 New Cards。

### 7.3 Released set 应视为长期增长集合

Note 一旦进入 Anki 并开始学习，原则上继续保留在 `study.csv`，这样后续释义/例句升级仍能更新它。

如果确需撤回已经释放的 Note，必须作为显式学习策略变更处理，而不是简单从 scope 删除。

---

## 8. Anki 长期组织方式

推荐一个主 Deck：

```text
Klose-English
└── Vocabulary
```

教材、年级、来源主要通过 Tags 表达。

用途分工：

- 正常长期学习：Main Deck + FSRS。
- 当前/历史学习库存：由 `study.csv` 控制。
- 已在 Anki 中但暂时不想出现：Suspend。
- 临时专项复习：Filtered Deck / Browser Search。

Anki Browser 与 Filtered Deck 都可以按 tags/search 条件筛选。官方文档说明 Filtered Deck 会临时抽取匹配 Cards，并在学习完成后返回 Home Deck。citeturn343402search1turn343402search5

---

## 9. Anki Note Type Contract

长期固定 Note Type：

```text
Klose Vocabulary
```

推荐字段顺序：

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
UserMemo          # Anki-local，可选，不从 CSV 更新
```

Tags 使用 Anki 自带 Tags，不需要建立名为 `Tags` 的普通字段。

### 关键导入规则

Anki 官方文档说明，文本导入默认使用**第一字段 + 同一 Note Type**判断已有 Note；选择更新时会原地更新已有 Note，并保留其 scheduling information。官方同时建议，如果长期要更新正文内容，应让第一字段是稳定 ID。citeturn343402search0turn612654search5

因此长期要求：

```text
第一字段 = NoteID
Match scope = Note Type
Import mode = Update Existing Notes
```

不要使用“Note Type + Deck”作为长期 identity 范围。

### System-managed Tags

repo 生成的来源/年级 Tags 视为 system-managed。Anki 文本导入可以把某列映射为 Tags；更新时可能替换既有 tags，因此不要把需要永久保留的个人标签混入 system-managed tags。个人备注建议使用不参与 CSV mapping 的 `UserMemo`，或使用 Card Flag。citeturn343402search0turn199332search0

---

## 10. 旧版 Word-first → NoteID-first 的一次性迁移

这是当前第一批数据必须考虑的兼容问题。

现有旧 CSV 第一字段是 `Word`。如果已经导入 Anki，直接把新版 `NoteID` 放第一列重新导入，会被当成不同 Note，从而产生重复卡片。

正确的一次性迁移：

```text
旧 Note Type：Word 是第一字段
        ↓
先在原 Note Type 中增加 NoteID 等新字段
        ↓
导入 migration/word-first-*.csv
第一列仍为 Word → Update Existing Notes
        ↓
原 Notes 被补上 NoteID，Review History 保留
        ↓
Manage Note Types → Fields
把 NoteID reposition 到第 1 位
        ↓
以后永久使用 NoteID-first study.csv
```

Anki 官方支持对 Note Type 字段进行 reposition，因此无需重建 Note。citeturn612654search0

详细步骤见：`docs/ANKI_MIGRATION.md`。

---

## 11. Publish 文件布局

长期：

```text
anki/klose/publish/
├── study.csv                         # 默认导入
├── all.csv                           # 完整库存
├── migration/
│   ├── word-first-study.csv          # 一次性兼容迁移
│   └── word-first-all.csv
└── by-source/
    └── rj_start1/
        ├── grade1.csv
        ├── grade2.csv
        ├── ...
        └── grade6.csv
```

`by-source` 文件是便利视图，不是长期独立真源，不应各自形成独立牌组体系。

---

## 12. 例句与 LearnerLevel

例句属于 Learner Presentation，不是教材事实。

规则：

1. 难度以当前 `LearnerLevel` 为基准，而不是 `FirstGrade`。
2. 句子应明显低于阅读理解上限，Anki 卡片不能变成阅读理解题。
3. 目标词必须承担清晰、自然的目标义项。
4. 优先使用已掌握/当前阶段常见词和语法。
5. 简单句不是自动失败；如果它对目标词最自然、最高效，可以保留。
6. 不为了“看起来像高年级”机械堆复杂从句。
7. 非教材原句必须标记为 learner-generated/curated，不声称是教材原句。

### 升级策略

升到 Grade 5 时：

```text
Identity Registry      不变
Source Occurrences     不变
Vocabulary Facts       原则上不变
LearnerLevel           4 → 5
Example                可批量升级
Anki FSRS History      不变
```

---

## 13. 自动质量门槛

### Identity

- NoteID 唯一；
- Registry 不因重建而重排；
- MatchKey collision / case collision；
- 同形不同义候选进入 review；
- publish 中 NoteID 唯一。

### Provenance

- 每个 Master 至少一个 source occurrence；
- SourceID / Book / Grade/Level / 原始行号可追溯；
- 不用全局 Grade 覆盖 source-scoped facts。

### Learner

- LearnerProfile / LearnerLevel 完整；
- Meaning / Example / Translation 完整；
- target sense 清晰；
- 当前 released Notes 必须有 learner presentation；
- 自动结构检查通过不能宣称“语义全部人工确认”。

### Publish

- `study.csv ⊆ all.csv`；
- `by-source/*` 只是 Master 视图；
- deterministic build；
- 不静默 fallback 到成人词典首义；
- migration CSV 第一列必须保持 `Word`，正式 publish 第一列必须是 `NoteID`。

---

## 14. 变更类型

### A. Source Expansion

新增北京版/沪教版/新概念：

```text
Raw source
→ normalize occurrences
→ identity candidate matching
→ merge provenance / append NoteID
→ learner presentation
→ release decision
→ rebuild
```

### B. Fact Correction

音标、拼写、核心义项错误：修改事实层；涉及 identity 时进入 migration review。

### C. Learner Upgrade

升年级：更新 Learner Layer，不改 NoteID / source facts。

### D. Identity Merge/Split

高风险变更。必须单独设计 Anki history migration，不允许作为普通清洗直接执行。

### E. Anki Presentation

Card Template/CSS/显示顺序变化，不改变 Vocabulary Identity。

---

## 15. 当前第一批基础数据

首批来源：

```text
SourceID = rj_start1
人教版一年级起点 1–6 年级
```

已知规模：

- 12 册；
- 908 次 source occurrences；
- 802 个当前唯一 learning units；
- 当前目标 LearnerProfile：Klose；
- 当前 LearnerLevel：Grade 4；
- 当前 release scope：人教版一年级起点 1–4 年级。

第一批正式迁移需要完成：

1. Bootstrap committed NoteID Registry；
2. 生成 global source occurrences / Master；
3. 建立 `LearnerLevel=4` presentation layer；
4. 生成 `all.csv` 与 `study.csv`；
5. 生成人教版 1–6 年级便利视图（上下册合并）；
6. 生成 Word-first → NoteID-first 一次性 migration CSV；
7. 对 identity collision、learner presentation、publish invariants 做 CI 检查。

完成后，人教版数据即成为未来北京版、沪教版、新概念等来源接入时的第一批稳定 Vocabulary Base。