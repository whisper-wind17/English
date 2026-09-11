# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

当前 Klose 主系统与第三方 Vocabulary 状态：

```text
Grade 5–6 Vocabulary GitHub Release   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated               = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Grade 5–6 Expressions GitHub Release  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Anki Updated              = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation    = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract       = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party allocation dry run        = IMPLEMENTED / VALIDATED / CHECKPOINTED
Guarded allocation mutator            = IMPLEMENTED / VALIDATED / CHECKPOINTED
Post-mutation transaction gate        = IMPLEMENTED / VALIDATED / CHECKPOINTED
Actual third-party Stable allocation  = IMPLEMENTED / VALIDATED / CHECKPOINTED

Third-party Learner Presentation      = NOT STARTED
Third-party Learning Admission        = NOT STARTED
Third-party Review / Release          = NOT STARTED
Third-party Anki merge                = NOT READY / NOT STARTED
```

项目总目标保持不变：

```text
完成第三方 Vocabulary 的 Source / Identity / Learner / Review / Release 全部前置处理
→ 生成可正式合入 Klose 当前 Vocabulary Anki 的发布状态
→ 到“只剩最终 Anki 合入”时停止自动推进并给出设备侧合入动作
```

---

## 2. Standing execution directive — CURRENT USER RULE

用户已明确：

```text
在第三方 Vocabulary 尚未达到“只剩最终合入 Klose 当前 Anki”之前：
用户说“继续” / “继续处理”
→ 授权执行当前流水线的下一步动作
→ 不再对内部 allocation / learner / review / release step 重复询问确认
```

约束仍然有效：

1. 每次 `继续` 推进一个 pipeline step；
2. 每一步仍必须经过 truth-boundary / diff-scope / Completion Recheck；
3. `IMPLEMENTED → VALIDATED → CHECKPOINTED` 不得跳过；
4. 出现 blocker 先修 blocker；
5. 到最终 Anki 合入前停止自动推进。

Standing directive 真源：

```text
anki/klose/third_party_vocabulary/allocation/authorization.json
anki/klose/third_party_vocabulary/allocation/plan.json
docs/THIRD_PARTY_ALLOCATION_TRANSACTION_GATE.md
```

---

## 3. Startup order

继续本任务时固定读取：

```text
AGENTS.md
→ NEXT.md
→ anki/klose/third_party_vocabulary/allocation/execution_receipt.json
→ anki/klose/third_party_vocabulary/allocation/plan.json
→ anki/klose/third_party_vocabulary/allocation/authorization.json
→ docs/THIRD_PARTY_ALLOCATION_MIGRATION_PLAN.md
→ docs/THIRD_PARTY_ALLOCATION_TRANSACTION_GATE.md
→ docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md
→ docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ relevant learner/review/release files and tools
```

不要再把 pre-allocation `KV001194` baseline 当作当前 Stable truth；它现在仅是 execution audit baseline。

---

## 4. Current Stable Vocabulary truth after actual allocation

Actual allocation commit：

```text
commit = fe0d1f04c2eae1cf5d492673dd79aef302691d39
run    = 34608158097 / PASS
```

Allocation commit 只包含：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

Post-allocation truth：

```text
persistent Stable registry rows        = 3015
active Stable NoteIDs                  = 3010
current max NoteID                     = KV003015
historical extension rows unchanged    = 392
new third-party Stable rows            = 1821
new NoteID range                       = KV001195..KV003015
external evidence bindings             = 15791
held identities allocated/bound        = 0
```

Stage-B action closure remains：

```text
reuse-existing                         = 903
new-stable-identity                    = 1821
held                                   = 96
TOTAL                                  = 2820
```

Allocation did **not** modify：

```text
Master textbook source identity mapping
Learner Presentation
Learning Admission / LearningOrder
Review registry
Release registry
publish/study.csv
publish/anki-import.csv
Anki FSRS / Review History / Due / Interval / Card State
Expressions
```

Current Vocabulary release therefore remains：

```text
released Vocabulary Notes              = 972
publish/study.csv                       = 972
publish/anki-import.csv                 = 972
```

---

## 5. Allocation validation evidence

Execution receipt：

```text
anki/klose/third_party_vocabulary/allocation/execution_receipt.json
```

Committed-state checker：

```text
tools/validate_third_party_allocation_committed_state.py
```

Validation evidence：

```text
pre-allocation dry run                  = 34587553210 / PASS
guarded mutator validation              = 34588197818 / PASS
transaction design validation           = 34596833236 / PASS
actual execution                        = 34608158097 / PASS
allocation commit                       = fe0d1f04c2eae1cf5d492673dd79aef302691d39
committed-state validation              = 34608453454 / PASS
```

The first execution attempt `34608014656` stopped after actual apply + Completion Recheck because the shell diff-scope check omitted an untracked new evidence file. No push occurred. The checker bug was fixed; retry `34608158097` passed CAS push. This failed run is historical validation evidence, not an incomplete repository mutation.

---

## 6. Provenance boundary after allocation

Third-party occurrence remains：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

`stable_evidence_bindings.csv` now records external evidence → Stable NoteID relationships, but it does not assert verified SourceEdition / Revision.

仍禁止：

```text
unverified third-party occurrence
→ anki/klose/master/source_identity_extensions.csv
```

除非未来取得真实教材/同 Edition 官方 evidence。

---

## 7. Immediate next pipeline step

下一步已经切换为：

```text
THIRD-PARTY LEARNER PRESENTATION + LEARNING ADMISSION PREPARATION
```

下一次用户说 `继续` / `继续处理` 时，直接执行：

1. 读取当前 3010 active Stable identities 与 2794 Stage-A learner candidates；
2. 明确哪些 third-party identities 进入 Klose `LearnerLevel=4` presentation scope；
3. 对 903 reuse-existing 保留现有 learner content，禁止因第三方释义覆盖已稳定 presentation；
4. 对 1821 new Stable identities 生成 LearnerLevel=4 presentation candidate；
5. 96 held 不进入 learner scope；
6. 设计/生成 explicit Learning Admission 与 deterministic LearningOrder，不能由 Source Grade 机械推导；
7. 运行 learner-level content / identity / duplication / workload gates；
8. Completion Recheck 后 CHECKPOINT；
9. 不直接修改 Release / Publish / Anki，除非该 next step 的 contract 明确进入对应生命周期。

重点：

```text
Source Grade ≠ LearnerLevel
Stable identity allocated ≠ learner admitted ≠ released ≠ Anki scheduled
```

---

## 8. Mutation boundary

始终禁止：

```text
promoting unverified third-party occurrence into Master textbook source map
turning held rows into automatic allocation/reuse
surface-word-only dedup when senses differ
overwriting existing reused Note learner presentation from third-party definitions
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
bulk resetting Learning/Review Cards
changing FSRS / Review History / Due from GitHub-side content operations
mixing ExpressionID operations into Vocabulary updates
```

Current authoritative state：

```text
Stable Vocabulary current max NoteID = KV003015
persistent / active Stable Notes      = 3015 / 3010
actual third-party Stable rows        = 1821
actual third-party evidence bindings  = 15791
current Vocabulary release            = 972
actual Stable allocation              = CHECKPOINTED
next pipeline step                    = third-party Learner Presentation + Admission preparation
execution trigger                     = next user “继续” / “继续处理”
```
