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
→ anki/klose/expressions/review/grade4-pilot-review.md
→ anki/klose/expressions/master/expression_registry.csv
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

## 2. Expressions source baseline

当前复习范围只纳入三、四年级实际教材 Expressions；一年级、二年级暂不复习。

```text
Grade 3 Source Occurrences = 94
Grade 4 Source Occurrences = 72
Total                      = 166

Curated Pattern Candidates = 64
Grade-4 priority block     = 36
Grade-3-only block         = 28
```

学习顺序冻结为：

```text
Grade 4 related first
→ Grade 3 only second
```

跨年级相同 Pattern 只学习一次，并归入 Grade-4 priority block。

---

## 3. Grade-4 pilot — 9 cards approved and release-ready

首批 Grade-4 priority pilot 已冻结 9 个 Stable Expressions：

```text
KE000001  What's [person]'s job?
KE000002  There is a/an [singular noun].
KE000003  Let's [verb phrase].
KE000004  What's the weather like in [place]?
KE000005  Whose [noun] is this?
KE000006  Can I [verb phrase]?
KE000007  What time is it?
KE000008  Can you please [verb phrase]?
KE000009  Would you like [thing]?
```

LearningOrder：

```text
000001..000009
```

2026-09-06 用户已确认整个 9-card pilot Presentation：

```text
approved       = 9
model-reviewed = 0
admitted       = 9
publishable    = 9
release-ready  = 9
```

`EC0014` 已显式从 Candidate 草案 `Can I [verb phrase], please?` 修正并冻结为正式 Identity `Can I [verb phrase]?`；`please` 是可选礼貌成分，不属于 Identity 的强制部分。

---

## 4. Front / Back policy

当前 Front 使用 Stage A：

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

---

## 5. Deterministic publish / release status

Expressions 独立生成链：

```text
upstream registries
→ tools/build_klose_expressions.py
→ publish/study.csv
→ publish/anki-import.csv
→ tools/check_klose_expressions_release_ready.py
```

当前已根据 9 个 approved Presentation 重新生成 publish artifacts；内容为 `KE000001..KE000009`，顺序 `000001..000009`。

正式导入文件：

```text
anki/klose/expressions/publish/anki-import.csv
```

当前状态：

```text
Build Valid        = yes
Content Releasable = yes
Anki Updated       = no
Learning Admitted  = yes
```

不要手工修改 `publish/study.csv` 或 `publish/anki-import.csv`；后续 Presentation / Admission 变化后仍通过生成链重建。

---

## 6. NEXT TASK — first Anki import

下一步在 Anki Desktop 完成首次 Expressions 建库：

```text
1. 创建/确认 Deck: Klose-English::Expressions
2. 创建/确认 Note Type: Klose Expression
3. 按 anki/klose/expressions/anki/README.md 配置字段、Production Card template、styling
4. 导入 anki/klose/expressions/publish/anki-import.csv
5. 仅对 is:new 卡按 LearningOrder materialize New #
6. Sync 到 AnkiWeb / iPad
7. 开始 one-month pilot
```

Anki 是 FSRS / Review History / Due / Card State 真源；repo 不重建这些状态。

Pilot `New/day` 尚未冻结。因为首批只有 9 张，可以在首次导入时先采用较低的新卡负担，再根据 Vocabulary `New/day=8` 与首周实际 review load 调整；不要为了尽快清空 9 张而一次性全部引入。

---

## 7. One-month evaluation

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

## 8. Deferred work

- Grade-3-only Expressions：Grade-4 pilot 进入真实学习后再继续正式 Identity / Presentation；
- Grade 1–3 Vocabulary actual-source reconciliation：Expressions pilot 建立后继续；
- Grade 5/6 actual source reconciliation：后续处理；
- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：对应 Note admission 前再补齐并 re-review。

---

## 9. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Expression Identity 分离；
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
