# Third-party Stage-B Identity Reconciliation

## Purpose

Stage A produces reviewed provisional Vocabulary identities. Stage B reconciles each provisional identity against the existing Klose Stable NoteID registry **before any identity mutation, release, or Anki update**.

```text
premerge candidate map          = derived matching evidence
reconciliation_decisions.csv    = durable reviewed decision truth
```

Exact MatchKey equality is never sufficient to authorize reuse.

## Required truth boundaries

Every reconciliation decision binds to both:

1. `StageACheckpointFingerprint` — sealed Stage-A content boundary.
2. `CandidateFingerprint` — exact current premerge row, including learner admission and current Klose candidate NoteIDs/senses.

If either changes, the old decision is stale. It may only be revalidated when the entire CandidateFingerprint is byte-for-byte unchanged; otherwise explicit review is required.

## Premerge snapshot contract

`premerge/readiness.json` must describe the current sealed Stage A.

```text
READY
  ActiveReviewBatch       = false
  ReadyForPremergeReview  = true

CURRENT BUT GATED
  ActiveReviewBatch       = true
  ReadyForPremergeReview  = false
```

The builder/checker fails on source count, checkpoint, Identity Preview coverage, audited-defer carry-forward, Klose candidate reference, or readiness drift. A previous `Ready=true` snapshot is never authoritative after Stage A changes.

## Reconciliation actions

### `reuse-existing`

Equivalent to one current active Klose Stable NoteID. Requires a current candidate NoteID, no proposed identity fields, `Status=reviewed`, `MutationAuthorized=no`.

### `new-stable-identity`

No existing Klose identity is equivalent. Records canonical word / MatchKey / sense as a **future allocation proposal only**; it does not mint StableThirdPartyID/NoteID and always has `MutationAuthorized=no`.

A same-MatchKey Klose candidate does not prohibit this action when explicit semantic review establishes a distinct homograph/learning unit.

### `held`

Current evidence does not permit safe one-to-one reconciliation, or the existing Klose identity boundary itself requires cleanup. It selects no ExistingNoteID, proposes no identity, and has `MutationAuthorized=no`.

`held` is a complete reconciliation result, not missing work.

## Learner Admission remains independent

```text
Identity reconciled != learner admitted != released != scheduled in Anki
```

Current explicit content policy excludes only:

```text
a / an / the = 3
```

On 2026-09-10 the user explicitly reversed the earlier number exclusion: the 71 cardinal/ordinal number learning units are **admitted** to the third-party learner vocabulary. They remain normal Vocabulary identities and may participate in Stage-B reconciliation. The number classifier is retained as an adversarial learner-gate check, not an exclusion rule.

Current Stage-A counts:

```text
Identity Preview          = 2820
Learner Preview           = 2794
Total learner-excluded    = 26
Explicit article excludes = 3
```

The remaining learner exclusions come from pre-existing learner gates. Source/Identity truth is not deleted by learner policy.

## Audited Stage-A defers

Final Stage A carries 52 current-context audited-defer surfaces. They are explicit valid holds caused primarily by insufficient current source context or policy-boundary ambiguity, not active unprocessed work.

Machine truth:

```text
anki/klose/third_party_vocabulary/audit/defer_context.csv
anki/klose/third_party_vocabulary/premerge/audited_deferred.csv
```

## Current final Stage-A boundary

```text
Stage-A workflow            = #443 / 34425589766 = SUCCESS
StageACheckpointFingerprint = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
SourceOccurrences           = 18887
StageAIdentityCandidates    = 2820
StageALearnerCandidates     = 2794
AuditedDeferredSurfaces     = 52
KloseActiveNoteIDs          = 901
exact-multiple              = 5
exact-single                = 781
no-existing-match           = 2029
orthographic-single         = 4
spelling-single             = 1
ActiveReviewBatch           = false
ReadyForPremergeReview      = true
StageBMutationAuthorized    = false
StableThirdPartyIDMinted    = false
MergeAuthorizedRows         = 0
```

## Deterministic review pipeline

```text
identity_candidates.csv
→ reconciliation_review_queue.csv
→ reconciliation_selected_view.csv
→ reviewed_batch.csv / decision_updates.csv
→ reconciliation_decisions.csv
→ Completion Recheck
```

Safe deterministic lanes may materialize proposals only when the rule itself is sufficient, e.g. exact MatchKey + exact learner sense, or no exact/orthographic/spelling candidate where the result is only a non-authorizing future identity proposal. Semantic mismatch, multiple candidates, mixed Klose senses, and variant ambiguity require explicit review.

### Exact historical revalidation

A learner-policy change can alter Stage-A checkpoint without altering most candidate evidence. To preserve auditability without mechanically re-reviewing unchanged rows, Stage B may reuse a historical decision only when all of the following hold:

```text
same ProvisionalIdentityKey
+ exact current CandidateFingerprint == historical CandidateFingerprint
+ historical MutationAuthorized=no
+ historical action/status valid
```

The rebound decision is written against the **current** Stage-A checkpoint and current fingerprint. If even one CandidateFingerprint field changes, the row cannot use this path and must be explicitly reviewed.

This mechanism was exercised after cardinal/ordinal admission: number identities whose learner-admission evidence changed were explicitly reviewed as needed, while unchanged semantic decisions were revalidated from Git history. No Stable NoteID was allocated.

## Final Stage-B closure — current checkpoint

Final reconciliation workflow:

```text
workflow run number = #68
workflow run id     = 34426580726
result              = SUCCESS
bot persist commit  = 7a6ca633fb00e8eb4ffcb5484ede62d149925c1e
```

Final machine state:

```text
CandidateCount                     = 2820
ValidDurableDecisionCount          = 2820
ReviewQueueCount                   = 0
SelectedCount                      = 0
ReviewLane                         = <none>
ExecutionReady                     = false
AutoExecutable                     = false
```

Final durable action distribution:

```text
reuse-existing                     = 719
new-stable-identity proposal       = 2021
held                               = 80
TOTAL                              = 2820
```

Completion Recheck confirms:

```text
reconciliation coverage            = 100%
high-risk multiple candidates      = 5 / 5 decided
learner-excluded identities        = 26 / 26 held
all durable rows current-fingerprint bound = yes
review queue                        = 0
selected batch                      = 0
Stable NoteID minted                = no
Stage-B mutation authorized         = no
Merge authorized                    = no
Klose identity/learner/release/Anki isolation = pass
```

Independent post-persist recheck confirms `reconciliation_next_batch.json` is 2820/2820 with queue/selected zero; queue and selected-view are header-only; final bot diff touches only third-party premerge/reconciliation state and removes the transient reviewed batch.

## HOLD POINT / mutation boundary

Stage-B read-only reconciliation is **CLOSED**. Per current user instruction, actual merge/allocation is intentionally not started.

Until a future explicit merge instruction, this layer does not:

- append or modify Klose `note_registry*.csv`;
- write Klose source identity mappings;
- allocate Stable NoteIDs;
- modify Klose learner/release/publish files;
- modify Anki or review history;
- turn `held` into automatic merges.

A later allocation/migration plan must consume this 100% closed reconciliation set, explicitly define treatment of `held` and proposed-new identities, protect stable NoteIDs and existing FSRS/review history, and pass its own independent Completion Recheck before any mutation is authorized.

## Historical note

The previous checkpoint `02bec123...` had 2723 learner candidates because 71 cardinal/ordinal identities were temporarily excluded by learner policy. That state is historical only. The current authoritative checkpoint is `c6083db4...`, with 2794 learner candidates and only `a/an/the` explicitly content-excluded.
