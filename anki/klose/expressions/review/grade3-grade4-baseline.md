# Grade 3–4 Expression Candidate Baseline

Scope: Klose 实际使用教材的三年级上/下、四年级上/下 Useful Expressions。

Source inputs:

```text
anki/klose/source_reference/rj_start1-grade3-klose-expressions.csv  # 94 occurrences
anki/klose/source_reference/rj_start1-grade4-klose-expressions.csv  # 72 occurrences
```

Total Source Occurrences: **166**

本文件记录从 Source Fact 到 Pattern Candidate 的第一次统一整理。它不是正式 Expression Registry，也没有分配 Stable ExpressionID。

## Result

```text
Source Occurrences         = 166
Curated Pattern Candidates = 64
core                       = 38
secondary                  = 26
pilot_candidate            = 19
```

详细结构化结果：

```text
anki/klose/expressions/review/candidate_registry.csv
```

## Curation rules

本轮只保留值得主动产出的 communicative production units：

- 多个教材原句如果表达同一 communicative function + canonical pattern，合并为一个 Candidate；
- 问句和答句承担不同 production function 时保留为不同 Candidate；
- 一次性叙述、纯课文事实、迁移价值低的完整句保留在 Source Reference，不机械抽成卡；
- `Can I ...?`、`Let's ...`、`What are these?`、`Would you like ...?` 等跨册或跨年级重复表达已合并；
- 固定社交表达如 `Here you are.`、`You're welcome.` 仍可成为 Expression，因为目标是主动调用，而不是必须具有 slot；
- 当前 CandidateKey `ECxxxx` 只是 review 阶段临时编号，不具备 Stable ExpressionID 语义。

## Examples of cross-source merge

```text
Can I use your eraser, please?       # Grade 3 lower
Can I wear this new shirt today?     # Grade 4 upper
Can I buy a new pair?                # Grade 4 lower

→ Can I [verb phrase], please?
```

```text
Let's go to the zoo!                 # Grade 3 upper
Let's draw some ... birds.           # Grade 3 upper
Let's do some sports.                # Grade 4 upper
Let's buy trousers.                  # Grade 4 lower
Let's feed the chickens.             # Grade 4 lower

→ Let's [verb phrase].
```

```text
What are these?                      # Grade 3 lower
What are these?                      # Grade 4 lower

→ one Candidate
```

## Pilot candidate selection

当前标记 19 个 `PilotCandidate=yes`，覆盖三类能力：

```text
basic social / personal information
request / preference / shopping
Grade-4 productive structures: job / existence / weather / ownership / time
```

Pilot 标记只是下一步 identity resolution 的输入，不表示已经 release，也不表示已经允许进入 Anki。

## Explicitly not done yet

本阶段没有：

```text
分配 KE000001...
冻结 Expression Identity
生成 Learner Presentation
生成 LearningOrder
生成 Anki Card
修改 Anki
```

下一步应先对 19 个 pilot candidates 做 identity review，冻结 CanonicalForm / FunctionKey / ExpressionType / SlotSchema，再分配首批 Stable ExpressionID。
