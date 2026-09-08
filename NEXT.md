# NEXT — Klose Learning

Last updated: 2026-09-08

## 1. 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary 继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
→ docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
```

动态进度以 repo 当前 machine state 为准。

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

## 3. Third-party Stage A source baseline

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
Normalized       = 2161 surfaces
```

Stage A 仍禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff before readiness audit.
DO NOT modify Klose Master/Learner/Publish/Anki.
```

---

## 4. FROZEN — Minimal Learner Identity

```text
Singleton MatchKey
→ Identity 内容稳定
→ OccurrenceKeys = provenance snapshot
→ source occurrence 增减自动重绑
→ 不重复 semantic review

Multipart MatchKey
→ OccurrenceKeys = semantic sense partition
→ non-empty + disjoint + complete 才 release
→ context 不足则 audited defer
```

核心原则：

```text
Identity 绑定 learning unit，不绑定教材 occurrence。
只有真实多义 Sense 才绑定 occurrence partition。
```

普通 singleton 只有 actual textbook 证明第二个 learner-relevant sense、source reconciliation / canonical / object-boundary 判断被证明错误，或显式 split/held/pending 时才 reopen。

Dictionary 多义本身不是 reopen 条件。

Machine implementation：

```text
tools/apply_third_party_identity_decision_updates.py
```

---

## 5. Minimal Identity architecture validation

Implementation：

```text
c824129b87a87a0f0a8d3f40d41f4ae5811ce31c
refactor: decouple singleton identity from source occurrences
```

Validation：

```text
Workflow #235 / 34219783836 = SUCCESS
bot persist = 1c61762870e3c91a23991856cd432abe7fc2e6bc
```

架构切换直接消除了普通 singleton 的重复审核：

```text
Review blockers          211 → 84
Evidence-changed         149 → 17
Identity Preview        1734 → 1816
Learner Preview         1719 → 1801
```

---

## 6. Tail state-machine migration — v6

旧 defer registry 使用：

```text
PolicyVersion = v4-learner-first
```

Minimal Identity 已改变 review policy，因此旧 defer 不能继续静默沿用。

Fix：

```text
fc92a7e40da85da3edb1ec52bef718c199410bc8
fix: reopen defers under minimal identity policy

POLICY_VERSION = v6-minimal-identity
```

Workflow：

```text
#248 / 34225784648 = SUCCESS
```

14 个旧 defer 全部被 state machine 重新激活并重新 adjudicate。

### Tail batch 1

```text
commit = 81dd23cab1e96f4337cf42f7f4ad4a5828f0515c
run    = #249 / 34226021650 = SUCCESS
```

`mouse` 已安全拆分：

```text
mouse#animal   = 老鼠
mouse#computer = 鼠标；电脑鼠标
```

4/4 occurrences complete + disjoint；其余 `too / french / kind / little / pass` 在 v6 下重新确认 defer。

### Tail batch 2

```text
commit = c7ecce2c8250481c476cec208f120ca3492c9cf4
run    = #250 / 34226147440 = SUCCESS
```

`flies / fan / get / letter / line / plant` 在 v6 下重新确认：真实多义已证明，但 flat-list occurrence 仍不足以完整分区，因此保留 audited defer。

### Tail batch 3

```text
commit = 76ba2eab330be1ed622fadcd2033a28d21b3fb14
run    = #251 / 34226315393 = SUCCESS
bot persist = d3450c6cd6648962bbb8ca57ffe4a9b4c10ec9a7
```

`right / sound` 同样在 v6 下重新确认 defer。

---

## 7. Current machine checkpoint — Stage A tail stable

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2204
Identity Vocabulary Preview        = 1892
Learner Vocabulary Preview         = 1877
Review blockers                    = 13
Evidence-changed surfaces          = 0
Multipart resolved                 = 41
Grammar-form quarantine gates      = 60
NextBatch SelectedCount            = 0
ExecutionReady                     = false
GateReason                         = no active review batch
```

这 13 个不是未处理 backlog，而是 **Minimal Identity v6 下已审计的 source-context limitations**：

```text
fan
flies
french
get
kind
letter
line
little
pass
plant
right
sound
too
```

它们都满足：

```text
多个 learner-relevant senses 已被证明
+
flat vocabulary list 无法把每个 occurrence 安全归组
→ split-required / held
→ audited defer
→ source/context/policy 不变化则 zero-scan
```

不得为了 blocker=0 猜 occurrence。

`mouse` 不再属于 residual blocker，已完整 resolve。

---

## 8. Validation / truth boundary

#248–#251 全部通过：

```text
Corpus Completion Recheck         = PASS
TargetSense complete              = PASS
multipart overlap                 = NO
multipart completeness            = enforced
partial split remains blocker     = YES
canonical blocker bypass          = NO
Learner grammar quarantine        = PASS
past-form leak                    = NO
Klose Master/Learner/Publish/Anki = UNTOUCHED
Stable ThirdPartyID minted        = NO
Stage-B diff executed             = NO
```

Independent compare `8db2bb11... → d3450c6c...` 只涉及 Stage-A review/audit/staging/learner generated state 与 `normalize_third_party_review_lanes.py`；没有修改 Klose publishing state。

---

## 9. NEXT TASK — Stage A completion / Stage B readiness audit

不要再次扫描 13 个 unchanged v6 defer。

下一步先明确 Stage A completion semantics：

```text
resolved corpus identities = 可进入 Stage-B reconciliation
v6 audited-defer identities = carry-forward unresolved exceptions
```

需要检查现有 Stage-B / Klose reconciliation 工具和 gate，确认：

1. 是否错误要求 `ReviewBlockers == 0`；
2. 是否能显式排除 / carry forward 13 个 audited defer，而不静默丢失；
3. Stage B 只消费 reviewed Identity Preview + learner-stage view；
4. Stable NoteID migration / Klose existing identity reconciliation 是否有 machine gate；
5. 在 readiness audit 完成前不得执行正式 Stage-B mutation。

如果现有 Stage-B contract 要求所有 source surfaces 100% resolved，应先设计显式 `AuditedDeferredIdentity` carry-forward contract，而不是放松 multipart completeness。

---

## 10. Frozen learner rules

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
```

- pure past / past-participle form：Identity 可 resolved，当前 learner quarantine；
- lexicalized adjective/noun 不得因词形误 gate；
- homograph learner gate 必须 DecisionKey-scoped；
- contractions 默认 Expressions；
- ordinary plural / 三单 / -ing 不自动 quarantine；
- irregular pedagogical forms 可按明确策略保留独立 Identity；
- actual textbook evidence > third-party dictionary gloss。
