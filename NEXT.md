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

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #13 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2105
Identity-level Vocabulary Preview  = 1066
Review/blocker surfaces            = 893
Evidence-changed surfaces          = 799
Multipart resolved                 = 11
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 1054
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 42
Explicit decision-bound past-form requirements = 13
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1066   (+81)
Learner Preview    979  → 1054   (+75)
Blockers          1010  →  893   (-117)
Evidence-changed   911  →  799   (-112)
Multipart            7  →   11   (+4)
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
short            → 短的；矮的
shorts           → lexicalized 短裤，not short morphology
sometime         → 在某一时候；改天
sometimes        → lexical frequency adverb，not sometime morphology
sport            → canonical 运动；体育运动
sports           → reuse sport
sleep            → 睡觉；睡眠
slept            → reuse sleep；learner quarantine
running          → lexicalized activity 跑步；not generic run inflection
stairs           → lexicalized plural noun 楼梯
broken           → lexicalized adjective 破损的/坏掉的，not automatic break reuse
fell             → reuse fall#verb；learner layer remains grammar-quarantined
fly#verb         → 飞；飞行；current 10 occurrences complete/disjoint with fly#insect
fly#insect       → 苍蝇；current 1 occurrence
flies            → split-required / held；canonical fly 已 resolve，但唯一 source occurrence 仍同时可解释 insect plural / fly 3sg，禁止 silent release
```

`fly` 的 Waiyan Start3 `Flag Day` occurrence 属于同一 verb identity 的 construction-specific extension；为保持既有 scoped reuse（例如 `flew → fly#verb`）的 canonical TargetSense 一致性，Stage-A learner-facing core sense 仍冻结为 `飞；飞行`，不为单一构式额外 mint identity。

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
#11 at / no / broken / candy / don't / fell
#12 fly / foot / go / leave / paint / shoe
#13 short / sleep / sock / sometime / sport / story
```

### Latest validation — Batch #13

```text
run               = 34191932272 / #208 = SUCCESS
batch commit       = c0039a098baab61a1a01b22432cb6ae8984306d3
bot persist        = 4d59274169837c6c0cbb914a85fd0db793466505
```

```text
selected active batch closure              = 100%
Batch decisions                            = 6
keep-identity                              = 6
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1066 / 1066
Third-party learner-stage quarantine       = PASS
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
homograph decision-scope gate              = ENFORCED
known morphology decisions preserved       = YES
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

Batch #13 delta：

```text
Blockers          899 → 893   (-6)
Evidence-changed  805 → 799   (-6)
Identity Preview 1060 → 1066  (+6)
Learner Preview  1048 → 1054  (+6)
Multipart          11 →   11
```

`short/shorts`、`sometime/sometimes`、`sport/sports` 三组关系保持原判，没有被 sixth-source revalidation 反向改写；`sleep` 仍是 noun/verb unified elementary concept，`slept` 继续 canonical reuse + learner quarantine。

独立 compare `c0039a0... → 4d59274...` 只包含 Stage-A review/audit/learner/staging 生成物与 transient batch 文件删除；未触碰 source adapter/raw，也未触碰 Klose Master/Learner/Publish/Anki。

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

## 8. NEXT TASK — POLICY-REVIEW BATCH #14

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 5
EvidenceWeight    = 57 / 60
ExecutionReady    = true
ReviewBundleFingerprint = 0d10c69531b03500e0b4efbe1554b5b5dd7c329a523ff805314960af1f56db2b
SelectedMatchKeys =
  study
  swim
  thank
  vegetable
  watch
```

本批重点：

```text
study
→ existing learner-first core 为“学习；读书”；需检查 sixth-source 是否引入 study-room / research 等真实 source sense，而不是 dictionary noise。

swim
→ noun / verb unified activity concept；同时与 swam reuse 有 canonical dependency，TargetSense 不得无意扩张。

thank
→ verb / interjection-like textbook presentation 边界；检查是否仍为稳定 gratitude lexical unit。

vegetable
→ concrete food noun vs plant/person dictionary noise。

watch
→ known multipart/homograph risk：watch#verb 与手表 noun boundary；必须检查 current occurrence partition，不能用一个 TargetSense 粗暴覆盖。
```

执行要求：

```text
1. 读取 current review_bundle / exact source occurrences / related canonical/multipart decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 5/5 closure，不 cherry-pick；manifest fingerprint 必须从当前 next_batch.json 直接读取。
5. apply + rebuild Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview / canonical dependency delta。
8. watch 若需要 multipart，必须 complete/disjoint；swam 等 scoped reuse 必须保持 canonical TargetSense 一致。
9. Klose isolation 必须 PASS。
10. bot persist 后重新 planner；阶段结束更新 NEXT.md。
```

`flies` 当前仍是 independently held split-resolution item；除非后续 deterministic planner 明确选择并且 source evidence 足以消除 ambiguity，否则不得在其他 batch 中顺手修改。

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
DO NOT admit grammar-quarantined forms into current learner view.
```
