# Third-party Vocabulary Allocation / Migration Plan

## Status

本计划已经从 pre-allocation plan 转为 **executed / validated / checkpointed**。

Authoritative execution truth：

```text
Stage-A checkpoint              = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
Stage-B candidates / decisions  = 2820 / 2820
reuse-existing                  = 903
new-stable-identity             = 1821
held                            = 96
allocation execution run        = 34608158097 / PASS
allocation commit               = fe0d1f04c2eae1cf5d492673dd79aef302691d39
committed-state validation      = 34608453454 / PASS
```

Execution receipt：

```text
anki/klose/third_party_vocabulary/allocation/execution_receipt.json
```

Post-allocation Stable truth：

```text
persistent registry rows        = 3015
active Stable NoteIDs           = 3010
max NoteID                      = KV003015
new Stable rows                 = 1821
new NoteID range                = KV001195..KV003015
external evidence bindings      = 15791
held identities allocated       = 0
```

原 `1194 / 1189 / KV001194` 仅保留为 pre-allocation audit baseline，不再是 current Stable truth。

---

## 1. Allocation result

Stage-B 三类 action 的执行结果：

### `reuse-existing` — 903

```text
Stable Registry mutation = none
ExistingNoteID           = reviewed existing Stable NoteID
External evidence binding = yes
```

现有 identity fields 与既有 learner presentation 均未因第三方释义改写。

### `new-stable-identity` — 1821

实际 append-only allocation：

```text
KV001195..KV003015
```

每条新 row：

```text
CanonicalWord <- Stage-B ProposedCanonicalWord
MatchKey      <- Stage-B ProposedMatchKey
SenseLabel    <- Stage-B ProposedSense
PrimaryOriginKey = third-party-vocabulary|<ProvisionalIdentityKey>
CreatedSource = third-party-vocabulary
CreatedSourceBook = external-evidence-corpus
Status = active
```

历史 Stable rows 未重编号、未删除、未复用。

### `held` — 96

```text
NoteID allocation          = no
ExistingNoteID selection   = no
External evidence binding  = no
Master source promotion    = no
```

`held` 仍是当前 evidence boundary 下的完整结果，不是自动 backlog。

---

## 2. Provenance result

Third-party adapter occurrences 仍属于：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

actual allocation 创建：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

其中：

```text
rows           = 15791
EvidenceStatus = external-unverified-edition
```

该表只表达 external evidence → Stable NoteID 关系，不代表已核实 SourceEdition / Revision。

仍禁止：

```text
unverified third-party occurrence
→ anki/klose/master/source_identity_extensions.csv
```

---

## 3. Transaction / validation evidence

设计验证：

```text
allocation dry run                     = 34587553210 / PASS
guarded mutator                         = 34588197818 / PASS
post-mutation transaction gate design  = 34596833236 / PASS
```

实际执行：

```text
run                                     = 34608158097 / PASS
commit                                  = fe0d1f04c2eae1cf5d492673dd79aef302691d39
committed-state validation              = 34608453454 / PASS
```

actual allocation commit 精确只包含：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

验证确认：

```text
historical extension rows unchanged    = 392
new Stable rows exact                   = 1821
full persistent Stable rows             = 3015
active Stable NoteIDs                   = 3010
external evidence bindings exact        = 15791
held identities allocated/bound         = no
Master source mapping mutation          = no
Learner / Release / Publish mutation    = no
Anki mutation                           = no
Compare-and-swap push                   = PASS
```

第一次 execution run `34608014656` 在 actual apply + Completion Recheck 已 PASS 后，因为 shell diff-scope 检查没有统计 untracked evidence file 而 fail；未发生 remote push。修复后 run `34608158097` 完整通过。

---

## 4. Current lifecycle boundary

Stable identity allocation 已完成，不得再次把 pre-allocation dry run 当作待执行计划。

下一 lifecycle：

```text
Stable Identity
→ Learner Presentation at LearnerLevel=4
→ explicit Learning Admission + LearningOrder
→ content review / fingerprint approval
→ Release Registry
→ generated study.csv / anki-import.csv
→ Release Gate
→ final Anki merge
```

当前 release / publish 仍维持 allocation 前状态，972 Vocabulary Notes；allocation 本身没有改变 FSRS / Review History / Due / Interval / Card State。

下一 pipeline step 以根目录 `NEXT.md` 为准。
