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
你刚认识一个同学，想了解他妈妈的职业。
person: your mother
```

Target：

```text
What's your mother's job?
```
