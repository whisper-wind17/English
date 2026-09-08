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
docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
→ docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine.csv
```

动态进度以 `stage_a_status.json` / generated state 为准，不从旧聊天推测。

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

仍处于 Stage A：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
```

---

## 4. FROZEN — Minimal Learner Identity

2026-09-08 起，废止旧的“所有 reviewed decision 因新增 occurrence 自动 stale/re-review”机制。

新 contract：

```text
Singleton MatchKey
→ Identity 内容稳定
→ OccurrenceKeys 只是 current provenance snapshot
→ source occurrence 增减自动重绑
→ 不重新 semantic review

Multipart MatchKey
→ OccurrenceKeys 是真实 sense partition
→ 必须 complete + disjoint
→ source occurrence 变化仍 requeue
```

核心原则：

```text
Identity 绑定 learning unit，不绑定教材 occurrence。
只有多义 Sense 才绑定 occurrence partition。
```

普通 singleton 只有在以下情况才 reopen：

```text
actual textbook 明确出现第二个 learner-relevant sense
source reconciliation 证明原判断错误
canonical / object boundary 被证明错误
explicit split-required / held / pending
```

Dictionary 多义本身不是 reopen 条件。

Machine implementation：

```text
tools/apply_third_party_identity_decision_updates.py
```

该工具在每次 workflow 自动刷新 singleton occurrence snapshot；multipart rows 不自动扩张。

---

## 5. Latest architecture validation — Minimal Identity

Implementation commit：

```text
c824129b87a87a0f0a8d3f40d41f4ae5811ce31c
refactor: decouple singleton identity from source occurrences
```

Workflow：

```text
#235 / 34219783836 = SUCCESS
```

Bot persist：

```text
1c61762870e3c91a23991856cd432abe7fc2e6bc
```

关键运行证据：

```text
singleton occurrence snapshots auto-rebound = 132
multipart decision rows preserved/checked   = 72
Source occurrences                          = 6005
Normalized surfaces                         = 2161
Durable Identity decisions                  = 2148
Identity Vocabulary Preview                 = 1816
Learner Vocabulary Preview                  = 1801
Review blockers                             = 84
Evidence-changed surfaces                   = 17
Multipart resolved                          = 19
Grammar-form quarantine gates               = 60
```

架构切换前 → 切换后：

```text
Review blockers          211 → 84   (-127)
Evidence-changed         149 → 17   (-132)
Identity Preview        1734 → 1816 (+82)
Learner Preview         1719 → 1801 (+82)
```

完整 validation：

```text
Corpus Completion Recheck         = PASS
TargetSense                       = 1816 / 1816
Learner grammar quarantine        = PASS
past-form leak                    = NO
multipart overlap                 = NO
multipart completeness            = enforced
canonical blocker bypass          = NO
Klose Master/Learner/Publish/Anki = UNTOUCHED
Stable ThirdPartyID minted        = NO
Stage-B diff executed             = NO
```

Independent compare 只涉及 Stage-A tool / review / audit / learner / staging generated state；未修改 Klose publishing state。

---

## 6. Remaining blocker structure

当前 84 个 blocker 已不再是“大量普通词重复审核”。normalized lanes：

```text
object-boundary            = 49
semantic-review            = 17
split-resolution           = 16
deferred-high-ambiguity     = 2
Total                      = 84
```

其中 `semantic-review=17` 主要是已有 multipart 在第六来源加入后的真实 occurrence partition 更新；这是应该保留的精细审核。

Current deterministic planner：

```text
ReviewLane    = semantic-review
SelectedCount = 6
SelectedMatchKeys =
  drink
  duck
  fall
  feel
  film
  past
```

---

## 7. Next execution strategy

不再建立大规模 evidence-revalidation batch。

优先策略：

```text
A. multipart evidence change / split-resolution
   → exact occurrence partition
   → 真正语义问题，小批精审

B. 49 个 object-boundary 新 surface
   → contraction / explicit slot / communicative formula 规则化 route-expression
   → stable lexical phrase / collocation 规则化 keep
   → 只有规则无法确定的少数项再 review

C. deferred-high-ambiguity
   → 保持 defer，除非 context/policy 真变化
```

目标是让人工/模型只处理真正困难的几十个边界项，而不是再次审核普通 singleton。

---

## 8. Frozen learner rules

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
```

- past / past-participle pure form：Identity 可 resolved，当前 learner quarantine；
- lexicalized adjective/noun 不得因词形误 gate；
- homograph learner gate 必须 DecisionKey-scoped；
- contractions 默认 Expressions；
- ordinary plural / 三单 / -ing 不自动 quarantine；
- irregular pedagogical forms 可按明确策略保留独立 Identity；
- actual textbook evidence > third-party dictionary gloss。

关键 multipart / boundary 继续保留：

```text
left#direction / left#leave-past
saw#tool / saw#see-past
her#possessive / her#object
fly#verb / fly#insect
watch#noun / watch#verb
chicken#meat / chicken#animal
cut#verb / cut#injury
cold#temperature / cold#illness
cook#person / cook#verb
```
