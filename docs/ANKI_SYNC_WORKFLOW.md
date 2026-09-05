# Klose Vocabulary：长期 Anki 同步流程

本文定义第一次正式导入之后，repo 与 Anki 之间长期、重复执行的同步契约。

## 1. 两个文件，两种职责

```text
anki/klose/publish/study.csv
```

是 **Released Set 的内部标准数据快照**。它用于构建、审计、diff、release 对账和自动检查，不直接给 Anki 使用。

```text
anki/klose/publish/anki-import.csv
```

是 **面向 Anki 的唯一发布产物**。它由当前 `study.csv` 自动生成，数据必须与 `study.csv` 完全一致，只额外增加 Anki `#...` file headers 和导入格式约束。

二者都属于 generated output：

```text
禁止手工编辑 study.csv
禁止手工编辑 anki-import.csv
```

任何内容变化必须从上游事实、Learner Layer、Release Registry 或 Source Adapter 修改，再通过构建重新生成。

---

## 2. 长期数据流

```text
Raw Source / Curation
        ↓
Identity + Source Occurrences
        ↓
Vocabulary Master
        ↓
Learner Presentation
        ↓
Learner Review / Approval
        ↓
Release Registry
        ↓
study.csv
        ↓
anki-import.csv
        ↓
Release Gate
        ↓
Anki
```

GitHub 负责“内容、身份和发布”；Anki 负责“学习状态”。

Anki 中的以下状态不得由 repo 重建：

```text
Review History
FSRS memory state
Due / Interval
Learning / Review 状态
```

---

## 3. 什么情况下需要重新同步

以下变化都通过重新生成并导入最新版 `anki-import.csv` 生效：

- 新增教材、词书或其他来源；
- 新增真正的新 learning unit / NoteID；
- 已有词新增 provenance；
- 修正核心释义、拼写、音标；
- 升 LearnerLevel 后升级例句/译文；
- 新 release scope，例如提前开放 Grade 5；
- system-managed Tags 变化。

不需要因为这些变化创建新的长期 Deck 或 Note Type。

---

## 4. 每次同步的固定 SOP

### Step 1：只修改上游

根据变更类型修改：

```text
Raw Source / Source Adapter
Identity Registry / Source Identity Map
Vocabulary facts
Learner presentation / overrides
Release Registry
```

不要修改 `publish/*.csv` 来“修最终结果”。

### Step 2：完成审校

若 `MeaningPrimary / ExampleSentence / ExampleTranslation / LearnerLevel` 发生变化，ContentFingerprint 会变化，对应 review 必须重新进入 `pending`，完成显式 review/approval 后才能发布。

### Step 3：重新构建

```bash
python tools/check_klose_persistent_state.py
python tools/build_klose_vocabulary.py
python tools/apply_klose_learner_overrides.py
python tools/sync_klose_learner_review_registry.py
python tools/check_klose_learner.py
python tools/check_klose_release_ready.py
```

构建会重新生成：

```text
study.csv
anki-import.csv
all.csv
onboarding / by-source views
```

### Step 4：Release Gate

必须确认：

```text
study.csv == Released Set
anki-import.csv data == study.csv
NoteID unique
review pending == 0
ContentFingerprint stale == 0
review queues == 0
Anki file headers valid
UTF-8 without BOM
```

Gate 未通过时不得把该版本导入 Anki。

### Step 5：导入 Anki

始终导入：

```text
anki/klose/publish/anki-import.csv
```

长期保持：

```text
Note Type      = Klose Vocabulary
Deck           = Klose-English::Vocabulary
Existing notes = Update
Match scope    = Note Type
```

Stable NoteID 已存在时更新原 Note；新 NoteID 创建新 Note。已有 Card 的 FSRS / Review History 不应因内容更新而重建。

### Step 6：只对尚未学习的新卡做准入控制

新增 release scope 后，使用 Tags 在 Browser 中控制 New Cards 的 Suspend/Unsuspend。

```text
未学 New Card → 可以 Suspend / Unsuspend
已学 Card     → 保持正常，由 FSRS 持续调度
```

不得因为教材或年级 scope 变化重新 Suspend 已经进入 Learning/Review 的旧卡。

---

## 5. 典型场景

### 新增北京版

```text
北京版 Raw Source
→ source identity matching
→ 已有词复用原 NoteID、扩展 provenance
→ 新词追加新 NoteID
→ learner review / release decision
→ rebuild
→ anki-import.csv v2
→ 导入同一个主 Deck
```

### 提前开放 Grade 5

```text
更新 Release Registry
→ Grade-5 learner presentation / review
→ rebuild
→ study.csv 增长
→ anki-import.csv 同步增长
→ 导入同一个主 Deck
→ 只 Unsuspend 本次准备学习的 New Cards
```

### Grade 5 升级旧词例句

```text
NoteID 不变
→ LearnerLevel 4 → 5
→ 例句/译文更新
→ fingerprint 变化
→ Grade-5 review / approval
→ rebuild
→ 重新导入 anki-import.csv
→ 原 Card 学习历史继续
```

---

## 6. 三个长期不变量

```text
Vocabulary Identity  → Stable NoteID
Anki 学习入口         → 一个主 Deck
Anki 同步入口         → anki-import.csv
```

而：

```text
教材来源
Released Set
LearnerLevel
例句
Tags
词汇规模
```

都可以持续演进。

核心原则：

> 修改发生在上游；`study.csv` 是内部 released snapshot；`anki-import.csv` 是自动生成的 Anki 发布包；Anki 自己保存多年累积的学习历史。
