# Klose Expressions System

本文定义教材 Useful Expressions / 常用表达法的长期处理方式。Expressions 与 Vocabulary 是不同 Learning Object，不能因为都来自英语教材就共用一套 Note 语义。

## 1. 三层模型

```text
Raw Expression
→ Pattern Candidate
→ Released Expression
```

### Raw Expression

教材原句与教材译文，属于 Source Fact，100%保留。

### Pattern Candidate

从原句中抽取可复用的 communicative pattern / sentence frame，属于 derived curation，不是教材原文。

例如：

```text
What's your mother's job?
→ What's [person]'s job?

What's the weather like in Sydney?
→ What's the weather like in [place]?

Whose sweater is this?
→ Whose [noun] is this?
```

### Released Expression

只有高频、可迁移、适合 Klose 主动表达的 pattern 才可能进入正式学习系统。

## 2. 不机械制卡

禁止：

```text
一条教材原句 = 一张 Anki Card
```

上下文依赖强、只在故事中自然的句子应保留为 Source Fact，但不一定值得长期记忆。

筛选重点：

- communicative intent 清晰；
- pattern 可替换 slot；
- 在多个真实场景可迁移；
- 适合当前 LearnerLevel；
- 不只是某篇课文中的一次性叙述。

## 3. 与 Vocabulary 的边界

Vocabulary：

```text
word / phrase / target sense
```

Expressions：

```text
communicative function / reusable structure
```

完整表达法不得塞进 `Klose Vocabulary` 破坏 `1 Note = 1 target sense` 的 Vocabulary Identity。

未来若正式发布 Expressions，应使用独立 Note Type 和独立 review contract；是否使用独立 Deck 在正式设计时再决定，不在 Source Capture 阶段提前冻结。

## 4. Context Vocabulary

Useful Expressions 还提供一类重要证据：

```text
Context Vocabulary
```

即某个词未列入教材 Core Vocabulary，但真实出现在课文/表达法中。

它可以用于：

- 判断 Klose 当前教材已暴露过哪些词；
- 控制 LearnerLevel=4 例句的词汇难度；
- 发现 Source Edition 差异；
- 后续扩展 Vocabulary candidate。

但：

```text
Context Vocabulary ≠ Core Vocabulary
```

不能仅因出现在一句表达法中就自动 release 成 Vocabulary Note。

## 5. LearnerLevel

Expression 的难度同样由 LearnerLevel 决定，而不是 Source Grade。

```text
Source Grade = 教材在哪里出现
LearnerLevel = Klose 今天以什么难度学习
```

未来 Klose 即使提前学习 Grade 5/6 的 expression，也可以继续使用 LearnerLevel 4 presentation。

## 6. 未来 Anki 交互方向

若以后发布 Expression Card，优先训练主动输出，而不是被动识别。例如：

```text
Front:
“询问某地天气”
地点：Sydney

Back:
What's the weather like in Sydney?
TTS
```

或者：

```text
Front:
“这是谁的毛衣？”

Back:
Whose sweater is this?
```

这是设计方向，不是当前已冻结的 Card Contract。

## 7. 当前状态

四年级上已经保存：

```text
anki/klose/source_reference/rj_start1-grade4-upper-klose-expressions.csv
anki/klose/source_reference/rj_start1-grade4-upper-pattern-candidates.csv
```

当前全部 pattern 仍为 candidate，不进入 Anki。

动态状态和下一步以根目录 `NEXT.md` 为准。
