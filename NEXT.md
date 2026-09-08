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

## 4. Current checkpoint — POLICY REVIEW THROUGH BATCH #14 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2105
Identity-level Vocabulary Preview  = 1072
Review/blocker surfaces            = 888
Evidence-changed surfaces          = 794
Multipart resolved                 = 12
```

Current learner projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 1060
Identity rows suppressed by gate   = 12
Preview occurrence contributions removed = 44
Explicit decision-bound past-form requirements = 13
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1072   (+87)
Learner Preview    979  → 1060   (+81)
Blockers          1010  →  888   (-122)
Evidence-changed   911  →  794   (-117)
Multipart            7  →   12   (+5)
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
shorts           → lexicalized 短裤，not short morphology
sometime         → 在某一时候；改天
sometimes        → lexical frequency adverb，not sometime morphology
sport            → canonical 运动；体育运动
sports           → reuse sport
sleep            → 睡觉；睡眠
slept            → reuse sleep；learner quarantine
study            → learner-first narrow sense 学习；读书
swim             → 游泳
swam             → reuse swim；learner quarantine
thank            → 感谢；distinct from lexicalized thanks
vegetable        → 蔬菜；vegetables reuse vegetable
watch#noun       → 手表；current 2 occurrences
watch#verb       → 观看；注视；current 4 occurrences
running          → lexicalized activity 跑步；not generic run inflection
stairs           → lexicalized plural noun 楼梯
broken           → lexicalized adjective 破损的/坏掉的，not automatic break reuse
fell             → reuse fall#verb；learner layer remains grammar-quarantined
fly#verb         → 飞；飞行；current 10 occurrences complete/disjoint with fly#insect
fly#insect       → 苍蝇；current 1 occurrence
flies            → split-required / held；canonical fly 已 resolve，但唯一 source occurrence 仍同时可解释 insect plural / fly 3sg，禁止 silent release
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
#11 at / no / broken / candy / don't / fell
#12 fly / foot / go / leave / paint / shoe
#13 short / sleep / sock / sometime / sport / story
#14 study / swim / thank / vegetable / watch
```

### Latest validation — Batch #14

```text
initial batch commit = 87ea8c80c3eaa022e108289057f7cfd8d2365dd0
first run            = 34192303590 / #209 = FAIL at former-semantic-collision marker; no bot persist
study marker fix     = 7293f8ed349cf515cd637f685204ba932dee9e76
corrected run        = 34192385503 / #210 = SUCCESS
bot persist          = 9368335ea8ce7dc2fd4e9c571688982a06d99077
```

第一次失败不是 sense 判断错误：`study` 是 checker 冻结的 former semantic collision，单一 keep 放行必须在 `DecisionBasis` 显式带 `learner-first`。修复后继续保留 narrow TargetSense `学习；读书`，不引入 research / study-room dictionary senses。

```text
selected active batch closure              = 100%
Batch decision rows                        = 6
Touched MatchKeys                          = 5
keep-identity                              = 6
watch multipart partition                  = 2 noun + 4 verb, complete/disjoint
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1072 / 1072
Third-party learner-stage quarantine       = PASS
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
homograph decision-scope gate              = ENFORCED
former semantic collision policy           = ENFORCED
known morphology decisions preserved       = YES
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

Batch #14 delta：

```text
Blockers          893 → 888   (-5)
Evidence-changed  799 → 794   (-5)
Identity Preview 1066 → 1072  (+6)
Learner Preview  1054 → 1060  (+6)
Multipart          11 →   12  (+1)
```

Preview 增加 6 而 selected surface 只有 5，是因为 `watch` 完整恢复两个 provisional identities：`watch#noun` 与 `watch#verb`。`swam → swim`、`thanks`、`vegetables → vegetable` 等既有关系保持不变。

独立 compare `7293f8e... → 9368335...` 只包含 Stage-A review/audit/learner/staging 生成物与 transient batch 文件删除；未触碰 source adapter/raw，也未触碰 Klose Master/Learner/Publish/Anki。

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

## 8. NEXT TASK — POLICY-REVIEW BATCH #15

Current deterministic planner：

```text
ReviewLane        = policy-review
SelectedCount     = 2
EvidenceWeight    = 20 / 60
ExecutionReady    = true
ReviewBundleFingerprint = d38d0c70f2216406d99aaa922535f8d1d8f0c5136709b6bf41a3686691322ac8
SelectedMatchKeys =
  win
  man
```

本批重点：

```text
win
→ canonical 与 won reuse 关系已冻结；需用 sixth-source evidence 重绑，不扩张 TargetSense。

man
→ singular adult/person concept 与 men reuse 的关系；检查 Waiyan Start3 的多个 source contexts，避免 dictionary broad sense 污染。
```

执行要求：

```text
1. 读取 exact source occurrences + current win/man/won/men decisions。
2. 不修改 source/raw/parser/config。
3. 生成 planner 精确对应的 batch_manifest.json + decision_updates.csv。
4. 2/2 closure；fingerprint 使用当前 next_batch 原值。
5. apply/build/recheck/learner/batch/Klose isolation 全部 PASS。
6. bot persist 后重新 planner并更新 NEXT.md。
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
