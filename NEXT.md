# NEXT — Klose Learning

Last updated: 2026-09-06

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Expressions 任务继续读取：

```text
docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/expressions/review/grade3-grade4-baseline.md
→ anki/klose/expressions/review/identity_resolution.csv
→ anki/klose/expressions/review/full-baseline-review.md
→ anki/klose/expressions/master/expression_registry.csv
→ anki/klose/expressions/master/expression_occurrences.csv
→ anki/klose/expressions/master/source_expression_map.csv
→ anki/klose/expressions/learner/current.csv
→ anki/klose/expressions/learner/learning_admission.csv
→ anki/klose/expressions/learner/presentation_review_registry.csv
→ anki/klose/expressions/master/release_registry.csv
→ anki/klose/expressions/anki/README.md
→ anki/klose/expressions/publish/anki-import.csv
```

不要仅凭聊天历史推测当前状态。

---

## 1. Vocabulary status

Grade-4 Vocabulary 已闭环并正常学习：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

FSRS / Due / Interval / Review History / Card State 继续以 Anki 为唯一真源。

---

## 2. Expressions source / identity baseline

当前复习范围只纳入 Klose 已学过的三、四年级实际教材 Expressions；一年级、二年级暂不复习。

```text
Grade 3 Source Occurrences = 94
Grade 4 Source Occurrences = 72
Total Source Occurrences   = 166

Curated Pattern Candidates = 64
Stable Expressions          = 66
Grade-4 priority            = 37
Grade-3-only                = 29
LearningOrder               = 000001..000066
```

学习顺序已经冻结：

```text
Grade 4 related first
→ Grade 3 only second
```

对应：

```text
KE000001..KE000037  = Grade-4 priority
KE000038..KE000066  = Grade-3 only
```

跨年级相同 Pattern 只学习一次，并归入 Grade-4 priority block。

64 Candidate 最终得到 66 Stable Expressions，是因为 Identity Review 明确拆分了两个 Candidate：

```text
EC0035
→ It's time for [noun].
→ It's time to [verb].

EC0058
→ Excuse me?   # 没听清时请求重复
→ Excuse me.   # 礼貌引起注意
```

这两个 split 遵守 `CanonicalForm + CommunicativeFunction` 身份规则，不是重复制卡。

其他显式调整：

```text
What's this? / What's that? → What's [demonstrative]?
Can I [verb phrase], please? → Can I [verb phrase]?  # please 可选
It's [weather adjective]... → It's [weather description]...
What about [thing]? → formal ExpressionType=slot_frame
```

完整 Identity 决策：

```text
anki/klose/expressions/review/identity_resolution.csv
```

---

## 3. Full 66-card Learner Presentation generated

全部 66 个 Stable Expressions 已生成当前 Stage-A Learner Presentation，并已建立 source provenance / admission / LearningOrder。

Front 当前统一采用：

```text
中文短场景 / communicative intent
+ English minimal slot cue
→ active English production
```

中文只建立意图，不直接提供可逐词翻译的完整中文目标句。

长期演进：

```text
Stage A — 中文短场景 + English cue
→ Stage B — concise English intent + English cue
→ Stage C — English-only situation / context
```

语言升级只修改 Learner Presentation；Stable ExpressionID、CanonicalForm 和 Anki FSRS / Review History 不变。Presentation 变化后 fingerprint 必须重新 review。

Back 保持最小 micro-lesson：

```text
Target + TTS
Pattern
Meaning / Usage
1–2 Examples
```

完整 66 张卡的 review sheet：

```text
anki/klose/expressions/review/full-baseline-review.md
```

---

## 4. Review / release state

当前：

```text
approved       = 9   # KE000001..KE000009，用户已明确确认
model-reviewed = 57  # KE000010..KE000066，已生成并模型审校
admitted       = 66
Anki Updated   = no
```

`model-reviewed != approved`。后 57 张虽然已经生成完整卡片 Presentation，但在用户最终 batch approval 前不得进入正式 full import artifact。

因此当前 generated publish 仍只包含已批准的前 9 张：

```text
anki/klose/expressions/publish/study.csv
anki/klose/expressions/publish/anki-import.csv
```

这不是缺失；Release Gate 正在阻止未经明确批准的 57 张 draft 泄漏到 Anki。

当前不要导入这个 9-card artifact，因为用户已经决定等全部卡片完成后一次性导入。

---

## 5. Deterministic publish / release gate

Expressions 生成链：

```text
upstream registries
→ tools/build_klose_expressions.py
→ publish/study.csv
→ publish/anki-import.csv
→ tools/check_klose_expressions_release_ready.py
```

Release Gate 已扩展到完整 Grade 3–4 baseline，验证：

- 64 Candidate 都有显式 Identity Resolution；
- 66 Stable ExpressionID 唯一且 active；
- CreatedFromOccurrence 均存在 confirmed source mapping；
- Grade-4 priority 必须有 Grade-4 source；
- Grade-3-only 不得混入 Grade-4 source；
- LearningOrder 六位、唯一、连续；
- Grade-4 block 必须完整位于 Grade-3 block 之前；
- current Presentation fingerprint 必须与 review registry 一致；
- `model-reviewed` draft 必须保持 `pending / pending`；
- approved Expression 才能进入 generated publish；
- `study.csv` / `anki-import.csv` 必须完全由上游确定性推导。

Generated publish 文件禁止手工维护。

---

## 6. NEXT TASK — final batch approval, then one full import artifact

下一步不是 Anki 导入，而是完成剩余 57 张的最终 batch review：

```text
KE000010..KE000066
```

以：

```text
anki/klose/expressions/review/full-baseline-review.md
```

为人工 review 入口。

用户确认后：

```text
ReviewStatus → approved
PresentationStatus → approved
→ deterministic rebuild
→ study.csv / anki-import.csv = 66 cards
→ full Expression Release Gate
→ 首次 Anki Desktop 导入
```

用户计划等全部卡片 release-ready 后再一次性导入，因此不要提前执行 9-card import。

---

## 7. First Anki import target state

最终首次导入仍使用：

```text
Deck      = Klose-English::Expressions
Note Type = Klose Expression
Card Type = Production
```

正式唯一导入文件：

```text
anki/klose/expressions/publish/anki-import.csv
```

待 full batch approval 后，该文件应包含：

```text
KE000001..KE000066
LearningOrder 000001..000066
```

导入后仅对 `is:new` Cards 按 LearningOrder materialize New #；Anki 继续作为 FSRS / Due / Interval / Review History / Card State 真源。

`New/day` 到首次正式导入时再结合 Vocabulary `New/day=8` 与实际总负担设置。

---

## 8. One-month evaluation

只观察有决策价值的指标：

```text
Again ratio
slot substitution success
transfer to unseen situations
pattern over-generalization
pronunciation / fluency issues
actual daily review load
```

核心问题：Klose 是记住了一条原句，还是获得了可迁移、可主动调用的 Expression。

不记录首次见过 / 首次 Again 等细粒度 acquisition history。

---

## 9. Deferred work

- Grade 1–3 Vocabulary actual-source reconciliation：Expressions 首次正式导入后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Expression Identity 分离；
- Expression Identity 以 `CanonicalForm + CommunicativeFunction` 判断；同 surface form 不同 function 必须允许 split；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- Expression 训练方向固定为 communicative intent → active production；
- 简单新 Expression 可以通过 Back micro-lesson 首次学习；
- Grade-4-related Expressions 当前优先于 Grade-3-only Expressions；
- Front 语言从中文支撑逐步演进到 English-only，但只修改 Presentation；
- `model-reviewed` 不等于人工 `approved`；
- LearningOrder 不进入内容 fingerprint；
- generated publish 文件禁止手工维护，只能由确定性生成链得到；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
