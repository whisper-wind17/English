# Klose Vocabulary：第一次正式导入 Anki

本文只描述 **NoteID-first 新系统的第一次正式导入**。第一次导入完成后的长期重复同步，统一按 `docs/ANKI_SYNC_WORKFLOW.md` 执行。

如果设备里已经导入过旧版 Word-first 人教版 CSV，先按 `docs/ANKI_MIGRATION.md` 做迁移，不要直接重复导入。

## 1. 当前正式基线

Grade-4 Baseline v1：

```text
Released Notes            = 518
model-reviewed            = 518
pending                    = 0
identity review            = 0
learner review             = 0
future-vocabulary review   = 0
```

当前学习阶段：

```text
stage::grade4-new            = 175
stage::grade4-review         = 26
stage::lower-grade-backfill  = 317
```

内部 released snapshot：

```text
anki/klose/publish/study.csv
```

**真正给 Anki 导入的发布文件：**

```text
anki/klose/publish/anki-import.csv
```

不要直接导入 `study.csv`。`study.csv` 保留普通 CSV 表头，供 repo 构建/审计；`anki-import.csv` 使用 Anki 官方 `#...` file headers，没有普通数据表头行，并使用 UTF-8 **无 BOM**，避免把表头误导入或影响 file headers 识别。

`study.csv` 和 `anki-import.csv` 都是 generated output，均不得手工修改。内容问题应修上游数据并重新构建。

---

## 2. 先建立唯一主 Deck

创建并长期保留：

```text
Klose-English::Vocabulary
```

不要按教材或阶段创建长期子 Deck。教材、年级、学习阶段统一由 Tags / Source metadata 表达。

Klose 日常只需要进入这个一个 Deck。

---

## 3. 建立唯一 Note Type

长期 Note Type：

```text
Klose Vocabulary
```

建议从 **Basic** 新建/复制，不要使用 `Basic (and reversed card)`。

字段顺序固定为：

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

其中：

- `NoteID` 永久保持第一字段；
- `UserMemo` 只在 Anki 本地维护，不映射 CSV；
- CSV 的 `Tags` 映射到 Anki 自带 Tags，不建立普通 `Tags` 字段。

Card Template 使用 repo 中：

```text
anki/klose/anki/card_front.html
anki/klose/anki/card_back.html
anki/klose/anki/styling.css
```

只保留 **1 个 Card Type**（建议名 `Recognition`）：

```text
1 Note = 1 Card
```

因此首次导入完成后应当是：

```text
518 Notes = 518 Cards
```

如果出现约 1036 Cards，说明误建了反向卡，必须先修 Note Type，不能继续学习。

---

## 4. 导入正式发布文件

导入：

```text
anki/klose/publish/anki-import.csv
```

该文件自带：

```text
#separator:Comma
#html:false
#notetype:Klose Vocabulary
#deck:Klose-English::Vocabulary
#tags column:12
#columns:...
```

仍应在 Import Preview 中核对：

```text
Note Type   = Klose Vocabulary
Deck        = Klose-English::Vocabulary
```

并确认字段：

```text
NoteID              → NoteID
CanonicalWord       → CanonicalWord
Word                → Word
British             → British
American            → American
MeaningPrimary      → MeaningPrimary
ExampleSentence     → ExampleSentence
ExampleTranslation  → ExampleTranslation
LearnerLevel        → LearnerLevel
Sources             → Sources
SourceBooks         → SourceBooks
Tags                → Anki Tags
```

长期重复导入时：

```text
Existing notes = Update
Match scope    = Note Type
```

不要使用 `Note Type + Deck` 作为长期匹配范围，否则卡片以后被移动到其他 Deck 时可能无法匹配同一 NoteID。Anki 对同一 Note Type + 第一字段匹配的 Note 会原地更新，并保留现有 scheduling information。

如果导入预览中出现一条：

```text
NoteID = NoteID
Word   = Word
```

立即停止导入。这表示使用了错误文件或 Anki 没有正确识别 file headers。若当前 Anki 仍启用了 Legacy import/export handling，也应关闭 Legacy importer 或升级到当前版本后再导入。

---

## 5. 第一次只开放四年级新词

518 Notes 全部导入同一个 Deck 后，**先不要点击 Study Now**，先完成下面的 Suspend 操作。

保持正常：

```text
tag:stage::grade4-new
```

175 Cards。

Suspend：

```text
tag:stage::grade4-review
```

26 Cards。

再 Suspend：

```text
tag:stage::lower-grade-backfill
```

317 Cards。

最终应为：

```text
Klose-English::Vocabulary
├── grade4-new            175   Unsuspended
├── grade4-review          26   Suspended
└── lower-grade-backfill  317   Suspended
```

仍然只有一个 Deck。

首次导入后建议在 Cards 模式核对：

```text
deck:"Klose-English::Vocabulary"                     → 518
deck:"Klose-English::Vocabulary" is:suspended        → 343
deck:"Klose-English::Vocabulary" -is:suspended       → 175
```

只有这三个数字正确后才开始第一次学习。

---

## 6. 新词顺序

当前 `grade4-new` 同时包含四年级上、下册新词。NoteID / 导入顺序保持教材顺序，因此希望先学四上再四下时，Deck Options 建议明确设置：

```text
New card insertion order = Sequential
New card gather order    = Ascending position（或 Deck，视版本名称）
New card sort order      = Order gathered
```

不要使用随机 New Card 顺序，否则四上、四下会混在一起。

---

## 7. FSRS 基础建议

当前建议起点：

```text
FSRS                 = ON
Desired retention    ≈ 0.93
Learning steps       = 10m
Relearning steps     = 10m
Reviews before new   = ON
Max reviews/day      = 足够高，不用它截断到期复习
```

新词数量先从实际负担出发。可以从 5 个/天开始；如果 2–3 周后日常 Review 负担稳定，再提高到 8–10 个/天。这个参数不影响数据架构。

---

## 8. Tags 的所有权

repo 导入的：

```text
source::...
stage::...
learner::...
```

统一视为 **system-managed Tags**。长期重新导入时 Tags 也可能被更新/替换，因此不要把需要永久保留的个人信息放在这些 Tags 里。

个人备注使用：

```text
UserMemo
```

或者 Anki Card Flag。

---

## 9. Suspend 的长期规则

Suspend 是“尚未开始学习的新卡的准入控制”，不是长期遗忘机制。

当前第一次导入时：

```text
grade4-review + lower-grade-backfill
```

都还没有 Review History，因此可以安全 Suspend。

一旦某张卡已经进入：

```text
Learning / Review
```

以后即使切换教材、年级或 active source，也**不要因为 scope 变化重新 Suspend 它**。否则会中断旧词按照 FSRS 持续复习，违背本系统的核心目标。

因此未来的原则是：

```text
未学 New Card    → 可以按阶段 Suspend / Unsuspend
已学 Card        → 保持正常，由 FSRS 决定复习时间
```

---

## 10. 第一次导入以后

第一次初始化完成后，不再把本文件当作每次同步 SOP。以后新增 Grade 5、北京版、新概念、升级例句等，都遵循：

```text
修改上游数据
→ rebuild study.csv
→ generate anki-import.csv
→ release gate
→ 重新导入最新版 anki-import.csv
```

详细规则见：

```text
docs/ANKI_SYNC_WORKFLOW.md
```

已有 NoteID 使用 Update Existing，原 Card / FSRS / Review History 保留；新 NoteID 在同一个主 Deck 中创建 New Card。

CSV 更新 Note 内容和 system-managed Tags，但不会替你决定所有已有 Card 的 Suspend/Unsuspend 状态。需要开放某个新阶段时，只对对应的 **New Cards** 做 Unsuspend；已经学过的 Card 保持正常 Review。

---

## 11. Release Gate

任何正式同步 Anki 之前：

```bash
python tools/check_klose_release_ready.py
```

必须通过。

它验证：

- `study.csv` 与 Released Set 一致；
- `anki-import.csv` 为 UTF-8 无 BOM；
- `anki-import.csv` headers 正确，且数据与 `study.csv` 完全一致；
- 每个 released Note 恰好一个 `stage::` Tag；
- 必填学习字段完整；
- identity / learner / future-vocabulary review 均为空；
- released Notes 全部 model-reviewed 或 human-reviewed；
- ContentFingerprint 与当前 Meaning / Example / Translation 一致。

CI 必须先通过该 Gate，之后才允许提交生成的 release 文件。
