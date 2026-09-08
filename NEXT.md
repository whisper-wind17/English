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

Durable truth 分层：

```text
review/identity_decisions.csv       = Identity content truth
learner/grammar_form_quarantine.csv = current Klose Learner Admission gate
```

Reviewed Identity decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

仍处于 Stage A：不得 mint Stable ThirdPartyID，不得运行 Stage-B Klose diff，不得修改 Klose Master/Learner/Publish/Anki。

---

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #9 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2103
Identity-level Vocabulary Preview  = 1032
Review/blocker surfaces            = 929
Evidence-changed surfaces          = 834
Multipart resolved                 = 10
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 1020
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 34
Explicit decision-bound past-form requirements = 13
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1032   (+47)
Learner Preview    979  → 1020   (+41)
Blockers          1010  →  929   (-81)
Evidence-changed   911  →  834   (-77)
Multipart            7  →   10   (+3)
```

---

## 5. Frozen identity / learner rules

```text
Source Fact
≠ Vocabulary Identity
≠ Learner Admission
≠ Anki learning state
```

- pure one-word past/past-participle forms 当前 learner quarantine；Identity 可先 resolve；
- lexicalized adjective/noun 不得因形态误 gate；
- homograph 必须 decision-scoped；
- contractions 默认 route-expression；
- dictionary/free-text Definition 不得作为 source identity truth；
- lexical abbreviation 若教材明确绑定小学 lexical concept 可 keep；若 full form 同时存在且 identity 等价，优先 canonicalize；
- 多个真实 target senses 必须 occurrence split，complete/disjoint cover 前不能 release。

已冻结典型：

```text
left#direction   → learner admit
left#leave-past  → quarantine
saw#tool         → learner admit
saw#see-past     → quarantine
her#possessive   → 她的
her#object       → 她（宾格）
PE               → reuse physical education
shorts           → lexicalized 短裤，not short morphology
sometimes        → lexical frequency adverb，not sometime morphology
running          → lexicalized activity 跑步；not generic run inflection
stairs           → lexicalized plural noun 楼梯
```

---

## 6. Completed deterministic policy batches

```text
#2  swam / taught / told / took / went / were / won / wore / wrote / goes
#3  noodles / sweets / thanks / women / sports / found / had / left
#4  lost / made / said / saw / spent / spoke / er / hasn't / children / men
#5  you're / am / can't / cd / dvd / he's / i'm / it / it's / mm / mr / ms
#6  o'clock / pe / physical education / pop / she's / tv / clothes / couldn't / didn't / doesn't
#7  drank / flew / her / here's / isn't / mrs / our / parent
#8  shorts / sometimes / they're / wasn't / weren't / what's / where's / woman / won't
#9  your / running / stairs / a / actor / cent / chemistry / chinatown / dragon / everything / firefighter / geography / halloween / happiness
```

### Latest validation — Batch #9

```text
run 34189090892 / #202 = SUCCESS
batch commit = 2ed87b4ab08a96f00643978a6cf4ce586ae6001d
bot persist  = af12ffc3943e1c804a2964b3bd24a4f34ada6848
```

```text
selected active batch closure              = 100%
Batch decisions                            = 14
keep-identity                              = 14
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1032 / 1032
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

Batch #9 evidence notes：

```text
running  → activity noun/learning unit 跑步；sixth-source evidence does not justify collapsing to run
stairs   → conventional lexicalized plural noun 楼梯
cent     → currency unit 分；cashier/dollar payment neighborhood is decisive
a        → indefinite article；waiyan_start3 dictionary “letter A/ampere” gloss is source-definition noise
all other selected rows → exact sixth-source evidence revalidated existing elementary lexical identity
```

---

## 7. High-throughput execution mechanism — FROZEN

```text
review_bundle.csv
→ normalize lanes
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

## 8. NEXT TASK — POLICY-REVIEW BATCH #10

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 19
EvidenceWeight    = 58 / 60
ExecutionReady    = true
SelectedMatchKeys =
  hide-and-seek
  kilometre
  language
  librarian
  passport
  physics
  raincoat
  sausage
  someday
  spaceship
  speech
  string
  taikonaut
  town
  traditional
  winner
  child
  no.
  flies
```

本批重点：

```text
hide-and-seek / raincoat / spaceship / taikonaut
→ lexicalized compound boundaries

kilometre / language / librarian / passport / physics / sausage / someday / speech / string / town / traditional / winner
→ sixth-source exact-evidence lexical revalidation

child
→ singular identity vs irregular plural children pedagogical treatment

no.
→ abbreviation identity vs source presentation form

flies
→ inflectional form vs possible lexical/homograph reading；不得机械 morphology collapse
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 19/19 closure，不 cherry-pick。
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
