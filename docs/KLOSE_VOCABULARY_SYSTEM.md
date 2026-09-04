# Klose Vocabulary System

> 本文定义 Klose 的长期英语词汇学习系统。目标不是制作一次性 Anki 牌组，而是维护一个可持续多年扩展、可追溯、可升级且不破坏既有记忆历史的 Vocabulary Knowledge Base；Anki 负责 SRS/FSRS 与学习状态。

## 1. 两条长期演进轴

### Vocabulary Expansion

不断接入新来源：

```text
人教版一年级起点
+ 北京版
+ 沪教版
+ 新概念
+ 分级阅读
+ 其他材料
```

已有 learning unit 只扩展 provenance；真正的新 learning unit 才获得新的 NoteID。

### Learner Presentation Evolution

```text
Grade 4 presentation
    ↓
Grade 5 presentation
    ↓
Grade 6 presentation
```

升级的是例句、解释方式和学习提示，不是 Vocabulary Identity，也不是 Anki Review History。

---

## 2. GitHub 与 Anki 的职责边界

### GitHub：内容与身份真源

负责：

- Stable NoteID；
- 标准词形、target sense、音标和核心释义；
- Source / Book / Grade / Unit / 原始行号等 provenance；
- 当前 LearnerLevel 的学习呈现；
- review queue、质量检查和发布 CSV。

### Anki：学习状态真源

负责：

- Review History；
- FSRS memory state；
- Due / Interval；
- New / Learning / Review / Suspended；
- Card-level scheduling。

repo 不重建 Anki scheduling；Anki 也不是词汇事实数据的内容真源。

---

## 3. 四层数据模型

### 3.1 Identity Registry

长期持久化状态：

```text
NoteID
CanonicalWord
MatchKey
SenseLabel
PrimaryOriginKey
CreatedSource
CreatedSourceBook
Status
```

- `NoteID`：永久业务主键；一旦发布不重编号、不复用。
- `CanonicalWord`：规范词形。
- `MatchKey`：只用于发现候选重复，例如 Unicode/空格/apostrophe 规范化后 casefold。
- `SenseLabel`：target sense 的可读锚点。
- `PrimaryOriginKey`：建立该 identity 时的来源锚点。

Registry 不是普通生成物。新增词只能追加 ID，禁止根据 Master 当前排序重新 enumerate。

### 3.2 Source Occurrence / Provenance

每次来源出现独立记录：

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

例如同一个 `apple` 可以同时有：

```text
KV000001 | rj_start1 | 1年级上 | 1 | 上 | ...
KV000001 | beijing   | 2年级上 | 2 | 上 | ...
```

新增来源不会覆盖历史来源事实。

### 3.3 Vocabulary Fact / Master

跨来源汇总：

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

`MeaningPrimary` 是该 learning unit 的核心学习义项。若同一 surface word 出现明显不同 target sense，应优先建立另一个 NoteID，而不是把所有义项塞进一张卡。

### 3.4 Learner Presentation

```text
LearnerProfile
LearnerLevel
NoteID
ExampleSentence
ExampleTranslation
PresentationStatus
PresentationSource
```

核心原则：

> `FirstGrade` 描述“教材什么时候教”；`LearnerLevel` 描述“Klose 今天怎么学”。

例如一年级首次出现的 `apple`，四年级仍可以使用四年级水平的例句；升五年级只更新 presentation，不修改 NoteID 和 Anki scheduling。

---

## 4. Identity：learning unit，不是字符串

不能使用“字符串一样 = 同一个 Note”的规则。

默认策略：

1. `MatchKey` 只产生 candidate；
2. 固定短语（如 `look at`、`go fishing`）是独立 learning unit；
3. 相同词形 + 相同 target sense 通常可合并来源；
4. 相同词形但词性/核心义项不同，可以拥有不同 NoteID；
5. 大小写可能携带语义，例如 `May` 与 `may`，不得因 casefold 后相同就自动合并；
6. 歧义进入 review queue，禁止静默 merge。

```text
CanonicalWord / MatchKey = 匹配索引
NoteID                  = 长期业务身份
```

---

## 5. Stable NoteID 分配

格式：

```text
KV000001
KV000002
...
```

分配方式：

```text
读取 committed Registry
→ 确认真正新 learning unit
→ next_id = max(existing) + 1
→ append registry row
```

禁止：

```text
Master 排序
→ 每次重新 enumerate
```

否则新增教材或排序变化会破坏 Anki identity。

---

## 6. Source-scoped Level

多教材以后，“几年级词”不是一个全局事实。

```text
apple
人教版一年级起点：1年级出现
北京版：2年级出现
```

因此 provenance / Tags 必须保留来源作用域：

```text
source::rj_start1
source::rj_start1::grade::1
source::rj_start1::grade::1::上
source::beijing::grade::2
source::newconcept::book::1
```

`FirstGrade` 只是便利汇总字段；当前学习资格必须按 `SourceID + SourceGrade/Level` 判断。

---

## 7. Inventory 与 Released Set 分离

### `all.csv`：完整库存

```text
anki/klose/publish/all.csv
```

包含进入 Master 的所有 Notes，用于审计、备份和完整视图。

### `study.csv`：默认 Anki 发布入口

```text
anki/klose/publish/study.csv
```

只包含已经释放给 Klose 学习、且需要持续获得内容更新的 Notes。

当前 Grade 4：

```text
Inventory：人教版 1–6 年级全部词
Released：人教版 1–4 年级
```

以后加入北京版但暂不 release 时，北京版独有新词可以先进入 `all.csv`，不会因为日常导入 `study.csv` 而突然进入 New Cards。

### Release 是持久化状态

`release_registry.csv` 记录已释放 Note。Note 一旦进入 Anki，原则上继续保留在 `study.csv`，以便后续释义/例句升级仍能更新它。撤回已释放 Note 必须是显式学习策略变更。

---

## 8. Anki 组织方式

推荐：

```text
Klose-English
└── Vocabulary
```

一个主 Deck + Tags；不按教材长期复制 Deck 体系。

- 长期日常学习：Main Deck + FSRS；
- 暂时不想出现的已存在 Card：Suspend；
- 临时专项复习：Filtered Deck / Browser Search；
- 教材/年级/来源：Tags 与 Source Occurrences 表达。

Anki 参考：

- [Searching](https://docs.ankiweb.net/searching.html)
- [Filtered Decks](https://docs.ankiweb.net/filtered-decks.html)

---

## 9. Anki Note Type Contract

长期固定 Note Type：

```text
Klose Vocabulary
```

推荐字段：

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

Tags 使用 Anki 自带 Tags，不需要建立普通 `Tags` 字段。

正式发布 CSV 第一字段固定为 `NoteID`；重新导入时保持同一 Note Type，并使用 Update Existing Notes / Note Type 范围匹配。这样已有 Note 原地更新，学习调度历史保留。

官方参考：

- [Importing Text Files](https://docs.ankiweb.net/importing/text-files.html)
- [Editing / Note Types](https://docs.ankiweb.net/editing.html)

repo 生成的来源/年级 Tags 视为 system-managed。需要永久保留的个人备注不要混入这组 Tags，使用不参与 CSV mapping 的 `UserMemo` 或 Card Flag。

---

## 10. Word-first → NoteID-first 一次性迁移

旧版人教版 CSV 第一字段是 `Word`。如果这些 Notes 已经进入 Anki，直接导入新版 NoteID-first CSV 会产生重复 Note。

安全迁移：

```text
旧 Note Type：Word 第一字段
→ 在原 Note Type 增加 NoteID 等字段
→ 导入 migration/word-first-*.csv（仍以 Word 为第一列）
→ Update Existing Notes，给旧 Note 补 NoteID
→ 抽样确认 Review History / Due / Interval 未丢失
→ Manage Note Types → Fields → 把 NoteID reposition 到第 1 位
→ 以后永久使用 NoteID-first study.csv
```

详细步骤：`docs/ANKI_MIGRATION.md`。

---

## 11. Publish 文件布局

```text
anki/klose/publish/
├── study.csv                         # 默认长期导入
├── all.csv                           # 完整库存
├── migration/
│   ├── word-first-study.csv          # 一次性旧库迁移
│   └── word-first-all.csv
└── by-source/
    └── rj_start1/
        ├── grade1.csv
        ├── grade2.csv
        ├── ...
        └── grade6.csv
```

`by-source` 文件把上下册合并成年级视图，仅用于检查/分析/特殊操作，不形成另一套数据真源或长期 Deck。

---

## 12. LearnerLevel 与例句

例句属于 Learner Presentation，不是教材事实。

规则：

1. 难度以当前 `LearnerLevel` 为基准，不是 `FirstGrade`；
2. 明显低于阅读理解上限，避免卡片变成阅读理解题；
3. target word/sense 在句中清晰、自然；
4. 优先使用已掌握或当前阶段常见词和语法；
5. 简单句并非自动不合格；自然和有效优先于机械复杂化；
6. 不为“像高年级”而堆复杂从句；
7. 非教材原句明确视为 generated/curated learner content。

升 Grade 5 时：

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
- Registry 不因重建重排；
- MatchKey/case/homograph candidate 检查；
- 歧义进入 review；
- publish NoteID 唯一。

### Provenance

- 每个 Master 至少一个 source occurrence；
- SourceID / Book / Grade/Level / 原始行号可追溯；
- 不用全局 Grade 覆盖 source-scoped facts。

### Learner

- LearnerProfile / LearnerLevel / Meaning / Example / Translation 完整；
- released Notes 必须有 learner presentation；
- Grade-4 例句不得无意使用同来源明确到后续年级才首次列出的词；
- 自动结构检查通过不能宣称“语义全部由教师人工确认”。

### Publish

- `study.csv ⊆ all.csv`；
- `by-source/*` 只是 Master 视图；
- deterministic build；
- 不静默 fallback 到成人词典首义；
- migration CSV 第一列必须是 `Word`，正式 publish 第一列必须是 `NoteID`。

---

## 14. 变更类型

### Source Expansion

```text
Raw source
→ normalize occurrences
→ sense-aware identity candidate matching
→ merge provenance / append NoteID
→ learner presentation
→ release decision
→ rebuild
```

### Fact Correction

修正拼写、音标或核心义项；涉及 identity 时进入 migration review。

### Learner Upgrade

升年级只更新 Learner Layer，不改 NoteID / source facts。

### Identity Merge/Split

高风险变更，必须单独设计 Anki history migration，不作为普通清洗直接执行。

### Anki Presentation

Card Template / CSS / 显示顺序变化不改变 Vocabulary Identity。

---

## 15. 第一批稳定基线：rj_start1

截至 2026-09-04，第一批基础数据已经完成正式迁移：

```text
SourceID = rj_start1
人教版一年级起点 1–6 年级
LearnerProfile = klose
LearnerLevel = 4
```

当前基线：

- 12 册；
- 908 次 source occurrences；
- 802 个 Inventory Notes；
- Stable Registry：`KV000001`–`KV000802`；
- 当前 Released Notes：518（人教版 1–4 年级范围）；
- `study.csv`：默认 Anki 发布入口；
- `all.csv`：完整 802 Notes 库存；
- 6 个按年级合并的 source convenience views；
- Word-first → NoteID-first migration CSV 已生成；
- Grade-4 learner layer 已建立；
- identity review / learner review / future-vocabulary review 当前均为 0；
- Global CI 已通过，并验证第二次构建 Registry/Release Registry 不发生漂移。

关键持久化文件：

```text
anki/klose/master/note_registry.csv
anki/klose/master/release_registry.csv
```

这两个文件不是普通生成缓存。未来接入北京版、沪教版、新概念等来源时，应在这套基线上扩展，而不是重新建立另一套 NoteID/Deck 体系。

---

## 16. 当前实现入口

```text
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/check_klose_learner.py
.github/workflows/build-klose-vocabulary.yml
```

Source Adapter：

```text
anki/人教版一年级起点/
tools/build_anki_rj_start1.py
```

Global Data Area：

```text
anki/klose/
```

详细执行规则以根目录 `AGENTS.md` 为准。