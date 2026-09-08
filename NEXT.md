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

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #10 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2105
Identity-level Vocabulary Preview  = 1049
Review/blocker surfaces            = 911
Evidence-changed surfaces          = 817
Multipart resolved                 = 10
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 1037
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 34
Explicit decision-bound past-form requirements = 13
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1049   (+64)
Learner Preview    979  → 1037   (+58)
Blockers          1010  →  911   (-99)
Evidence-changed   911  →  817   (-94)
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
- 多个真实 target senses 必须 occurrence split，complete/disjoint cover 前不能 release；证据不足时可显式 `split-required / held`，不得猜 sense。

已冻结典型：

```text
left#direction   → learner admit
left#leave-past  → quarantine
saw#tool         → learner admit
saw#see-past     → quarantine
her#possessive   → 她的
her#object       → 她（宾格）
PE               → reuse physical education
No.              → reuse number
shorts           → lexicalized 短裤，not short morphology
sometimes        → lexical frequency adverb，not sometime morphology
running          → lexicalized activity 跑步；not generic run inflection
stairs           → lexicalized plural noun 楼梯
flies            → split-required / held；source cannot disambiguate insect plural vs fly 3sg
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
#10 hide-and-seek / kilometre / language / librarian / passport / physics / raincoat / sausage / someday / spaceship / speech / string / taikonaut / town / traditional / winner / child / no. / flies
```

### Latest validation — Batch #10

```text
first run 34189627528 / #203 = FAIL at manifest fingerprint only; no durable apply/build executed
corrected run 34189731265 / #204 = SUCCESS
batch commit       = 1d492793108b4f317e3f072f2b127b2d3fe685c3
fingerprint fix    = 8f01fff6e8e5c0d2025a89e08fb07b63ca6fe358
bot persist        = 89aeaba...
```

```text
selected active batch closure              = 100%
Batch decisions                            = 19
keep-identity                              = 17
reuse-identity                             = 1   (No. → number)
split-required                             = 1   (flies held)
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1049 / 1049
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

Batch #10 delta：

```text
Blockers          929 → 911   (-18)
Evidence-changed  834 → 817   (-17)
Identity Preview 1032 → 1049  (+17)
Learner Preview  1020 → 1037  (+17)
```

为什么不是净释放 19：`flies` 已完成审查，但唯一 source occurrence 同时可解释为 insect plural 与 `fly` 的 third-person singular，当前 flat vocabulary neighborhood 无法证明哪一个才是教材 target sense，因此显式保留为 blocker；这属于正确的 evidence-aware hold，而非未处理。

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
manifest fingerprint == current next_batch fingerprint
decision_updates MatchKey set == selected set
selected active batch closure = 100%
source mutation 与 decision mutation 不得混合
```

---

## 8. NEXT TASK — POLICY-REVIEW BATCH #11

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 6
EvidenceWeight    = 46 / 60
ExecutionReady    = true
ReviewBundleFingerprint = 4f605c11ac420fd025c803327fa04e9b9f419fa93b26bae714caa52d674a080e
SelectedMatchKeys =
  at
  no
  broken
  candy
  don't
  fell
```

本批重点：

```text
at / no
→ dictionary abbreviation noise vs elementary grammatical core

broken
→ lexicalized adjective vs break participle

candy
→ elementary food noun despite broad dictionary noise

don't
→ contraction；继续 route-expression，并重绑 sixth-source evidence

fell
→ past form of multipart canonical fall；必须核对 scoped canonical reuse 与 learner quarantine
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 6/6 closure，不 cherry-pick；manifest fingerprint 必须从当前 next_batch.json 直接读取。
5. apply + rebuild Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview / canonical dependency delta。
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
