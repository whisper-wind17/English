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

### GitHub：内容、身份与发布真源

负责：

- Stable NoteID；
- 标准词形、target sense、音标和核心释义；
- Source / Book / Grade / Unit / 原始行号等 provenance；
- 当前 LearnerLevel 的学习呈现；
- Learner Review Registry 与 approval manifest；
- review queue、质量检查和发布文件。

### Anki：学习状态真源

负责：

- Review History；
- FSRS memory state；
- Due / Interval；
- New / Learning / Review / Suspended；
- Card-level scheduling。

repo 不重建 Anki scheduling；Anki 也不是词汇事实数据的内容真源。

---

## 3. 六层数据模型

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

### 3.2 Source Identity Map（持久化）

跨来源接入时，candidate matching 的确认结果必须持久化：

```text
SourceID
SourceItemKey
NoteID
Decision
Status
```

`source_identity_map.csv` 与 `note_registry.csv` 一样属于长期状态，不是每次构建重新推导的缓存。新教材接入时可以重新计算候选，但一旦确认某个 source learning unit 对应某个 NoteID，后续构建必须复用该映射；若语义发生冲突，进入 identity migration/review，而不是静默改映射。

### 3.3 Source Occurrence / Provenance

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

### 3.4 Vocabulary Fact / Master

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

### 3.5 Learner Presentation

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

### 3.6 Learner Review Registry

Review truth 不能只依赖“自动检查没报错”，也不能只挂在 NoteID 上。长期键：

```text
LearnerProfile + LearnerLevel + NoteID
```

状态：

```text
ContentFingerprint
ReviewStatus       # pending / model-reviewed / human-reviewed
ReviewedAt
ReviewerType
ReviewNote
```

`ContentFingerprint` 绑定：

```text
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerProfile
LearnerLevel
```

任何受审内容变化都会使旧 approval 失效为 `pending`。显式审批产生不可覆盖的：

```text
learner/review_approvals/<batch-id>.csv
```

详细机制见 `docs/LEARNER_REVIEW_REGISTRY.md`。

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

## 7. Inventory、Released Set 与 Anki Import 分离

### `all.csv`：完整库存

```text
anki/klose/publish/all.csv
```

包含进入 Master 的所有 Notes，用于审计、备份和完整视图。

### `study.csv`：Released Set 的内部数据真源

```text
anki/klose/publish/study.csv
```

只包含已经释放给 Klose 学习、且需要持续获得内容更新的 Notes。它保留普通 CSV 表头，用于 repo 构建、审计和 release 对账，**不直接导入 Anki**。

### `anki-import.csv`：唯一正式 Anki 导入文件

```text
anki/klose/publish/anki-import.csv
```

它的数据必须与 `study.csv` 完全一致，但使用 Anki 官方 file headers：

```text
#separator:Comma
#html:false
#notetype:Klose Vocabulary
#deck:Klose-English::Vocabulary
#tags column:12
#columns:...
```

因此没有普通 CSV 数据表头行，不会把 `NoteID / Word / ...` 当成一张 Note。

当前 Grade 4：

```text
Inventory：人教版 1–6 年级全部词
Released：人教版 1–4 年级
```

以后加入北京版但暂不 release 时，北京版独有新词可以先进入 `all.csv`，不会因为日常导入 `anki-import.csv` 而突然进入 New Cards。

### Release 是持久化状态

`release_registry.csv` 记录已释放 Note；每个 release scope 必须显式带 `released_at`，因此 Grade 5/新来源在未来释放时不会被错误记成初始基线日期。Note 一旦进入 Anki，原则上继续保留在 `study.csv` / `anki-import.csv`，以便后续释义/例句升级仍能更新它。撤回已释放 Note 必须是显式学习策略变更。

---

## 8. Anki 组织方式

推荐：

```text
Klose-English
└── Vocabulary
```

**一个主 Deck + Tags**；不按教材、年级或导入批次长期复制 Deck 体系。

- 长期日常学习：Main Deck + FSRS；
- 暂时不想出现的已存在 Card：Suspend；
- 临时专项复习：Filtered Deck / Browser Search；
- 教材/年级/来源/学习阶段：Tags 与 Source Occurrences 表达。

当前 Grade-4 onboarding：

```text
stage::grade4-new             # 四年级首次出现
stage::grade4-review          # 四年级再次出现的低年级词
stage::lower-grade-backfill   # 1–3 年级其余查漏词
```

第一次导入时三个 stage 全部位于同一个 Deck；只开放 `grade4-new`，另外两组先 Suspend。详见 `docs/ANKI_FIRST_IMPORT.md`。

Anki 参考：

- [Searching](https://docs.ankiweb.net/searching.html)
- [Filtered Decks](https://docs.ankiweb.net/filtered-decks.html)

---

## 9. Anki Note / Card Contract

长期固定 Note Type：

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
UserMemo          # Anki-local，可选，不从 CSV 更新
```

Tags 使用 Anki 自带 Tags，不需要建立普通 `Tags` 字段。

长期只保留一个 Card Type：

```text
Recognition
```

因此：

```text
1 Note = 1 Card
```

不要使用 `Basic (and reversed card)`。Card Template / CSS 冻结在：

```text
anki/klose/anki/
```

正式导入第一数据字段固定为 `NoteID`；重新导入时保持同一 Note Type，并使用：

```text
Existing notes = Update
Match scope    = Note Type
```

这样已有 Note 原地更新，学习调度历史保留。

官方参考：

- [Importing Text Files](https://docs.ankiweb.net/importing/text-files.html)
- [Editing / Note Types](https://docs.ankiweb.net/editing.html)

repo 生成的来源/年级/stage Tags 视为 system-managed。长期重新导入可能更新这些 Tags。需要永久保留的个人备注不要混入这组 Tags，使用不参与 CSV mapping 的 `UserMemo` 或 Card Flag。

---

## 10. Word-first → NoteID-first 一次性迁移

旧版人教版 CSV 第一字段是 `Word`。如果这些 Notes 已经进入 Anki，直接导入新版 NoteID-first 发布文件会产生重复 Note。

安全迁移：

```text
旧 Note Type：Word 第一字段
→ 在原 Note Type 增加 NoteID 等字段
→ 导入 migration/word-first-*.csv（仍以 Word 为第一列）
→ Update Existing Notes，给旧 Note 补 NoteID
→ 抽样确认 Review History / Due / Interval 未丢失
→ Manage Note Types → Fields → 把 NoteID reposition 到第 1 位
→ 以后永久使用 NoteID-first anki-import.csv
```

详细步骤：`docs/ANKI_MIGRATION.md`。

---

## 11. Publish 文件布局

```text
anki/klose/publish/
├── study.csv                         # released-set 内部数据真源/审计 CSV
├── anki-import.csv                   # 唯一正式 Anki 导入文件
├── all.csv                           # 完整库存
├── onboarding/                       # 同一 study 集合的学习阶段便利视图
│   ├── grade4-new.csv
│   ├── grade4-review.csv
│   └── lower-grade-backfill.csv
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

`by-source` 与 `onboarding` 都只是 Master/Study 的便利视图，不形成另一套数据真源或长期 Deck；不要在已经导入 `anki-import.csv` 后再把这些视图重复导入。

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
Grade-5 Review         新建，默认 pending
Anki FSRS History      不变
```

---

## 13. 自动质量门槛与 Release Gate

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

### Review

- 每个 released Note 有当前 `LearnerProfile + LearnerLevel` review row；
- review status 必须绑定当前 ContentFingerprint；
- 内容变化后旧 approval 必须失效；
- `model-reviewed` 与 `human-reviewed` 明确区分；
- 只有真实完成逐条审校后才能运行显式 approval 工具。

### Publish

- `study.csv` 与 Released Set 一致；
- `anki-import.csv` 数据与 `study.csv` 完全一致；
- `anki-import.csv` 使用正确的 Anki file headers，没有普通数据表头；
- 每个 released Note 恰好一个 `stage::` Tag；
- `by-source/*` / `onboarding/*` 只是视图；
- deterministic build；
- 不静默 fallback 到成人词典首义；
- migration CSV 第一列必须是 `Word`，正式 Anki import 第一数据字段必须是 `NoteID`。

### 正式导入门槛

```bash
python tools/check_klose_release_ready.py
```

只有当：

```text
identity / learner / future-vocabulary reports = 0
review pending                             = 0
ContentFingerprint stale                  = 0
study.csv == Released Set
anki-import.csv data == study.csv
Anki file headers                          = valid
stage partition                            = valid
```

才能把当前 `anki-import.csv` 描述为“可以正式导入 Anki”。

CI 必须在 commit/push generated release **之前**通过该 Gate，禁止先发布错误数据再报失败。

---

## 14. 变更类型

### Source Expansion

```text
Raw source
→ normalize occurrences
→ sense-aware identity candidate matching
→ persist SourceItemKey → NoteID decision
→ merge provenance / append NoteID
→ learner presentation
→ learner review
→ release decision
→ rebuild / release gate
```

### Fact Correction

修正拼写、音标或核心义项；涉及 identity 时进入 migration review。若 `MeaningPrimary` 改变，相关 learner review fingerprint 必须失效。

### Learner Upgrade

升年级只更新 Learner Layer，不改 NoteID / source facts；新 level 必须重新审校和 approval。

### Identity Merge/Split

高风险变更，必须单独设计 Anki history migration，不作为普通清洗直接执行。

### Anki Presentation

Card Template / CSS / 显示顺序变化不改变 Vocabulary Identity。

---

## 15. 第一批正式基线：rj_start1 Grade-4 Baseline v1

截至 2026-09-05，第一批正式基础数据：

```text
SourceID = rj_start1
人教版一年级起点 1–6 年级 inventory
LearnerProfile = klose
LearnerLevel = 4
Released scope = 人教版 1–4 年级
```

当前基线：

- 12 册；
- 908 次 source occurrences；
- 802 个 Inventory Notes；
- Stable Registry：`KV000001`–`KV000802`；
- Source Identity Map：802；
- 当前 Released Notes：518；
- Grade-4 `model-reviewed = 518 / pending = 0`；
- approval manifest：`learner/review_approvals/grade4-baseline-v1.csv`；
- identity / learner / future-vocabulary review 均为 0；
- onboarding：175 个 `grade4-new`、26 个 `grade4-review`、317 个 `lower-grade-backfill`；
- `study.csv`：released-set 内部数据真源；
- `anki-import.csv`：唯一正式 Anki 导入文件；
- `all.csv`：完整 802 Notes 库存；
- Note/Card contract：一个 `Recognition` Card，`1 Note = 1 Card`；
- Word-first → NoteID-first migration CSV 已生成。

关键长期状态：

```text
anki/klose/master/note_registry.csv
anki/klose/master/source_identity_map.csv
anki/klose/master/release_registry.csv
anki/klose/learner/presentation_review_registry.csv
anki/klose/learner/review_approvals/*.csv
```

未来接入北京版、沪教版、新概念等来源时，应在这套基线上扩展，而不是重新建立另一套 NoteID/Deck 体系。

---

## 16. 当前实现入口

Global：

```text
tools/check_klose_persistent_state.py
tools/build_klose_vocabulary.py
tools/apply_klose_learner_overrides.py
tools/sync_klose_learner_review_registry.py
tools/check_klose_learner.py
tools/check_klose_release_ready.py
tools/approve_klose_learner_review.py    # 显式操作，不属于日常 CI
.github/workflows/build-klose-vocabulary.yml
```

Source Adapter：

```text
anki/人教版一年级起点/
tools/build_anki_rj_start1.py
```

Anki Contract：

```text
anki/klose/anki/
```

Global Data Area：

```text
anki/klose/
```

详细执行规则以根目录 `AGENTS.md` 为准；首次正式导入见 `docs/ANKI_FIRST_IMPORT.md`。
