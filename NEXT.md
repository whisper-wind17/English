# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

当前 Klose 主系统与第三方 Vocabulary 前置链路：

```text
Grade 5–6 Vocabulary GitHub Release   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated               = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Grade 5–6 Expressions GitHub Release  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Anki Updated              = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation    = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract       = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party allocation plan           = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party allocation dry run        = IMPLEMENTED / VALIDATED / CHECKPOINTED
Guarded allocation mutator            = IMPLEMENTED / VALIDATED / CHECKPOINTED
Post-mutation transaction gate        = IMPLEMENTED / VALIDATED / CHECKPOINTED

Actual third-party allocation         = NOT STARTED
Actual third-party merge              = NOT STARTED
```

项目工作目标不是停在 allocation plan，而是：

```text
完成第三方 Vocabulary 的全部 Source / Identity / Learner / Review / Release 前置处理
→ 生成可正式合入 Klose 当前 Vocabulary Anki 的发布状态
→ 到“只剩最终 Anki 合入”时再由用户执行/确认设备侧动作
```

---

## 2. Standing execution directive — CURRENT USER RULE

用户已明确给出持续执行规则：

```text
在第三方 Vocabulary 尚未达到“只剩最终合入 Klose 当前 Anki”之前：
用户说“继续”
→ 授权执行当前流水线的下一步动作
→ 不再要求对内部 allocation / learner / review / release step 重复询问确认
```

解释规则：

1. 每个 `继续` 默认推进 **当前下一 pipeline step**；
2. 若该 step 包含受保护 mutation，`继续` 本身就是该 step 的用户授权证据；
3. 所有 truth-boundary、diff-scope、review、Completion Recheck、`IMPLEMENTED → VALIDATED → CHECKPOINTED` gate 仍必须执行；
4. 一个 step 完成并 CHECKPOINT 后，才进入下一个 step；
5. 若发现数据/架构 blocker，应先修 blocker，而不是机械 mutation；
6. 当系统已经达到“只剩最终 Anki 合入”时停止自动推进，向用户给出最终 Anki 合入动作与影响范围。

该 standing directive 已持久化在：

```text
anki/klose/third_party_vocabulary/allocation/authorization.json
anki/klose/third_party_vocabulary/allocation/plan.json
docs/THIRD_PARTY_ALLOCATION_TRANSACTION_GATE.md
```

---

## 3. New-conversation startup order

继续本任务时固定读取：

```text
AGENTS.md
→ NEXT.md
→ docs/THIRD_PARTY_ALLOCATION_MIGRATION_PLAN.md
→ docs/THIRD_PARTY_ALLOCATION_TRANSACTION_GATE.md
→ docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md
→ docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ current anki/klose/master registries
→ anki/klose/third_party_vocabulary/allocation/plan.json
→ anki/klose/third_party_vocabulary/allocation/authorization.json
```

不要仅凭聊天历史推测状态。

---

## 4. Current Klose Vocabulary / Anki truth

```text
Stable Vocabulary active Notes           = 1189
persistent registry rows incl. merged    = 1194
current max NoteID                       = KV001194

Klose LearnerLevel                       = 4
Learning Admission allowed              = 627
Learning Admission held                 = 345
LearningOrder count / max               = 627 / 627

released Vocabulary Notes                = 972
learner review scope                     = 972
model-reviewed                           = 972
pending                                  = 0

publish/study.csv                        = 972 Notes
publish/anki-import.csv                  = 972 Notes
Vocabulary Anki Updated                  = true
```

当前 `note_registry_extensions.csv` 仍止于：

```text
KV001194 = dream / 梦
```

第三方 allocation 尚未实际写入 Stable Registry；`stable_evidence_bindings.csv` 当前不存在。

Anki FSRS / Review History / Due / Interval / Card State 仍未被第三方处理修改。

---

## 5. Third-party Stage A / Stage-B — CHECKPOINTED

Stage A：

```text
StageACheckpointFingerprint = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
source occurrences          = 18887
Vocabulary identities       = 2820
learner candidates          = 2794
audited deferred surfaces   = 52
explicit exclusions         = a / an / the
```

Stage-B against current 1189 active Stable NoteIDs：

```text
CandidateCount              = 2820
ValidDurableDecisionCount   = 2820
ReviewQueueCount            = 0
SelectedCount               = 0
reuse-existing              = 903
new-stable-identity         = 1821
held                        = 96
learner-excluded held       = 26 / 26
high-risk multiple decided  = 17 / 17
```

Workflow：

```text
run    = 34581146513 / PASS
commit = 153dfabd258eafc039d8545c1ffd1e77f1a362ca
```

---

## 6. Third-party provenance — CHECKPOINTED

20 adapters / 18887 occurrences 属于：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

当前第三方 occurrence 没有真实 `SourceEdition / Revision`，因此：

```text
external evidence may support Stable Identity allocation = yes
Stable Identity implies verified textbook provenance     = no
MasterSourceMappingMutationAuthorized                     = false
```

不得制造 `unknown / unverified / third-party / klose-current` 假 SourceEdition，也不得根据文件名、Grade 或第三方标签猜版本。

actual allocation 后 evidence 关系进入：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

不会进入 Master textbook source map，除非未来有独立可验证的 SourceEdition evidence。

---

## 7. Allocation / transaction readiness — CHECKPOINTED

Current baseline：

```text
persistent registry rows      = 1194
active Stable NoteIDs         = 1189
max NoteID                    = KV001194
reuse-existing                = 903
new-stable-identity           = 1821
held                          = 96
```

若 truth boundary 不变，deterministic allocation range：

```text
KV001195..KV003015
Reserved = false
```

Validated dry run：

```text
identity actions              = 2820
hypothetical registry append  = 1821
external evidence bindings    = 15791
held source occurrences       = 993
run                           = 34587553210 / PASS
```

Guarded mutator / transaction validation：

```text
guarded mutator + recovery/idempotency             = 34588197818 / PASS
authorization-aware control plane                  = 34588814219 / PASS
post-mutation transaction gate                     = 34596833236 / PASS
final integrated transaction checkpoint validation = 34596997031 / PASS
```

Isolated actual-transaction rehearsal verified：

```text
1821 exact new Stable rows
392 historical extension rows unchanged
3015 post-allocation full Stable rows
15791 exact evidence bindings
96 held identities allocated = no
Master/Learner/Release/Publish/Anki mutation = no
pre-commit Completion Recheck = PASS
allocation commit exactly two paths = PASS
post-commit Completion Recheck = PASS
remote push during validation = no
```

Transaction contract：`docs/THIRD_PARTY_ALLOCATION_TRANSACTION_GATE.md`。

---

## 8. Immediate next pipeline step

当前下一步已经明确：

```text
ACTUAL THIRD-PARTY STABLE IDENTITY ALLOCATION
```

下一次用户说 `继续` 时，直接执行：

1. 重新读取 latest main / truth boundary；
2. 重新跑 provenance / allocation plan / dry-run preflight；
3. 用当前 `继续` + standing directive 作为 `UserAuthorizationEvidence`；
4. 将 allocation control plane 切到 `authorized-pending-apply`：

```text
Authorized                           = true
ActualMutationAuthorized             = true
StableNoteIDAllocationAuthorized     = true
MasterSourceMappingMutationAuthorized = false
LearnerMutationAuthorized            = false
ReleaseMutationAuthorized            = false
PublishMutationAuthorized            = false
AnkiMutationAuthorized               = false
```

5. authorization-aware validation PASS；
6. actual allocator 只修改：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

7. pre-commit persistent-state + post-mutation Completion Recheck；
8. commit exactly two mutation paths；
9. post-commit recheck；
10. CHECKPOINT actual allocation；
11. 下一个 pipeline step 转入 third-party Learner Presentation / Learning Admission，而不是直接写 Anki。

---

## 9. Mutation boundary

始终禁止：

```text
promoting unverified third-party occurrence into Master textbook source map
turning held rows into automatic allocation/reuse
surface-word-only dedup when senses differ
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
bulk resetting Learning/Review Cards
changing FSRS / Review History / Due from GitHub-side content operations
mixing ExpressionID operations into Vocabulary updates
```

Current authoritative state：

```text
Stable Vocabulary current max NoteID = KV001194
actual third-party Stable rows        = 0
actual third-party evidence bindings  = 0
current Vocabulary release            = 972
next pipeline step                    = actual third-party Stable identity allocation
execution trigger                     = next user “继续”
```
