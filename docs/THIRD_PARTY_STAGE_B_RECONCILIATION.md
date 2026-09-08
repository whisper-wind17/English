# Third-party Stage-B Identity Reconciliation

## Purpose

Stage A produces reviewed provisional learner identities. Stage B reconciles each provisional identity against the existing Klose Stable NoteID registry before any identity mutation, release, or Anki update.

This layer is intentionally separate from `premerge/identity_candidates.csv`:

```text
premerge candidate map = derived matching evidence
reconciliation_decisions.csv = durable reviewed decision truth
```

Exact MatchKey equality is never sufficient to authorize reuse.

## Required truth boundaries

Every reconciliation decision binds to both:

1. `StageACheckpointFingerprint` — the sealed `stage-a-status-v2` content boundary.
2. `CandidateFingerprint` — the exact current premerge row, including current Klose candidate NoteIDs and senses.

If either Stage-A identity truth or the Klose Stable NoteID context changes, the old decision must fail validation and be re-reviewed.

## Premerge snapshot states

`premerge/readiness.json` is derived state, but it must always describe the **current sealed Stage A**, including when Stage A is not yet ready for reconciliation.

Current contract is `third-party-stage-b-readiness-v2`:

```text
StageAStatusVersion
StageACheckpointFingerprint
SourceOccurrences
ActiveReviewBatch
ReadyForPremergeReview
```

Two valid states exist:

```text
READY
  ActiveReviewBatch       = false
  ReadyForPremergeReview  = true

CURRENT BUT GATED
  ActiveReviewBatch       = true
  ReadyForPremergeReview  = false
```

A gated snapshot is not stale. It is a current read-only description of the present Stage-A/Klose candidate relation, but Stage-B durable reconciliation validation must not run until the gate becomes ready.

The builder/checker must fail if:

- `SourceOccurrences` differs from the sealed Stage-A source union;
- the snapshot does not bind the current `StageACheckpointFingerprint`;
- candidate coverage differs from the current Identity Preview;
- deferred carry-forward differs from the current Stage-A review queue;
- `ReadyForPremergeReview` does not reflect the current Stage-A review batch state.

No previous `Ready=true` snapshot may remain authoritative after Stage A changes.

## Actions

### `reuse-existing`

The provisional identity is equivalent to one current active Klose Stable NoteID.

Requirements:
- exactly one `ExistingNoteID` is selected;
- selected NoteID is active and present in the current candidate row;
- no proposed new identity fields;
- `Status=reviewed`;
- `MutationAuthorized=no`.

### `new-stable-identity`

No existing Klose identity is equivalent to the provisional learner identity.

Requirements:
- `ExistingNoteID` empty;
- `ProposedCanonicalWord`, `ProposedMatchKey`, `ProposedSense` present;
- `Status=reviewed`;
- this is only a reviewed allocation candidate — no NoteID is minted here;
- `MutationAuthorized=no`.

### `held`

Current evidence does not permit a safe one-to-one reconciliation, or the existing Klose identity boundary itself requires cleanup first.

Requirements:
- no existing NoteID selected;
- no proposed new identity;
- `Status=held`;
- explicit rationale;
- `MutationAuthorized=no`.

## Learner Admission remains independent

Stage-B Identity reconciliation covers all Stage-A provisional identities, including identities currently excluded by the learner grammar gate.

```text
Identity reconciled != learner admitted != released != scheduled in Anki
```

The current learner-quarantined identities may be reconciled at the identity layer, but cannot enter the current learner release unless the learner-stage gate changes separately.

## Audited Stage-A defers

Current Stage A carries 20 v6 audited-defer surfaces. They are not provisional Identity candidates and must not appear in `reconciliation_decisions.csv`:

```text
fan / feel / flies / french / get / kind / letter / light / like / line /
little / mouse / pass / plant / put up / right / sound / square / too / watch
```

They remain explicit carry-forward exceptions in `premerge/audited_deferred.csv` until source/canonical/policy context changes. Do not force occurrence partition merely to reduce the blocker count.

## Current gated snapshot — 2026-09-09

Current Stage-A content boundary:

```text
StageACheckpointFingerprint = eadb2d5163ff3193cc735b834a20dcec393df51f8d9d48867f93b5532060a556
SourceOccurrences           = 7535
StageAIdentityCandidates    = 2039
StageALearnerCandidates     = 2024
AuditedDeferredSurfaces     = 20
KloseActiveNoteIDs          = 901
exact-multiple              = 7
exact-single                = 811
no-existing-match           = 1221
ActiveReviewBatch           = true
ReadyForPremergeReview      = false
```

The active Stage-A review batch is the targeted orthographic audit for `program / programme`. Therefore Stage-B durable reconciliation remains gated even though the premerge snapshot itself is current and fully validated.

Validation:

```text
Stage-B readiness workflow #5 / 34292245929 = SUCCESS
reconciliation workflow #5 / 34292266672 = SUCCESS
reconciliation decision validation = SKIPPED BY GATE
Klose isolation = PASS
```

## Mutation boundary

This reconciliation layer does not:

- append or modify `note_registry*.csv`;
- write `source_identity*.csv`;
- allocate Stable NoteIDs;
- modify learner/release/publish files;
- modify Anki or review history.

A later allocation/migration plan must consume a **100% closed reconciliation decision set**, run an independent Completion Recheck, and remain read-only until explicit Stage-B mutation gating is approved.

## Historical high-risk adjudication

The prior exact-multiple review covered:

```text
can
cook#person
cook#verb
free
milk
over
speak
```

Historical reviewed results:

```text
can          -> reuse KV000074 (modal)
cook#person  -> held; KV000424 still has legacy mixed noun/verb SenseLabel
cook#verb    -> reuse KV000805 (actual-textbook distinct verb identity)
free         -> reuse KV000502 (空闲的)
milk         -> reuse KV000088 (牛奶)
over         -> new-stable-identity candidate (在……上方；在……上面)
speak        -> held; provisional broad sense overlaps KV000705 and KV000901
```

These historical decisions are review evidence only until revalidated against the current Stage-A checkpoint and current candidate fingerprints. No row authorizes merge or NoteID allocation.
