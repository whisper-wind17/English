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

## 4. Current checkpoint — SEMANTIC REVIEW BATCH #16 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2130
Identity-level Vocabulary Preview  = 1095
Review/blocker surfaces            = 857
Evidence-changed surfaces          = 788
Multipart resolved                 = 12
```

Current learner projection：

```text
Grammar-form quarantine gates      = 58
Learner-stage Vocabulary Preview   = 1081
Identity rows suppressed by gate   = 14
Preview occurrence contributions removed = 49
Explicit decision-bound past-form requirements = 15
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1095   (+110)
Learner Preview    979  → 1081   (+102)
Blockers          1010  →  857   (-153)
Evidence-changed   911  →  788   (-123)
Multipart            7  →   12   (+5)
```

Policy-review lane 已在 Batch #15 清空；当前进入 `semantic-review`。

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
- lexical abbreviation 若教材明确绑定小学 lexical concept 可 keep；若 full form 同时存在且 identity 等价，允许 canonicalize 到已 reviewed 的稳定 provisional identity；
- 多个真实 target senses 必须 occurrence split，complete/disjoint cover 前不能 release；证据不足时可显式 `split-required / held`，不得猜 sense；
- former semantic collision 若不 split/held，必须使用显式 `learner-first` DecisionBasis + narrow TargetSense 才能 release。

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
shorts           → lexicalized 短裤
sometime         → 在某一时候；改天
sometimes        → lexical frequency adverb
sport            → canonical 运动；体育运动
sports           → reuse sport
sleep            → 睡觉；睡眠
slept            → reuse sleep；learner quarantine
study            → learner-first narrow sense 学习；读书
swim             → 游泳
swam             → reuse swim；learner quarantine
watch#noun       → 手表
watch#verb       → 观看；注视
win              → 赢；获胜
won              → reuse win；learner quarantine
man              → 男人；男性
men              → pedagogically salient irregular-plural Identity
fly#verb         → 飞；飞行
fly#insect       → 苍蝇
flies            → split-required / held；禁止 silent release
```

Batch #16 新冻结边界：

```text
ah / aah / ouch / bye-bye → route-expression
haven't / that's           → route-expression
beautifully                → 独立 learner adverb Identity，不机械 reuse beautiful
loudly                     → 独立 learner adverb Identity，不机械 reuse loud
grandchild                 → singular kinship Identity
grandchildren              → pedagogically salient irregular-plural Identity
kilo                        → reuse kilogram
television                  → reuse current reviewed TV identity
rang                        → pedagogical past-form Identity；learner quarantine
sang                        → pedagogical past-form Identity；learner quarantine
```

`rang/sang` 本轮没有绕过当前 evidence-changed 的 `ring/sing` canonical blocker；Identity 层按教材显式过去式 learning form resolve，Learner Admission 层继续隔离。以后 canonical re-review 完成时可再决定是否迁移为 reuse，但当前不得 silent rewrite。

---

## 6. Completed deterministic batches

Policy-review：

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
#14 study / swim / thank / vegetable / watch
#15 win / man
```

Semantic-review：

```text
#16 ah / beautifully / bye-bye / chameleon / coffee / e-book / foreign / goalkeeper / grandchild / grandchildren / haven't / herself / information / interviewer / kilo / lady / lantern / loudly / ouch / rang / sang / shelf / television / that's / topic / aah / afraid / afternoon / airport
```

### Latest validation — Batch #16

```text
batch commit       = 64e29c1d1dfefd09f34852f0dc0328418300866b
run                = 34203187550 / #212 = SUCCESS
bot persist        = b584e0b55790287b3978212b508ebe5a8a5e510b
```

```text
selected active batch closure              = 100%
Batch decisions                            = 29
keep-identity                              = 21
reuse-identity                             = 2
route-expression                           = 6
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1095 / 1095
Third-party learner-stage quarantine       = PASS
Grammar-form quarantine gates              = 58
Explicit decision-bound past requirements  = 15
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
homograph decision-scope gate              = ENFORCED
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

Batch #16 delta：

```text
Blockers          886 → 857   (-29)
Evidence-changed  792 → 788   (-4)
Identity Preview 1074 → 1095  (+21)
Learner Preview  1062 → 1081  (+19)
Multipart          12 →   12
Grammar gates      56 →   58
```

`rang/sang` 两个 Identity-level rows 进入 Identity Preview，但被新增 learner gate 精确压住，因此 Learner Preview 比 Identity Preview 少 2 个增量。

独立 compare `64e29c1... → b584e0b...` 只包含 Stage-A review/audit/learner/staging 生成物与 transient batch 文件删除；未触碰 source adapter/raw，也未触碰 Klose Master/Learner/Publish/Anki。

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

## 8. NEXT TASK — SEMANTIC-REVIEW BATCH #17

Current deterministic planner：

```text
ReviewLane        = semantic-review
SelectedCount     = 5
EvidenceWeight    = 52 / 60
ExecutionReady    = true
ReviewBundleFingerprint = 2943abd3e4bf51527ab52f4c985f7b8821bb364e3cca17837b159c25d33bd319
SelectedMatchKeys =
  always
  an
  and
  angry
  animal
```

本批全部是高 occurrence / cross-source semantic revalidation，虽然历史已有 reviewed learner core，但 sixth-source evidence 已变化，必须重新绑定 exact occurrence set，不能机械继承旧 decision。

执行要求：

```text
1. 读取 current review_bundle + exact current occurrences + current durable decisions。
2. 核对新增 Waiyan Start3 evidence 是否仍与既有 learner-facing core 同义；dictionary broad senses 不作为 source identity truth。
3. 5/5 closure，不 cherry-pick。
4. 不修改 source/raw/parser/config。
5. 生成当前 planner 精确对应的 batch_manifest.json + decision_updates.csv。
6. apply/build Identity/Learner views。
7. core Completion Recheck + learner checker + batch recheck 全部 PASS。
8. Klose isolation 必须 PASS。
9. bot persist 后重新 planner并更新 NEXT.md。
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
