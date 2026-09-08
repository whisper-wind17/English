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

Durable truth：

```text
review/identity_decisions.csv       = Identity content truth
learner/grammar_form_quarantine.csv = current Klose Learner Admission gate
```

Reviewed Identity decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

仍处于 Stage A：不得 mint Stable ThirdPartyID，不得运行 Stage-B Klose diff，不得修改 Klose Master/Learner/Publish/Anki。

---

## 4. Current checkpoint — SEMANTIC REVIEW BATCH #17 CHECKPOINTED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2130
Identity-level Vocabulary Preview  = 1100
Review/blocker surfaces            = 852
Evidence-changed surfaces          = 783
Multipart resolved                 = 12
```

Current learner projection：

```text
Grammar-form quarantine gates      = 58
Learner-stage Vocabulary Preview   = 1086
Identity rows suppressed by gate   = 14
Preview occurrence contributions removed = 49
Explicit decision-bound past-form requirements = 15
```

从 grammar-gate baseline 到当前：

```text
Identity Preview   985  → 1100   (+115)
Learner Preview    979  → 1086   (+107)
Blockers          1010  →  852   (-158)
Evidence-changed   911  →  783   (-128)
Multipart            7  →   12   (+5)
```

Policy-review lane 已在 Batch #15 清空；当前持续执行 `semantic-review`。

---

## 5. Frozen identity / learner rules

```text
Source Fact
≠ Vocabulary Identity
≠ Learner Admission
≠ Anki learning state
```

- pure one-word past/past-participle forms当前 learner quarantine；Identity 可先 resolve；
- lexicalized adjective/noun 不得因形态误 gate；
- homograph 必须 decision-scoped；
- contractions 默认 route-expression；
- dictionary/free-text Definition 不得作为 source identity truth；
- full form / abbreviation 若同一 learner identity，可 canonicalize 到已 reviewed provisional identity；
- 多个真实 target senses 必须 occurrence split，complete/disjoint cover 前不能 release；证据不足时 `split-required / held`；
- former semantic collision 若不 split/held，必须显式 learner-first narrow TargetSense。

关键冻结边界：

```text
left#direction   → learner admit
left#leave-past  → quarantine
saw#tool         → learner admit
saw#see-past     → quarantine
her#possessive   → 她的
her#object       → 她（宾格）
PE               → reuse physical education
No.              → reuse number
shorts           → lexicalized 短裤
sometimes        → lexical frequency adverb
sports           → reuse sport
slept/swam/won   → canonical reuse + learner quarantine
watch#noun       → 手表
watch#verb       → 观看；注视
men/women/children/grandchildren → pedagogically salient irregular-plural Identity
fly#verb         → 飞；飞行
fly#insect       → 苍蝇
flies            → split-required / held；禁止 silent release
beautifully/loudly → 独立 learner adverb Identity
kilo             → reuse kilogram
television       → reuse current reviewed TV identity
rang/sang        → pedagogical past-form Identity + learner quarantine
```

`rang/sang` 没有绕过 evidence-changed 的 `ring/sing` canonical blocker；以后 canonical re-review 完成后再决定是否迁移为 reuse。

---

## 6. Completed deterministic batches

Policy-review 已完成 #2–#15；semantic-review：

```text
#16 ah / beautifully / bye-bye / chameleon / coffee / e-book / foreign / goalkeeper / grandchild / grandchildren / haven't / herself / information / interviewer / kilo / lady / lantern / loudly / ouch / rang / sang / shelf / television / that's / topic / aah / afraid / afternoon / airport
#17 always / an / and / angry / animal
```

### Latest validation — Batch #17

```text
batch commit       = ac8708e3ec6a8c829efe55a40bf623fcb46a199a
run                = 34203667397 / #213 = SUCCESS
bot persist        = 9d383e7f437448c5ce344ef6f7285abb0dab9ea4
```

```text
selected active batch closure              = 100%
Batch decisions                            = 5
keep-identity                              = 5
Third-party Simplified Completion Recheck  = PASS
Identity Preview TargetSense               = 1100 / 1100
Third-party learner-stage quarantine       = PASS
Grammar-form quarantine gates              = 58
Explicit decision-bound past requirements  = 15
past-form leak into learner preview        = NO
lexicalized participle/adjective over-gating = NO
canonical blocker bypass                   = NO
source occurrence closure                  = PASS
Klose Master/Learner/Publish/Anki          = UNTOUCHED
Stable ThirdPartyID minted                 = NO
Final Klose diff executed                  = NO
```

Batch #17 delta：

```text
Blockers          857 → 852   (-5)
Evidence-changed  788 → 783   (-5)
Identity Preview 1095 → 1100  (+5)
Learner Preview  1081 → 1086  (+5)
```

`always / an / and / angry / animal` 的 sixth-source evidence 均与既有 elementary core 一致；dictionary broad senses 未被导入 TargetSense。

独立 compare `ac8708e... → 9d383e7...` 只包含 Stage-A review/audit/learner/staging 生成物与 transient batch 文件删除；未触碰 source adapter/raw，也未触碰 Klose Master/Learner/Publish/Anki。

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

## 8. NEXT TASK — SEMANTIC-REVIEW BATCH #18

```text
ReviewLane        = semantic-review
SelectedCount     = 6
EvidenceWeight    = 57 / 60
ExecutionReady    = true
ReviewBundleFingerprint = 06b78d12b93fb81b19daa3ea8b3b0944ebeb5c8667e8e655ca220df5dff52bac
SelectedMatchKeys =
  apple
  arrive
  aunt
  banana
  baseball
  basketball
```

执行要求：

```text
1. 读取 current exact occurrences / source neighborhood / durable decisions。
2. 6/6 semantic adjudication；重点排除 apple/banana 等 dictionary noise，并确认 arrive 与 aunt 的 elementary core。
3. 不修改 source/raw/parser/config。
4. manifest / decision_updates / planner set 100% 一致。
5. apply/build Identity/Learner views。
6. core Completion Recheck + learner checker + batch recheck 全部 PASS。
7. Klose isolation PASS；bot persist 后重新 planner并更新 NEXT.md。
```

`flies` 仍是 independently held split-resolution item，非 planner 选择不得顺手修改。

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
DO NOT admit grammar-quarantined forms into current learner view.
```
