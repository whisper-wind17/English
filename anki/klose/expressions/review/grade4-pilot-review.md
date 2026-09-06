# Grade-4 Expressions Pilot Review

当前首批 Grade-4 priority pilot 共 **9 个 Stable Expressions**，已由用户整体确认。

状态：

```text
approved       = 9
model-reviewed = 0
LearningOrder  = 000001..000009
publishable    = 9
release-ready  = 9
```

| Order | ID | Front intent | Cue | Target | Pattern | Review |
|---|---|---|---|---|---|---|
| 000001 | KE000001 | 想知道同学妈妈的职业 | person: your mother | What's your mother's job? | What's [person]'s job? | approved |
| 000002 | KE000002 | 介绍一个地方有什么 | thing: a playground | There is a playground. | There is a/an [singular noun]. | approved |
| 000003 | KE000003 | 提议和朋友一起做运动 | action: do some sports | Let's do some sports. | Let's [verb phrase]. | approved |
| 000004 | KE000004 | 想知道悉尼的天气 | place: Sydney | What's the weather like in Sydney? | What's the weather like in [place]? | approved |
| 000005 | KE000005 | 看到一件毛衣，想知道是谁的 | thing: sweater | Whose sweater is this? | Whose [noun] is this? | approved |
| 000006 | KE000006 | 今天想穿新衬衫，先征求妈妈同意 | action: wear this new shirt today | Can I wear this new shirt today? | Can I [verb phrase]? | approved |
| 000007 | KE000007 | 想知道现在几点了 |  | What time is it? | What time is it? | approved |
| 000008 | KE000008 | 吃饭时，想请别人把蔬菜递给你 | action: pass me the vegetables | Can you please pass me the vegetables? | Can you please [verb phrase]? | approved |
| 000009 | KE000009 | 吃饭时，问对方要不要刀叉 | thing: a knife and fork | Would you like a knife and fork? | Would you like [thing]? | approved |

Identity Review 中对 `EC0014` 做过显式修正：Candidate 草案 `Can I [verb phrase], please?` 冻结为更通用的 `Can I [verb phrase]?`；`please` 作为可选礼貌成分放在 Usage 中，不作为 Identity 的强制组成部分。

Front 当前统一采用 Stage A：

```text
中文短场景 / communicative intent
+ English minimal slot cue
→ active English production
```

长期仍按 Stage A → Stage B → Stage C 演进；Front 语言升级只修改 Learner Presentation，不改变 Stable ExpressionID 或 Anki FSRS / Review History。

用户于 2026-09-06 明确确认 `KE000002..KE000009` 整批通过。Presentation fingerprints 保持 current，ReviewStatus 已升级为 `approved`。

随后按 Expressions 确定性生成逻辑重新生成：

```text
anki/klose/expressions/publish/study.csv
anki/klose/expressions/publish/anki-import.csv
```

当前 9 张均为 `PublishStatus=generated / ReleaseStatus=ready`。Anki 尚未更新；下一步是在 Desktop 创建/确认 `Klose Expression` Note Type 后导入正式 `anki-import.csv`。
