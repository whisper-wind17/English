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

`premerge/readiness.json` must describe the current sealed Stage A **and current Klose Stable Vocabulary identity boundary**.

```text
READY
  ActiveReviewBatch       = false
  ReadyForPremergeReview  = true

CURRENT BUT GATED
  ActiveReviewBatch       = true
  ReadyForPremergeReview  = false
```

The builder/checker fails on source count, checkpoint, Identity Preview coverage, audited-defer carry-forward, Klose candidate reference, or readiness drift. A previous `Ready=true` snapshot is never authoritative after Stage A **or Klose Stable identity state** changes.

Stable Vocabulary mutation can be produced by GitHub Actions. A commit made with the workflow `GITHUB_TOKEN` does not recursively trigger ordinary `push` workflows, so Stage-B readiness also listens to successful completion of Stable Vocabulary allocation/build workflows via `workflow_run`. This prevents a valid but stale premerge snapshot from surviving a Klose identity expansion.

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

## Current premerge boundary

```text
StageACheckpointFingerprint = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
SourceOccurrences           = 18887
StageAIdentityCandidates    = 2820
StageALearnerCandidates     = 2794
AuditedDeferredSurfaces     = 52
KloseActiveNoteIDs          = 1189
exact-multiple              = 17
exact-single                = 974
no-existing-match           = 1822
orthographic-single         = 6
spelling-single             = 1
ActiveReviewBatch           = false
ReadyForPremergeReview      = true
StageBMutationAuthorized    = false
StableThirdPartyIDMinted    = false
MergeAuthorizedRows         = 0
```

This boundary was refreshed after Grade 5–6 added 288 Stable Vocabulary Notes. The previous 901-NoteID premerge snapshot was therefore stale: 218 third-party CandidateFingerprints changed and were retired from durable truth before re-review. The lifecycle trigger fix is commit `36d420ee127c8cb7be680f58e621a08e68faa706`; refreshed premerge state was persisted by `6452c351c65d3cbf4f75986b6ad469d13c3978a7`.

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

A learner-policy or Klose identity change can alter current candidate evidence. To preserve auditability without mechanically re-reviewing unchanged rows, Stage B may reuse a historical decision only when all of the following hold:

```text
same ProvisionalIdentityKey
+ exact current CandidateFingerprint == historical CandidateFingerprint
+ historical MutationAuthorized=no
+ historical action/status valid
```

The rebound decision is written against the current Stage-A checkpoint and current fingerprint. If even one CandidateFingerprint field changes, the row cannot use this path and must be explicitly reviewed.

After the Grade 5–6 Stable Vocabulary expansion, 2602 old decisions remained fingerprint-valid; 218 changed rows were invalidated and reprocessed. The changed set included exact-match, multiple-candidate, orthographic/spelling variant, and semantic-review cases. No Stable NoteID was allocated.

## Final Stage-B closure — current checkpoint

Final reconciliation workflow:

```text
workflow run number = #75
workflow run id     = 34581146513
result              = SUCCESS
bot persist commit  = 153dfabd258eafc039d8545c1ffd1e77f1a362ca
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
reuse-existing                     = 903
new-stable-identity proposal       = 1821
held                               = 96
TOTAL                              = 2820
```

Completion Recheck confirms:

```text
reconciliation coverage                    = 100%
high-risk multiple candidates              = 17 / 17 decided
learner-excluded identities                = 26 / 26 held
all durable rows current-fingerprint bound = yes
review queue                               = 0
selected batch                             = 0
Stable NoteID minted                       = no
Stage-B mutation authorized                = no
Merge authorized                           = no
Klose identity/learner/release/Anki isolation = pass
```

The changed semantic rows were reviewed conservatively. Same spelling was not treated as equivalence: examples retained as future new-identity proposals include `take=拿/取/带走`, `heavy=重的`, `turn=转动`, and `way=道路/方向`; mixed Stage-A targets such as `paint`, `email`, `Spanish`, and `open` remain `held` rather than being forced into an existing Klose sense.

Post-persist state has `reconciliation_next_batch.json = 2820/2820`, queue/selected zero, queue and selected-view header-only, and no mutation outside third-party premerge/reconciliation state.

## HOLD POINT / mutation boundary

Stage-B read-only reconciliation is **CLOSED** against the current 1189 active Klose Stable NoteIDs. Actual merge/allocation is intentionally not started.

Until a future explicit merge instruction, this layer does not:

- append or modify Klose `note_registry*.csv`;
- write Klose source identity mappings;
- allocate Stable NoteIDs;
- modify Klose learner/release/publish files;
- modify Anki or review history;
- turn `held` into automatic merges.

A later allocation/migration plan must consume this 100% closed reconciliation set, explicitly define treatment of `held` and proposed-new identities, protect stable NoteIDs and existing FSRS/review history, and pass its own independent Completion Recheck before any mutation is authorized.

## Historical note

Two earlier boundaries are historical only:

- checkpoint `02bec123...`: 2723 learner candidates because 71 cardinal/ordinal identities were temporarily excluded by learner policy;
- Stage-B run #68 / commit `7a6ca633fb00e8eb4ffcb5484ede62d149925c1e`: 2820/2820 reconciliation against only 901 active Klose NoteIDs, with `719 reuse / 2021 new / 80 held`.

The current authoritative Stage-A checkpoint remains `c6083db4...`, with 2794 learner candidates. The current authoritative Stage-B identity boundary is the 1189-NoteID closure documented above.
