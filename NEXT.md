# NEXT — Klose Learning

Last updated: 2026-09-08

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary Stage A 继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
→ anki/klose/third_party_vocabulary/learner/learner_vocabulary_preview.csv
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine_view.csv
```

动态进度只以 repo 当前文件为准。

---

## 1. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 identities
Expressions Stable = 66
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus / Stage A

```text
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary Identity View
→ current Learner Admission gate
→ Klose learner-stage vocabulary view
```

Durable truth 必须分层：

```text
review/identity_decisions.csv
= Identity content truth

learner/grammar_form_quarantine.csv
= current Klose Learner Admission gate
```

Reviewed Identity decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

Enabled adapters：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
```

仍处于 Stage A：不得 mint Stable ThirdPartyID，不得运行 Stage-B Klose diff，不得修改 Klose Master/Learner/Publish/Anki。

---

## 3. Current checkpoint — POLICY REVIEW THROUGH BATCH #5 CHECKPOINTED

当前 six-adapter corpus：

```text
Enabled adapters                   = 6
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2102
Identity-level Vocabulary Preview  = 1005
Review/blocker surfaces            = 970
Evidence-changed surfaces          = 875
Multipart resolved                 = 9
```

Current learner-stage projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 993
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 34
Explicit decision-bound past-form requirements = 11
```

Identity / Learner separation 仍成立：

```text
Identity Preview 1005
→ learner grammar-stage gate
→ Learner Preview 993
```

被 gate 的 12 个 Identity 没有被删除，只是当前不进入 Klose learner-facing view。

---

## 4. Grammar-stage quarantine — FROZEN

Klose 当前尚未系统学习过去式、过去分词/完成时，因此 pure one-word past/past-participle forms 暂不进入 learner vocabulary。

```text
Identity resolved
≠ current Learner Admission
```

典型：

```text
went → go                 Identity resolved；learner quarantine
broke → break#damage      Identity resolved；learner quarantine
had / made / took / were  pedagogical Identity 可保留；learner quarantine
```

不得按字面形态粗暴过滤：

```text
lost   = 迷路的 / 丢失的      → lexicalized adjective，保留
scared = 害怕的；受惊的       → 保留
broken = 坏的；破损的         → 保留
```

普通复数、三单、`-ing` 不自动 quarantine。

Homograph 必须 decision-scoped：

```text
left#direction   → 保留
left#leave-past  → quarantine

saw#tool         → 保留
saw#see-past     → quarantine
```

Machine checker 不得把第三方 dictionary/free-text Definition 当 grammar identity truth。

---

## 5. Completed deterministic policy batches after grammar-gate baseline

Grammar-gate baseline：

```text
Decisions 2098 / Identity Preview 985 / Learner Preview 979
Blockers 1010 / Evidence-changed 911 / Multipart 7
```

### Batch #2 — 10 surfaces

```text
swam / taught / told / took / went / were / won / wore / wrote / goes
```

完成 exact-evidence rebind；过去式继续由 learner gate 隔离，`goes` 不 quarantine。

### Batch #3 — 8 surfaces

```text
noodles / sweets / thanks / women / sports / found / had / left
```

关键边界：`left` 完整拆为 direction 与 leave-past 两个 subgroup。`left#leave-past` 作为高频 pedagogical form 在 Identity 层显式 keep，当前 learner gate 精确隔离；不绕过 evidence-stale canonical `leave`。

最终：

```text
Identity Preview 993 / Learner Preview 983 / Blockers 992
Evidence-changed 894 / Multipart 8
```

### Batch #4 — 10 surfaces

```text
lost / made / said / saw / spent / spoke / er / hasn't / children / men
```

关键边界：

```text
lost      → lexicalized adjective，保留
saw       → saw#tool + saw#see-past multipart
saw#see-past → learner quarantine
er        → 犹豫语气词，route-expression；第三方 ER 缩写释义为 glossary noise
hasn't    → grammatical contraction，route-expression
children / men → pedagogically salient irregular plural，keep
```

最终：

```text
Identity Preview 999 / Learner Preview 987 / Blockers 982
Evidence-changed 886 / Multipart 9
```

### Batch #5 — 12 surfaces

```text
you're / am / can't / cd / dvd / he's / i'm / it / it's / mm / mr / ms
```

Adjudication：

```text
route-expression = you're / can't / he's / i'm / it's / mm
keep-vocabulary  = am / cd / dvd / it / mr / ms
```

关键边界：

- contractions 属 grammar presentation / Expressions；
- `mm` 由教材 food/tasting neighborhood 绑定为反应语气词，millimetre 等释义为 glossary noise；
- `CD / DVD / Mr / Ms` 虽是 abbreviation，但教材绑定明确小学 lexical concept，保留 Vocabulary；
- `am` 是高频 present be-form pedagogical Identity，不属于 past-form quarantine；
- `it` 是代词，技术缩写释义不作为 source identity truth。

最终 successful workflow：

```text
run 34186941286 / #198 = SUCCESS
batch commit = 767c367ea580e4e20beb8f34fbedf2dd11db1466
bot persist  = 677bbc65657ed5eaa9cfb8e5f118715f0c741532
```

Batch #5 validation：

```text
selected active batch closure              = 100%
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1005 / 1005
Third-party learner-stage quarantine       = PASS
past-form leak into learner preview        = NO
lexicalized adjective/noun over-gating     = NO
homograph decision-scope gate              = ENFORCED
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
transient batch files removed              = YES
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

Cumulative delta from grammar-gate baseline：

```text
Identity Preview   985  → 1005   (+20)
Learner Preview    979  →  993   (+14)
Blockers          1010  →  970   (-40)
Evidence-changed   911  →  875   (-36)
Multipart            7  →    9   (+2)
```

---

## 6. Identity / Learner separation — HARD INVARIANT

```text
Source Fact
≠ Vocabulary Identity
≠ Learner Admission
≠ Anki learning state
```

因此：

```text
reuse-identity      ≠ 当前必须学习
keep-identity       ≠ 当前必须学习
learner quarantine  ≠ Identity unresolved
```

Future Stage B 不能直接消费 `unified_vocabulary_preview.csv` 作为当前学习清单；Identity reconciliation 后必须再经过 learner-stage gate。

---

## 7. V4 learner-first Identity policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频 pedagogical form
→ Identity 层可显式 keep，必须有 rationale
→ 是否当前学习仍由 Learner Admission 独立决定

显式 slot / reusable grammar pattern / communicative formula
→ route-expression

event / tense-specific source chunk
→ source-only

多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

Contractions 默认属于 grammar presentation / Expression；lexical abbreviation 只有 source 能绑定明确小学概念时才 keep。

所有 reviewed Identity decision 仍以 exact current `OccurrenceKeys` 为 validity boundary。

---

## 8. High-throughput execution mechanism — FROZEN

```text
review_bundle.csv
→ normalize lanes
→ decision proposals
→ deterministic next_batch.json
→ batch_manifest.json + decision_updates.csv
→ manifest closure check
→ apply/build Identity view
→ build/check learner-stage view
→ core Completion Recheck
→ batch Completion Recheck
→ Klose isolation
→ bot persist
```

硬规则：

```text
ExecutionReady must be true
manifest set == planner selected set
decision_updates MatchKey set == selected set
selected active batch closure = 100%
source mutation 与 decision mutation 不得混合
```

---

## 9. NEXT TASK — POLICY-REVIEW BATCH #6

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 10
EvidenceWeight    = 57 / 60
ExecutionReady    = true
SelectedMatchKeys =
  o'clock
  pe
  physical education
  pop
  she's
  tv
  clothes
  couldn't
  didn't
  doesn't
```

本批重点边界：

```text
she's / couldn't / didn't / doesn't
→ contraction / grammar-object boundary

pe / physical education
→ school-subject abbreviation / canonical relation

tv
→ lexical abbreviation

o'clock
→ fixed lexical/time expression boundary

pop
→ source-context lexical sense，防止 broad dictionary polysemy 污染

clothes
→ lexicalized plural vs morphology policy
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical decisions。
2. 不修改 source/raw/parser/config。
3. 生成与 planner 精确一致的 batch_manifest.json + decision_updates.csv。
4. 10/10 closure，不 cherry-pick。
5. apply + rebuild Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview delta。
8. Klose isolation 必须 PASS。
9. bot persist 后重新 planner；阶段结束时更新 NEXT.md。
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
DO NOT admit grammar-quarantined forms into current learner view.
```

---

## 10. Long-term invariants

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 用于回溯，不等于学习优先级；
- MatchKey / morphology / alias 只做 candidate evidence；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- complete cover 前 partial split 不得 release；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
