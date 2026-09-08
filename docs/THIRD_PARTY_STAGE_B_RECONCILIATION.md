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

The current 15 learner-quarantined identities may be reconciled at the identity layer, but cannot enter the current learner release unless the learner-stage gate changes separately.

## Audited Stage-A defers

The 13 v6 audited-defer surfaces are not provisional Identity candidates and must not appear in `reconciliation_decisions.csv`. They remain explicit carry-forward exceptions in `premerge/audited_deferred.csv` until source/context/policy changes.

## Mutation boundary

This reconciliation layer does not:

- append or modify `note_registry*.csv`;
- write `source_identity*.csv`;
- allocate Stable NoteIDs;
- modify learner/release/publish files;
- modify Anki or review history.

A later allocation/migration plan must consume a **100% closed reconciliation decision set**, run an independent Completion Recheck, and remain read-only until explicit Stage-B mutation gating is approved.

## First high-risk batch

The current `exact-multiple` candidate class contains seven provisional identities:

```text
can
cook#person
cook#verb
free
milk
over
speak
```

Initial reviewed results:

```text
can          -> reuse KV000074 (modal)
cook#person  -> held; KV000424 still has legacy mixed noun/verb SenseLabel
cook#verb    -> reuse KV000805 (actual-textbook distinct verb identity)
free         -> reuse KV000502 (空闲的)
milk         -> reuse KV000088 (牛奶)
over         -> new-stable-identity candidate (在……上方；在……上面)
speak        -> held; provisional broad sense overlaps KV000705 and KV000901
```

These decisions are content truth only. No row authorizes merge or NoteID allocation.
