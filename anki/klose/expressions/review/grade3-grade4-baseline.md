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

按当前学习顺序规则，64 个 Candidate 分成：

```text
Grade-4 priority block = 36  # SourceGrades=4 或 3|4
Grade-3-only block      = 28  # SourceGrades=3
Total                   = 64
```

凡一个 Pattern 同时在三、四年级出现，归入 Grade-4 priority block，不在三年级再次重复学习。

因此未来正式 LearningOrder 固定采用：

```text
Grade 4 related first
→ Grade 3 only second
```

Candidate Registry 当前文件行序只是 review 顺序，不等于正式 LearningOrder；LearningOrder 只在 Identity / Admission 冻结后写入正式 learner state。

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
→ Grade-4 priority block
```

```text
Let's go to the zoo!                 # Grade 3 upper
Let's draw some ... birds.           # Grade 3 upper
Let's do some sports.                # Grade 4 upper
Let's buy trousers.                  # Grade 4 lower
Let's feed the chickens.             # Grade 4 lower

→ Let's [verb phrase].
→ Grade-4 priority block
```

```text
What are these?                      # Grade 3 lower
What are these?                      # Grade 4 lower

→ one Candidate
→ Grade-4 priority block
```

## Pilot candidate selection

当前标记 19 个 `PilotCandidate=yes`，覆盖三类能力：

```text
basic social / personal information
request / preference / shopping
Grade-4 productive structures: job / existence / weather / ownership / time
```

Pilot 实际 LearningOrder 也必须遵循 Grade 4 related → Grade 3 only。

Pilot 标记只是下一步 identity resolution 的输入，不表示已经 release，也不表示已经允许进入 Anki。

## Expected card count

当前 candidate baseline 对应的理论上限是 **64 张 Expression Cards**，前提是 Identity Review 后没有进一步 merge / reject。

正式卡片数量只有在 Identity Review 完成后才能冻结；若某些 Candidate 被判定重叠、迁移价值不足或不适合独立 active-production card，最终数量可以小于 64，但不会因为同一 Pattern 在三、四年级重复出现而创建重复卡。

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

下一步应先对 pilot candidates 做 identity review，冻结 CanonicalForm / FunctionKey / ExpressionType / SlotSchema，再分配首批 Stable ExpressionID；分配后的 LearningOrder 必须把 Grade-4 priority block 放在最前面。
