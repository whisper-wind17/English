# Klose Expression — Anki Note / Card Contract

本目录冻结 Klose Expressions 的长期 Anki 交互契约。Vocabulary 与 Expressions 使用独立 Note Type。

## Note Type / Deck

```text
Note Type = Klose Expression
Deck      = Klose-English::Expressions
Card Type = Production
```

长期保持 `1 Expression Note = 1 Card`。

## Note fields

字段顺序建议：

```text
ExpressionID
FunctionLabel
Prompt
PromptHint
Target
Pattern
MeaningUsage
Examples
LearnerLevel
LearningOrder
Sources
SourceBooks
```

`ExpressionID` 必须为第一字段，并长期稳定。

`Prompt` / `PromptHint` 使用语言中性字段名；不要改成 `ChinesePrompt`，因为 Front 语言会随 Learner Presentation 演进。

`LearningOrder` 是 curriculum/admission metadata，固定使用 6 位零填充字符串；它不属于 Identity，也不进入 Presentation fingerprint。

## Production contract

训练方向固定为：

```text
communicative intent / situation
→ active English production
```

正面显示：

```text
FunctionLabel
Prompt
PromptHint
```

正面不得显示 `Target`、`Pattern`、`MeaningUsage` 或 TTS，避免在主动回忆前泄露答案。

答案面显示：

```text
FrontSide
Target
Target TTS
Pattern
MeaningUsage
Examples
```

TTS 使用：

```html
{{tts en_US:Target}}
```

Examples 默认不自动播放。

## Front language policy

当前 Klose 使用：

```text
Stage A
中文短场景 / 交际意图
+ English minimal slot cue
→ English production
```

中文 Prompt 必须短，只负责建立 communicative intent，不应直接给出可逐词翻译的完整目标句。

推荐：

```text
【询问职业】
想知道同学妈妈的职业
person: your mother
```

不推荐：

```text
你妈妈做什么工作？
```

长期演进：

```text
Stage A — 中文短场景 / intent + English cue
Stage B — concise English intent + English cue
Stage C — English-only situation / context
```

迁移到下一阶段不按固定年龄或年级自动发生；以真实学习表现为依据。当英文 Front 不再显著增加无关阅读负担时，才调整 Learner Presentation。

Front 语言变化只修改 `Prompt / PromptHint` 等 Presentation 字段：

```text
ExpressionID 不变
CanonicalForm 不变
FSRS / Review History 不重建
Presentation fingerprint 更新并重新 review / approve
```

## Card-back micro-lesson

答案面同时支持两种情况：

```text
已学表达 → retrieval / consolidation
第一次见到的简单表达 → lightweight acquisition
```

因此 Back 保留最小 micro-lesson：

```text
Target
Pattern
简短 Meaning / Usage
1–2 个替换 Examples
TTS
```

不把卡片扩展为完整语法课。

## Presentation fingerprint v1

`expression-presentation-v1` 依次连接以下 UTF-8 字段，字段之间使用 ASCII Unit Separator `0x1F`，再计算 SHA-256：

```text
LearnerProfile
LearnerLevel
ExpressionID
Prompt
PromptHint
Target
Pattern
MeaningUsage
Examples
FunctionLabel
ContextNote
```

这些字段任一变化，旧 approval 失效。`LearningOrder` 不进入 fingerprint。

## First formal card

```text
ExpressionID  = KE000001
Function      = 询问职业
Pattern       = What's [person]'s job?
LearningOrder = 000001
```

Front：

```text
【询问职业】
想知道同学妈妈的职业
person: your mother
```

Target：

```text
What's your mother's job?
```

## First full import operational baseline

2026-09-06 用户已在 Anki Desktop 完成首次正式导入、排序、Deck Options 配置与同步。

已确认：

```text
Notes / Cards         = 66 / 66
LearningOrder         = 000001..000066
New #                 = 1..66, materialized only while cards were is:new
Preset                = Klose Expressions
New cards/day         = 2
Maximum reviews/day   = 9999
Learning steps        = 1m 10m
New card gather order = Ascending position
New card sort order   = Order gathered
New/review order      = Show after reviews
FSRS                  = ON
Desired retention     = 90%
FSRS parameters       = Default parameters
FSRS search scope     = deck:"Klose-English::Expressions" -is:suspended
Reschedule on change  = OFF
Sync                  = completed
```

这部分只记录首次运行时用户确认的 operational baseline。FSRS memory state / Due / Interval / Review History / Card State 仍以 Anki 为唯一真源；repo 不回写或重建这些状态。

后续只有尚未进入真实 Learning / Review 的 `is:new` Cards 才允许按 LearningOrder 初始化或调整 New #。一旦进入真实复习，不使用 repo 顺序重建其调度状态。
