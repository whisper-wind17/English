# Anki 一次性迁移：Word-first → NoteID-first

本文只处理旧版人教版 CSV 已经导入 Anki 时的兼容问题。迁移完成后的长期同步统一使用 `anki/klose/publish/anki-import.csv`；详细 SOP 见 `docs/ANKI_SYNC_WORKFLOW.md`。

如果设备已经完成 NoteID-first 迁移、当前只需要扩展字段，不要重跑本文：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

## 为什么必须迁移

旧版 CSV 第一字段是：

```text
Word
```

新版长期系统第一字段是：

```text
NoteID
```

Anki 文本导入默认依赖第一字段 + Note Type 识别重复 Note。若旧 Notes 已存在，直接导入 NoteID-first 发布文件，会把 `KV000001` 与旧 `book/apple/...` 视为不同第一字段，产生重复 Note。

因此必须先给现有 Notes 补 NoteID，再把 NoteID reposition 为 Note Type 第一字段。

## 场景 A：还没有导入过旧版数据

不需要做本迁移，直接按：

```text
docs/ANKI_FIRST_IMPORT.md
```

正式导入文件：

```text
anki/klose/publish/anki-import.csv
```

不要直接导入 `study.csv`。

## 场景 B：已经导入过旧版 Word-first 数据

### Step 0：先备份

先导出 Collection/Deck 备份。

### Step 1：保持当前 Word 仍是第一字段

不要先 reposition。

在原 `Klose Vocabulary` Note Type 中增加以下字段（不存在才加）：

```text
NoteID
CanonicalWord
PromptHint
LearnerLevel
LearningOrder
Sources
SourceBooks
```

建议另外增加：

```text
UserMemo
```

`PromptHint` 是可选 Learner Presentation；`LearningOrder` 是 curriculum/admission metadata；`UserMemo` 只在 Anki 本地维护，不从 repo CSV 更新。

### Step 2：导入兼容迁移文件

如果当前 Anki 中只希望保留/迁移人教版 1–4 年级：

```text
anki/klose/publish/migration/word-first-study.csv
```

如果此前已经把 1–6 年级全部导入：

```text
anki/klose/publish/migration/word-first-all.csv
```

迁移 CSV 第一列仍是 Word，因此可以匹配旧 Notes。

导入要求：

```text
Note Type       = existing Klose Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Word            -> Word
NoteID          -> NoteID
PromptHint      -> PromptHint
LearningOrder   -> LearningOrder
Tags            -> Anki Tags
```

其余字段按名称映射；`UserMemo` 不映射。

确认结果主要是 updated existing notes，而不是批量新增重复 Notes。

### Step 3：抽样检查 Review History

至少检查 3–5 张已有卡：

- Card Info 中 Reviews 未清零；
- Due / Interval 正常；
- Note 中已出现 `KVxxxxxx` NoteID。

### Step 4：把 NoteID reposition 为第一字段

Anki：

```text
Tools
→ Manage Note Types
→ Klose Vocabulary
→ Fields
→ NoteID
→ Reposition
→ 1
```

这一步只修改 Note Type 字段顺序，不新建 Note。

最终字段顺序以 `anki/klose/anki/README.md` 为准，当前为：

```text
NoteID
CanonicalWord
Word
PromptHint
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
LearningOrder
Sources
SourceBooks
UserMemo
```

### Step 5：以后只使用 NoteID-first 正式发布文件

永久改用：

```text
anki/klose/publish/anki-import.csv
```

长期导入规则：

```text
第一数据字段   = NoteID
Note Type      = Klose Vocabulary
Match scope    = Note Type
Existing Notes = Update
```

`study.csv` 只用于 repo 内 Released Set 审计，不直接导入 Anki。不要再把旧 `anki/人教版一年级起点/import/*.csv` 当长期入口。

若当前 learning admission 有 `LearningOrder`，对仍为 `is:new` 的 admitted Cards 按 `docs/ANKI_LEARNING_ORDER_MIGRATION.md` 初始化 New Card Position；不要对已进入真实 FSRS 的 Cards 重排 Due。

## Tags / local state 边界

来源、学习范围等 system-managed Tags 由 repo 管理。需要永久保留但 repo 不知道的个人信息，不要混入这些系统 Tags；优先使用：

- `UserMemo`；
- Card Flag。

## 发布文件边界

```text
study.csv       = generated released long-lived snapshot
anki-import.csv = generated 唯一正式 Anki 发布包
```

二者都不手工编辑；问题必须回到 Source / Identity / Learner / Admission / Release 上游处理。

## 迁移完成标准

- 旧卡没有因迁移大幅翻倍；
- Review History / Due / Interval 保留；
- 每个 Note 有稳定 NoteID；
- NoteID 已成为第一字段；
- Note Type 字段契约与 `anki/klose/anki/README.md` 一致；
- 最新 `anki-import.csv` 重新导入只更新已有 Notes + 增加真正新 Note；
- 尚未学习的新卡可按明确 LearningOrder 初始化顺序；
- 后续新增教材不会为已有 learning unit 创建第二套 FSRS 记忆状态。
