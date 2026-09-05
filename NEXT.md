# NEXT — Klose Learning

Last updated: 2026-09-06

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前任务继续读取：

```text
docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/rj_start1-grade4-upper-klose-expressions.csv
→ anki/klose/source_reference/rj_start1-grade4-upper-pattern-candidates.csv
```

Grade 1–3 实际教材词表核对后续继续读取：

```text
docs/SOURCE_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Current status — Grade-4 Vocabulary closed loop complete

Grade-4 Vocabulary 已完成从真实教材到 Anki Desktop 的完整闭环：

```text
Source / Edition / Occurrence
→ Sense-aware Identity / Stable NoteID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Release Gate
→ anki-import.csv
→ existing Note Type in-place update
→ Suspend / Unsuspend admission
→ LearningOrder → New Card Position
```

当前执行状态：

```text
Build Valid                 = yes
Content Releasable          = yes
Anki content updated        = yes
Learning Admitted           = yes
LearningOrder in repo       = yes
LearningOrder in Anki New # = yes
```

Repo baseline：

```text
inventory Notes        = 901
released / study       = 638
Grade-4 allowed        = 221
held library           = 417
model-reviewed         = 638
review pending         = 0
PromptHint nonempty    = 4
LearningOrder          = 000001..000221
held LearningOrder     = blank
Release Gate           = PASS
held IPA debt          = 99
```

正式 Anki artifact：

```text
anki/klose/publish/anki-import.csv
```

Anki Desktop 已实测：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

Klose 开始真实学习后，FSRS / Due / Interval / Review History / Card State 以 Anki 为唯一真源；已进入 Learning / Review 的 Cards 不再由 repo 重排。

---

## 2. Current Phase B — Expressions one-month pilot

当前优先任务切换为 **Expressions 长期系统的一月试运行**。

长期定位已经冻结：

```text
Vocabulary  = recognition of word / phrase / target sense
Expressions = active production from communicative intent / situation
```

Expressions 不是“教材句子收藏”，核心 Identity 是：

```text
Stable ExpressionID
+ Canonical English realization
+ Communicative Function
```

正式长期链路：

```text
Source Evidence / Learner Need
→ Expression Occurrence
→ Candidate Extraction
→ Expression Identity Resolution
→ Stable ExpressionID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Release Registry
→ deterministic publish
→ Expression Release Gate
→ Anki
→ Real-learning Feedback
```

Anki Expressions 可以同时承担：

```text
已有输入后的 retrieval / consolidation
+ 简单新表达的 lightweight acquisition
```

Meaningful input / interaction 仍是主要学习来源，但不是 Learning Admission 的硬前置条件。若一个新表达能通过卡片背面的简短 micro-lesson 清楚解释其含义、结构和用法，可以直接进入学习。

不为“是否第一次见”建立额外状态，也不区分第一次 Again 与遗忘后的 Again。`Again` 统一表示：当前还不能稳定主动产出该 Expression。

### Pilot implementation order

下一步按以下顺序执行：

```text
1. 建立 anki/klose/expressions/ bounded context
2. 冻结 Expression Registry / Occurrence / Mapping schema
3. 对四上现有 pattern candidates 做 dedup + identity resolution
4. 选取约 10–20 个高价值 Expression 作为 pilot batch
5. 建立 Learner Presentation / Review / Approval / Admission
6. 冻结 Expression LearningOrder
7. 实现 deterministic study.csv / anki-import.csv
8. 实现独立 Expression Release Gate
9. 冻结并创建 Anki schema
10. Klose 实际学习一个月
11. 基于真实数据决定是否扩量或调整 Presentation
```

当前不要把全部四上 candidates 直接导入 Anki。

### Pilot Anki direction

长期目标：

```text
Deck      = Klose-English::Expressions
Note Type = Klose Expression
Card      = Intent / Situation → English Production
```

正面优先采用：

```text
communicative intent / situation
+ minimal slot cue
```

避免长期形成完整“中文句子 → 英文翻译”的机械通路。

例如：

```text
【询问职业】
person: your mother

→ What's your mother's job?
```

Back 至少包含：

```text
Target
Canonical Pattern
简短 Meaning / Usage
1–2 个替换例子
TTS
```

这样既能支持第一次见到简单表达时的 micro-lesson，也能支持后续 retrieval / spacing。

### One-month evaluation

Pilot 期间重点观察：

```text
Again ratio
slot substitution success
transfer to unseen situations
whether recall depends on Chinese translation
pattern over-generalization
pronunciation / fluency issues
actual daily review load
real speaking / writing reuse when observable
```

不对 Again 做 acquisition-history 细分，也不额外分析“第一次 Again”。

核心评估问题：

```text
Klose 是只记住了卡片原句，
还是形成了可迁移、可主动调用的 expression pattern？
```

Pilot 的 `New/day` 暂不提前冻结。先建立正式 batch 和 Card Contract，再结合 Vocabulary 当前 `New/day=8` 与实际总复习负担确定保守初始值。

---

## 3. Deferred Phase A — reconcile actual Grade 1–3 textbooks

Grade 1–3 Source Reconciliation 暂后移，Expressions pilot 建立后继续。

目标仍是：

```text
Klose actual Grade 1/2/3 textbook vocabulary
→ capture SourceID / SourceEdition / Book / Unit / Order
→ reconcile existing source occurrences
→ sense-aware mapping to Stable NoteID
→ classify discrepancies
```

核心规则不变：

```text
Actual Textbook Evidence > third-party organized data
Source Grade ≠ LearnerLevel ≠ Learning Admission
```

Source Reconciliation 首先修正 source truth / provenance，不自动 Unsuspend 或扩大学习范围。

---

## 4. Real-learning feedback loop

Vocabulary 当前继续正常学习：

```text
New/day = 8
```

Vocabulary 与 Expressions 的真实学习状态都必须从 Anki 获取，不从 GitHub 推测 FSRS / Due / Interval / Review History。

Expressions pilot 上线后，需同时观察两个 Deck 的总复习负担，避免为了增加 production training 破坏 Vocabulary 的可持续性。

---

## 5. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源修正、presentation 修改或普通内容修正而变化；
- actual textbook evidence 优先于第三方来源，冲突先 reconciliation；
- Source Grade、LearnerLevel、Learning Admission 三者独立；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- Expression Occurrence 与 Expression Identity 分离，允许 many-to-many；
- Expression 的核心训练方向是 communicative intent → active English production；
- Anki Expressions 可承担简单新表达的轻量首次学习和后续 consolidation，但不替代主要的 meaningful input / interaction；
- 不为首次见过/首次 Again 建额外状态，Again 只表示当前未能稳定主动产出；
- 内容 fingerprint 变化后旧 approval 失效；LearningOrder 不进入内容 fingerprint；
- 只有仍为 `is:new` 的 Cards 才允许由 repo materialize New #；
- generated publish 文件禁止手工修改；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。

---

## Deferred / technical debt

- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：未来对应 Note admission 前补齐并 re-review；当前 held 不阻塞学习。
- Grade 1–3 actual source reconciliation：Expressions pilot 建立后继续。
- Grade 5/6 actual source reconciliation：Grade 1–3 与 Expressions 稳定后再处理。
