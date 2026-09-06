# Grade-4 Expressions Pilot Review

当前首批 Grade-4 priority pilot 共 9 个 Stable Expressions。

状态：

```text
approved       = 1
model-reviewed = 8
LearningOrder  = 000001..000009
```

`model-reviewed` 只表示已按当前 Stage-A 卡片规则完成模型审校，不等于用户确认；只有 `approved` Presentation 才能进入 generated publish。

| Order | ID | Front intent | Cue | Target | Pattern | Review |
|---|---|---|---|---|---|---|
| 000001 | KE000001 | 想知道同学妈妈的职业 | person: your mother | What's your mother's job? | What's [person]'s job? | approved |
| 000002 | KE000002 | 介绍一个地方有什么 | thing: a playground | There is a playground. | There is a/an [singular noun]. | model-reviewed |
| 000003 | KE000003 | 提议和朋友一起做运动 | action: do some sports | Let's do some sports. | Let's [verb phrase]. | model-reviewed |
| 000004 | KE000004 | 想知道悉尼的天气 | place: Sydney | What's the weather like in Sydney? | What's the weather like in [place]? | model-reviewed |
| 000005 | KE000005 | 看到一件毛衣，想知道是谁的 | thing: sweater | Whose sweater is this? | Whose [noun] is this? | model-reviewed |
| 000006 | KE000006 | 今天想穿新衬衫，先征求妈妈同意 | action: wear this new shirt today | Can I wear this new shirt today? | Can I [verb phrase]? | model-reviewed |
| 000007 | KE000007 | 想知道现在几点了 |  | What time is it? | What time is it? | model-reviewed |
| 000008 | KE000008 | 吃饭时，想请别人把蔬菜递给你 | action: pass me the vegetables | Can you please pass me the vegetables? | Can you please [verb phrase]? | model-reviewed |
| 000009 | KE000009 | 吃饭时，问对方要不要刀叉 | thing: a knife and fork | Would you like a knife and fork? | Would you like [thing]? | model-reviewed |

Identity Review 中对 `EC0014` 做了一个明确修正：Candidate 的草案是 `Can I [verb phrase], please?`，正式 Identity 冻结为更通用的 `Can I [verb phrase]?`；`please` 作为可选礼貌成分放在 Usage 中，不作为 Identity 的强制组成部分。这与四年级教材中的 `Can I wear ...? / Can I watch ...? / Can I buy ...?` 一致。

下一次人工确认应以本文件和 `learner/current.csv` 为准。确认后刷新 Presentation Review 状态，再由 `tools/build_klose_expressions.py` 确定性生成 publish artifacts，并运行 `tools/check_klose_expressions_release_ready.py`。
