# Anki 一次性迁移：增加 PromptHint，不重建 Card

本 SOP 只处理当前 `Klose Vocabulary` Note Type 增加 `PromptHint` 字段和对应 Recognition 正面模板。

目标：

```text
同一个 Note Type
同一个 NoteID
同一张 Card
同一份 FSRS / Review History
+ 一个可选 PromptHint 字段
```

禁止通过新建第二套 Note Type、删除旧 Notes、重新创建 Cards 来完成。

## 1. 为什么需要 PromptHint

当前 Grade-4 active set 同时存在：

```text
KV000424  cook  厨师
KV000805  cook  烹饪；煮
KV000816  over  在……远端/对面
KV000863  over  结束（的）
```

如果 Recognition 正面只有 `Word`，看到 `cook` / `over` 时无法知道要回忆哪个 target sense。

因此仅给这 4 个 Note 最小消歧：

```text
KV000424  cook  -> n.
KV000805  cook  -> v.
KV000816  over  -> 位置
KV000863  over  -> 结束
```

其他 Notes 的 `PromptHint` 必须为空。

## 2. 迁移前检查

先确认：

```text
Deck      = Klose-English::Vocabulary
Note Type = Klose Vocabulary
Card Type = Recognition
```

并先做 Anki Collection/Deck 备份。

不要删除已有 Notes；不要 Change Note Type；不要增加第二个 Card Type。

## 3. 在现有 Note Type 增加字段

Anki Desktop：

```text
Tools
→ Manage Note Types
→ Klose Vocabulary
→ Fields
→ Add
→ PromptHint
```

把字段 reposition 到 `Word` 后面。

最终字段顺序：

```text
1  NoteID
2  CanonicalWord
3  Word
4  PromptHint
5  British
6  American
7  MeaningPrimary
8  ExampleSentence
9  ExampleTranslation
10 LearnerLevel
11 Sources
12 SourceBooks
13 UserMemo
```

`UserMemo` 继续只在 Anki 本地维护，不从 repo CSV 导入。

## 4. 更新 Recognition Card Template

在同一个 `Klose Vocabulary` Note Type 中打开 Cards。

Recognition Front Template 使用 repo：

```text
anki/klose/anki/card_front.html
```

核心内容：

```html
<div class="word">{{Word}}</div>
{{#PromptHint}}
<div class="prompt-hint">{{PromptHint}}</div>
{{/PromptHint}}
```

因此普通卡仍只显示 `Word`；只有非空 PromptHint 才显示第二行提示。

Back Template 使用现有：

```text
anki/klose/anki/card_back.html
```

无需新增 Card Type。Back 中 `{{FrontSide}}` 会自然保留正面的 Word + optional PromptHint。

Styling 使用：

```text
anki/klose/anki/styling.css
```

其中 `.prompt-hint` 是小号、弱化样式，不应比 Word 更抢眼。

## 5. 模板迁移后的抽样检查

在真正导入 CSV 前，先确认：

- 原有 Cards 数量没有变化；
- Note Type 仍然叫 `Klose Vocabulary`；
- 每个 Note 仍然只有 1 张 `Recognition` Card；
- 原 NoteID 未变化；
- Card Info 中已有 Review History / Due / Interval 没有被重建。

此时旧 Notes 的 PromptHint 都为空是正常的。

## 6. 导入正式发布文件

只有 repo Release Gate 已 PASS 后才导入：

```text
anki/klose/publish/anki-import.csv
```

不要导入 `study.csv`。

导入要求：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing Notes  = Update
Match scope     = Note Type
第一字段         = NoteID
Tags            = Tags
```

检查字段 mapping 至少包括：

```text
NoteID            -> NoteID
CanonicalWord     -> CanonicalWord
Word              -> Word
PromptHint        -> PromptHint
British           -> British
American          -> American
MeaningPrimary    -> MeaningPrimary
ExampleSentence   -> ExampleSentence
ExampleTranslation-> ExampleTranslation
LearnerLevel      -> LearnerLevel
Sources           -> Sources
SourceBooks       -> SourceBooks
Tags              -> Tags
```

`UserMemo` 不映射。

导入后的目标：

```text
Total Notes / Cards = 638
```

其中原 518 NoteID 应原地更新，新增 120 个 NoteID 创建新 Notes。

## 7. 验证 PromptHint

Browser 中分别搜索 4 个 NoteID，确认：

```text
KV000424  PromptHint = n.
KV000805  PromptHint = v.
KV000816  PromptHint = 位置
KV000863  PromptHint = 结束
```

并抽查一个普通词：

```text
PromptHint = blank
```

Preview 应看到：

```text
cook
n.
```

或：

```text
over
结束
```

普通词仍只显示 Word。

## 8. 重置当前学习范围

当前 Klose 尚未产生真实 Review History，因此本次可以按明确 Learning Admission 做一次初始 active-set reset：

```text
1. Browser 选中 Klose Vocabulary 全部 638 Cards
2. Suspend 全部
3. 搜索：tag:learning::klose::grade4
4. 结果必须 = 221 Cards
5. 选中这 221 Cards
6. Toggle Suspend -> Unsuspend
```

最终：

```text
Total Cards       = 638
Unsuspended       = 221
Suspended / held  = 417
```

如果 `tag:learning::klose::grade4` 不是 221，不要继续学习，先回 repo / import mapping 排查。

## 9. 完成标准

```text
Note Type         = 原 Klose Vocabulary
Card Type         = 原 Recognition
Stable NoteID     = preserved
Card count        = 638
PromptHint nonempty = 4
Current Grade-4   = 221 unsuspended
Held library      = 417 suspended
FSRS history      = preserved
```

完成后，PromptHint 不再是“一次性迁移字段”，而成为长期 Note Type contract 的正常可选字段。未来新增同形异义 active Notes，只改 Learner Presentation + review + release，不再修改 Note Type schema。
