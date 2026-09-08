# NEXT — Klose Learning

Last updated: 2026-09-08

## 1. 启动顺序

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
```

动态进度只以 repo 当前文件为准。

---

## 2. Klose operational baseline

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

## 3. Current task — Third-party Multi-Edition Vocabulary Corpus / Stage A

```text
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Unified Vocabulary Identity View
→ current Learner Admission gate
→ Klose learner-stage vocabulary view
```

Durable truth 分层：

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

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #6 CHECKPOINTED

```text
Enabled adapters                   = 6
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2102
Identity-level Vocabulary Preview  = 1010
Review/blocker surfaces            = 960
Evidence-changed surfaces          = 865
Multipart resolved                 = 9
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 998
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 34
Explicit decision-bound past-form requirements = 11
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1010   (+25)
Learner Preview    979  →  998   (+19)
Blockers          1010  →  960   (-50)
Evidence-changed   911  →  865   (-46)
Multipart            7  →    9   (+2)
```

Identity / Learner separation 仍是硬边界：被 gate 的 Identity 没有被删除，只是不进入当前 learner-facing view。

---

## 5. Grammar-stage quarantine — FROZEN

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
lost   = 迷路的 / 丢失的   → lexicalized adjective，保留
scared = 害怕的；受惊的    → 保留
broken = 坏的；破损的      → 保留
```

Homograph 必须 decision-scoped：

```text
left#direction   → 保留
left#leave-past  → quarantine
saw#tool         → 保留
saw#see-past     → quarantine
```

Machine checker 不得把第三方 dictionary/free-text Definition 当 grammar identity truth。

---

## 6. Completed deterministic policy batches after grammar-gate baseline

```text
#2  swam / taught / told / took / went / were / won / wore / wrote / goes
#3  noodles / sweets / thanks / women / sports / found / had / left
#4  lost / made / said / saw / spent / spoke / er / hasn't / children / men
#5  you're / am / can't / cd / dvd / he's / i'm / it / it's / mm / mr / ms
#6  o'clock / pe / physical education / pop / she's / tv / clothes / couldn't / didn't / doesn't
```

关键已冻结判断：

- 过去式 Identity adjudication 与 Learner quarantine 分离；
- `left`、`saw` 使用 occurrence-partitioned homograph split；
- `lost` 等 lexicalized adjective 不因形态被误 gate；
- contractions 默认 route-expression；
- `er / mm` 按教材上下文识别为反应/犹豫语气词，第三方缩写释义为 glossary noise；
- `CD / DVD / TV / Mr / Ms` 在教材明确绑定小学 lexical concept 时可保留 Vocabulary；
- irregular plural `children / men / women` 可作为 pedagogically salient Identity；
- `clothes` 是 lexicalized clothing noun，不是 `cloth` 的普通复数；
- `PE` 与 `physical education` 是同一 school-subject Identity：`physical education` canonical keep，`PE → physical education` reuse，历史 duplicate 已消除；
- `o'clock` 保留为稳定 clock-time lexical unit；
- `pop` 由 music / concert source neighborhood 绑定为流行音乐义，Point-of-Purchase 等释义不作为 source identity truth。

### Latest validation — Batch #6

```text
run 34187325943 / #199 = SUCCESS
batch commit = 7056113f868bd1a79d564b0922ec96d88feb397b
bot persist  = 07ef8cb557ee702f321ead78283ea70126b3a7bb
```

```text
selected active batch closure              = 100%
Batch decisions                            = 10
keep-identity                              = 5
reuse-identity                             = 1
route-expression                           = 4
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1010 / 1010
Third-party learner-stage quarantine       = PASS
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
homograph decision-scope gate              = ENFORCED
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

---

## 7. Identity / Learner / Source — HARD INVARIANT

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

Future Stage B 不能直接把 `unified_vocabulary_preview.csv` 当当前学习清单；必须再经过 learner-stage gate。

---

## 8. V4 learner-first Identity policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频 pedagogical form
→ Identity 层可显式 keep，必须有 rationale
→ 是否当前学习由 Learner Admission 独立决定

显式 slot / grammar pattern / communicative formula / contraction
→ route-expression

event / tense-specific source chunk
→ source-only

多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

Lexical abbreviation 只有 source 能绑定明确小学概念时才 keep；若 full form 同时存在且 identity 等价，优先 canonicalize，避免 duplicate Identity。

---

## 9. High-throughput execution mechanism — FROZEN

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

## 10. NEXT TASK — POLICY-REVIEW BATCH #7

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 8
EvidenceWeight    = 57 / 60
ExecutionReady    = true
SelectedMatchKeys =
  drank
  flew
  her
  here's
  isn't
  mrs
  our
  parent
```

本批重点：

```text
drank / flew
→ past-form Identity re-review + learner quarantine boundary

here's / isn't
→ contraction / Expression routing

her / our
→ high-frequency pronoun/determiner identity

mrs
→ lexical title abbreviation

parent
→ singular lexical identity vs regular plural relationship
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 8/8 closure，不 cherry-pick。
5. apply + rebuild Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview delta。
8. Klose isolation 必须 PASS。
9. bot persist 后重新 planner；阶段结束更新 NEXT.md。
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

## 11. Long-term invariants

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
