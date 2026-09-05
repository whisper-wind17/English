# Anki 一次性迁移：LearningOrder → New Card Position

本 SOP 处理当前 Grade-4 Vocabulary 的学习顺序迁移。

目标不是修改 Stable NoteID，也不是让 GitHub 接管 Anki 的 Due / FSRS，而是把 repo 中明确的 curriculum order 一次性 materialize 为 Anki 的 New Card Position。

## 1. 两种“顺序”必须区分

```text
LearningOrder
= GitHub 中的教学顺序意图
= Learning Admission metadata

New Card Position / New #
= Anki 中当前 New Card 的物理位置
= Anki state
```

`LearningOrder` 的正式序列化固定为 6 位十进制零填充字符串：

```text
000001 .. 999999
```

这样未来扩展到数千/数万学习单元时不需要再做 3 位 → 4 位 → 5 位迁移，并保证 Anki 文本排序与数值排序一致。

当前 Grade-4：

```text
allowed Notes  = 221
LearningOrder  = 000001..000221
held Notes     = 417
LearningOrder  = blank
```

顺序规则：

```text
四年级上 Unit 1 -> Unit 6
-> 四年级下 Unit 1 -> Unit 6
-> Unit 内按教材 Order
```

前 8 个应为：

```text
000001 PE
000002 job
000003 doctor
000004 farmer
000005 nurse
000006 office worker
000007 factory worker
000008 busy
```

## 2. 为什么不能只保留当前 New #

现有 638 Cards 由历史 release 演进而来。即使当前 221 张 active Cards 正确，原 New # 仍可能继承旧 Note 创建顺序，因此第一天出现 `there / chair / desk ...`，而不是教材 Unit 1 顺序。

仅在 Anki 手工 Reposition 可以解决一次，但 repo 无法解释或重建教学顺序。因此需要显式 `LearningOrder`。

## 3. Note Type schema migration

在现有：

```text
Klose Vocabulary
```

中增加字段：

```text
LearningOrder
```

放在 `LearnerLevel` 后、`Sources` 前。

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
11 LearningOrder
12 Sources
13 SourceBooks
14 UserMemo
```

不要新建 Note Type / Card Type，不修改模板显示，不删除 Notes。

## 4. 导入最新 release

先确认 repo Release Gate PASS，再导入：

```text
anki/klose/publish/anki-import.csv
```

导入：

```text
Note Type       = Klose Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Identity        = NoteID
```

新增 mapping：

```text
LearningOrder -> LearningOrder
```

`UserMemo` 仍映射为 Nothing。

预期：

```text
Total Cards = 638
221 active Notes have LearningOrder 000001..000221
417 held Notes have blank LearningOrder
```

这次导入只更新 Note 字段，不应改变 Card identity / FSRS / Review History。

## 5. Reposition 前置条件

本次只对尚未开始真实 Review History 的 current Grade-4 New Cards执行初始化排序。

Browser 搜索：

```text
tag:learning::klose::grade4 -is:suspended is:new
```

必须得到：

```text
221 Cards
```

如果不是 221，停止并排查，不要继续 Reposition。

## 6. 按 LearningOrder 排序

在 Browser 中显示 `LearningOrder` 列，并按升序排序。

因为值固定 6 位零填充：

```text
000001, 000002, ... 000009, 000010, ... 000221
```

文本排序与数值排序都会得到同一顺序。

最上面的 8 张必须是：

```text
PE
job
doctor
farmer
nurse
office worker
factory worker
busy
```

## 7. Materialize 到 New #

保持上述 221 张按 `LearningOrder` 升序显示，全选：

```text
Ctrl+A
-> Cards
-> Reposition
```

设置：

```text
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

执行后，这 221 张 current Grade-4 New Cards 应对应：

```text
LearningOrder 000001 -> New #1
LearningOrder 000002 -> New #2
...
LearningOrder 000221 -> New #221
```

未选中的 held New Cards 会被移到后续位置；它们本身处于 Suspended，不影响当前学习。

## 8. 验收

仍搜索：

```text
tag:learning::klose::grade4 -is:suspended is:new
```

按 `Due / New #` 升序后，前 8 张必须是：

```text
PE
job
doctor
farmer
nurse
office worker
factory worker
busy
```

同时确认：

```text
Total Cards = 638
Unsuspended = 221
Suspended   = 417
```

## 9. 长期规则

`LearningOrder` 是教学计划元数据，不进入 learner content fingerprint。

未来：

- 修改词义 / IPA / Example / PromptHint -> 需要内容 re-review；
- 修改 LearningOrder -> 不需要重新审校内容，但必须通过 Admission / Release Gate；
- LearningOrder 的正式存储格式固定为 6 位 `000001..999999`，不得随词库规模改变位宽；
- 已经进入真实 Learning / Review 的 Card，不因为后续 curriculum order 变化而重排其 FSRS / Due；
- LearningOrder 主要用于尚未学习的新卡准入和初始化 sequencing。
