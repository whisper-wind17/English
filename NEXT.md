# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. 启动顺序

所有 Klose 任务固定读取：`AGENTS.md → NEXT.md → 当前任务 docs → source_freeze.json → stage_a_status.json → next_batch.json → premerge/readiness.json`。动态进度以 machine state 为准。

当前任务文档：`docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。

## 2. Current phase

```text
Phase A1 Source Adapter Bulk Ingestion = CLOSED
SOURCE FREEZE                         = ESTABLISHED
Phase A2 Global Identity Closure      = CLOSED
Stage B Identity Reconciliation       = CURRENT (read-only review)
Stage B mutation / NoteID allocation  = GATED
```

SOURCE FREEZE：20 adapters / 18887 occurrences / 3763 surfaces；source fingerprints 未变化。Stage A 全程未修改 Klose Master/Learner/Release/Publish/Anki。

## 3. Final Stage-A seal

Latest/final sealed workflow：**#429 / 34413943452 = SUCCESS**

```text
sealed input commit                = 10b013ed8f4893989e6ba8931a5731e06401d6b4
Durable Identity decisions         = 3871
Identity Vocabulary Preview        = 2820
Learner Vocabulary Preview         = 2797
Review blockers                    = 52
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
NextBatch SelectedCount            = 0
NextBatch ExecutionReady           = false
NextBatch GateReason               = no active review batch
CheckpointFingerprint              = 3a3d8728e96901ce66272422eb81d25bd44e59146c00c15000fa482e09fccecc
```

Residual 52 blockers are exactly the current-context audited-defer registry (`defer_context.csv`): overwhelmingly `evidence-insufficient`, plus explicit policy-boundary cases. They are valid holds, not active unprocessed work. Do not guess meanings to force blocker=0.

Final closure evidence:
- #429 full Stage-A Validation Gate PASS: Completion Recheck / learner gate / audit recheck / Klose isolation / seal / bot persist.
- Completion Recheck includes duplicate/canonical collision guards; seal verify includes review/defer duplicate-MatchKey checks.
- independent post-seal diff PASS; bot persist changed only third-party workspace.
- `NextBatch=0` and no active review batch.

## 4. Stage-B readiness

Readiness workflow：**#6 / 34414390985 = SUCCESS**

Current `premerge/readiness.json`:

```text
StageACheckpointFingerprint = 3a3d8728e96901ce66272422eb81d25bd44e59146c00c15000fa482e09fccecc
SourceOccurrences           = 18887
StageAIdentityCandidates    = 2820
StageALearnerCandidates     = 2797
AuditedDeferredSurfaces     = 52
ActiveReviewBatch           = false
ReadyForPremergeReview      = true
KloseActiveNoteIDs          = 901
exact-multiple              = 5
exact-single                = 781
no-existing-match           = 2034
StageBMutationAuthorized    = false
StableThirdPartyIDMinted    = false
MergeAuthorizedRows         = 0
```

Readiness bot persist changed only `anki/klose/third_party_vocabulary/premerge/**`.

CI fix: `.github/workflows/third-party-stage-b-readiness.yml` now listens to successful `Prepare Third-party Vocabulary Stage A` `workflow_run` and checks out current `main`, preventing readiness from remaining stale after Stage-A bot persist.

## 5. NEXT — Stage-B reconciliation review

Follow `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md` and keep Stage B read-only.

Execution order:

```text
verify final Stage-A seal
→ verify current premerge readiness
→ inspect/revalidate existing reconciliation_decisions.csv against current Stage-A checkpoint + CandidateFingerprint
→ resolve all 5 exact-multiple candidates first
→ process exact-single / no-existing-match reconciliation in deterministic batches
→ require 100% reconciliation closure or explicit held rows
→ independent Completion Recheck
→ only then design a later allocation/migration gate
```

Stage-B decision actions remain only:
- `reuse-existing`
- `new-stable-identity`
- `held`

Every durable decision must bind current `StageACheckpointFingerprint` and exact `CandidateFingerprint`; `MutationAuthorized=no` throughout this phase. Do not mint StableThirdPartyID/NoteID, do not modify Klose identity/source/learner/release/publish/Anki state.
