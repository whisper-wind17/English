# Third-party Stage-B Identity Reconciliation

## Purpose

Stage A produces reviewed provisional Vocabulary identities. Stage B reconciles each provisional identity against the existing Klose Stable NoteID registry **before any identity mutation, release, or Anki update**.

This layer is intentionally separate from `premerge/identity_candidates.csv`:

```text
premerge candidate map          = derived matching evidence
reconciliation_decisions.csv    = durable reviewed decision truth
```

Exact MatchKey equality is never sufficient to authorize reuse.

## Required truth boundaries

Every reconciliation decision binds to both:

1. `StageACheckpointFingerprint` — the sealed `stage-a-status-v2` content boundary.
2. `CandidateFingerprint` — the exact current premerge row, including current Klose candidate NoteIDs and senses.

If either Stage-A identity truth or the Klose Stable NoteID context changes, the old decision must fail validation and be re-reviewed. Stale decisions are not silently carried forward.

## Premerge snapshot contract

`premerge/readiness.json` is derived state and must describe the current sealed Stage A.

Current contract: `third-party-stage-b-readiness-v2`.

```text
READY
  ActiveReviewBatch       = false
  ReadyForPremergeReview  = true

CURRENT BUT GATED
  ActiveReviewBatch       = true
  ReadyForPremergeReview  = false
```

The builder/checker fails if source occurrence count, Stage-A checkpoint, Identity Preview coverage, audited-defer carry-forward, Klose candidate references, or readiness state drifts.

No previous `Ready=true` snapshot remains authoritative after Stage A changes.

## Reconciliation actions

### `reuse-existing`

The provisional identity is equivalent to one current active Klose Stable NoteID.

Requirements:
- exactly one current `ExistingNoteID` selected;
- selected NoteID appears in the current candidate context;
- no proposed new identity fields;
- `Status=reviewed`;
- `MutationAuthorized=no`.

### `new-stable-identity`

No existing Klose identity is equivalent to the provisional learner identity.

Requirements:
- `ExistingNoteID` empty;
- proposed canonical word / MatchKey / sense present;
- `Status=reviewed`;
- records a future allocation candidate only;
- **does not mint a StableThirdPartyID/NoteID**;
- `MutationAuthorized=no`.

A same-MatchKey Klose candidate does not prohibit this action when explicit semantic review establishes a distinct homograph/learning unit; the decision basis must make the non-equivalence explicit.

### `held`

Current evidence does not permit safe one-to-one reconciliation, or the existing Klose identity boundary itself requires cleanup first.

Requirements:
- no ExistingNoteID selected;
- no proposed new identity;
- `Status=held`;
- explicit rationale;
- `MutationAuthorized=no`.

`held` is a complete Stage-B reconciliation result, not missing work.

## Learner Admission remains independent

```text
Identity reconciled != learner admitted != released != scheduled in Anki
```

Stage B covers all Stage-A provisional identities. Identities excluded by learner policy are retained at Source/Identity layers but are `held` in current Stage B with no ExistingNoteID and no allocation proposal.

Current user-requested content exclusion policy removes from learner admission:

```text
a / an / the                    = 3
cardinal / ordinal number units = 71
TOTAL                            = 74
```

The exclusion does not delete Source Facts or Vocabulary Identity. Other existing learner gates bring total current learner-excluded identities to 97. Current Identity Preview remains 2820; Learner Preview is 2723.

## Audited Stage-A defers

Final Stage A carries 52 current-context audited-defer surfaces. These are explicit valid holds caused primarily by insufficient current source context or policy-boundary ambiguity. They are not active unprocessed work and are not forced into Identity Preview merely to reduce blocker count.

The exact current set is machine-owned in:

```text
anki/klose/third_party_vocabulary/audit/defer_context.csv
anki/klose/third_party_vocabulary/premerge/audited_deferred.csv
```

## Final Stage-A boundary used by Stage B

```text
StageACheckpointFingerprint = 02bec1239e717f8f9141c38cec2fa16947f9c16a6ec372478db26936c5451b0f
SourceOccurrences           = 18887
StageAIdentityCandidates    = 2820
StageALearnerCandidates     = 2723
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

Orthographic/spelling candidate discovery explicitly catches conservative equivalence such as space/hyphen variants and configured spelling variants before a `no-existing-match` candidate can be treated as a future new identity.

## Deterministic review pipeline

Stage B uses the same durable/derived/transient separation as Stage A:

```text
identity_candidates.csv                   derived candidate evidence
→ reconciliation_review_queue.csv         derived unresolved set
→ reconciliation_selected_view.csv        deterministic current batch
→ reviewed_batch.csv / decision_updates   transient reviewed input
→ reconciliation_decisions.csv            durable review truth
→ Completion Recheck
```

Safe deterministic lanes may materialize reviewed proposals only when the equivalence rule itself is sufficient, for example exact MatchKey + exact learner sense, or when there is no exact/orthographic/spelling candidate and the output is only a non-authorizing future identity proposal.

Semantic mismatch, multiple candidates, mixed existing Klose senses, and variant ambiguity remain explicit-review cases.

## Final Stage-B closure — 2026-09-10

Final reconciliation workflow:

```text
workflow run number = #56
workflow run id     = 34420414777
result              = SUCCESS
bot persist commit  = 5b6936852a48abc3df337ada35666d357c5e9dd4
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
reuse-existing                     = 692
new-stable-identity proposal       = 1977
held                               = 151
TOTAL                              = 2820
```

Completion Recheck confirms:

```text
reconciliation coverage            = 100%
high-risk multiple candidates      = 5 / 5 decided
learner-excluded identities        = 97 / 97 held
all durable rows current-fingerprint bound = yes
review queue                        = 0
selected batch                      = 0
Stable NoteID minted                = no
Stage-B mutation authorized         = no
Merge authorized                    = no
Klose identity/learner/release/Anki isolation = pass
```

Independent post-persist diff recheck found only third-party `premerge/**` / `reconciliation/**` review-state changes for the final batch. Across the current Stage-B review sequence, no Klose Master/Learner/Publish/Anki state was changed.

## HOLD POINT / mutation boundary

Stage-B read-only reconciliation is **CLOSED**. Per current user instruction, actual merge/allocation is intentionally not started.

Until a future explicit user instruction opens a new allocation/migration phase, this layer does not:

- append or modify `note_registry*.csv`;
- write `source_identity*.csv`;
- allocate Stable NoteIDs;
- modify Klose learner/release/publish files;
- modify Anki or review history;
- turn `held` decisions into automatic merges;
- admit learner-excluded identities.

A later allocation/migration plan must consume this 100% closed reconciliation set, explicitly define treatment of `held` and proposed-new identities, protect stable NoteIDs and existing FSRS/review history, and pass its own independent Completion Recheck before any mutation is authorized.

## Historical note

The earlier 2026-09-09 snapshot (`eadb2d...`, 7535 source occurrences, 2039 identities, 20 audited defers) was a **historical gated checkpoint**, not the current state. Historical high-risk adjudications were revalidated against the final Stage-A checkpoint; Git history retains the older evidence for auditability.
