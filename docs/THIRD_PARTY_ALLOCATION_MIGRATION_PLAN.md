# Third-party Vocabulary Allocation / Migration Plan

## Purpose

Stage-B reconciliation is closed against the current Klose Stable Vocabulary boundary, but **actual merge/allocation remains unauthorized**. This document defines the mutation contract that must exist before any third-party identity is written into Klose persistent registries.

Current authoritative boundary:

```text
Stage-A checkpoint                = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
Klose active Stable NoteIDs       = 1189
persistent registry rows          = 1194
current max NoteID                = KV001194
Stage-B candidates / decisions    = 2820 / 2820
reuse-existing                    = 903
new-stable-identity proposal      = 1821
held                              = 96
learner-excluded held             = 26
review queue / selected batch     = 0 / 0
```

Machine contract: `anki/klose/third_party_vocabulary/allocation/plan.json`.

Validation entry: `tools/check_third_party_allocation_plan.py`.

---

## 1. Truth boundary and invalidation

The allocation plan is valid only against the exact closed Stage-B truth and exact current Stable Vocabulary registry.

It binds:

```text
StageACheckpointFingerprint
reconciliation_decisions.csv Git blob SHA
identity_candidates.csv Git blob SHA
note_registry.csv Git blob SHA
note_registry_extensions.csv Git blob SHA
```

Any change to Stage A, Stage B decisions, or either Stable Registry invalidates this plan. A changed registry count that happens to produce the same maximum NoteID is still a new truth boundary and requires re-planning.

No NoteID is reserved by this plan.

---

## 2. Three Stage-B action classes

### `reuse-existing` — 903

Future authorized mutation must **not change the Stable Registry** for these identities.

The Stage-B `ExistingNoteID` remains the identity. Future work may add third-party provenance bindings to that NoteID after the provenance contract is resolved, but it must not:

- allocate a duplicate NoteID;
- rewrite CanonicalWord / MatchKey / SenseLabel merely to match third-party wording;
- change existing learner presentation or release state as a side effect.

### `new-stable-identity` — 1821

These are reviewed future allocation proposals, not allocated identities.

If actual allocation is later explicitly authorized, the allocator must be append-only:

```text
current max = KV001194
hypothetical first = KV001195
hypothetical last  = KV003015
count              = 1821
```

This range is **illustrative for the current frozen registry only**. It is not reserved. If the Stable Registry changes before mutation, the plan becomes stale and the range must be recomputed from the new committed maximum.

Allocation order is deterministic and carries no pedagogical meaning:

```text
sort by ProvisionalIdentityKey lexically
```

Each allocated row must derive only from the current Stage-B proposal:

```text
CanonicalWord <- ProposedCanonicalWord
MatchKey      <- ProposedMatchKey
SenseLabel    <- ProposedSense
```

The stable retry/idempotency origin key is planned as:

```text
third-party-vocabulary|<ProvisionalIdentityKey>
```

On retry, an existing origin key may be reused only when NoteID plus CanonicalWord / MatchKey / SenseLabel exactly agree with the current authorized allocation input. Any disagreement is a migration blocker, not an overwrite instruction.

### `held` — 96

Held is a terminal result for the current evidence boundary. It is **not** an allocation backlog.

```text
held -> no NoteID allocation
held -> no existing NoteID selection
held -> no master provenance promotion
```

This includes all 26 current learner-excluded identities plus semantic/mixed-POS ambiguity such as `paint`, `email`, `Spanish`, and `open`.

A held identity can leave this state only through a new reviewed decision whose evidence/fingerprint changes the Stage-B truth boundary.

---

## 3. Source provenance blocker

The current 20 third-party source adapters use the standardized occurrence schema:

```text
SourceOccurrenceKey
SourceID
SourceBook
Grade
Semester
SourceRow
Word
MatchKey
British
American
Definition
SourceFile
```

They currently do **not** carry `SourceEdition`.

The Klose master source mapping schema is:

```text
SourceID + SourceEdition + SourceItemKey + NoteID + Decision + Status
```

Therefore actual third-party provenance cannot be promoted into `master/source_identity_extensions.csv` by inventing a textbook edition. In particular, values such as `2024-revision`, `pre-2024-revision`, or `klose-current` must not be inferred from the third-party adapter filename or source grade.

Before master provenance mutation, one of the following must be explicitly designed and validated:

1. the adapters gain a real SourceEdition / Revision fact derived from verified source evidence; or
2. the source model gains an explicit auditable unknown/unverified-edition representation whose semantics do not pretend to identify a textbook revision.

Until then:

```text
MasterSourceMappingMutationAuthorized = false
```

This is a provenance gate, not a reason to discard Stage-A source occurrences or Stage-B identity decisions.

---

## 4. Future authorized mutation transaction

When the user explicitly authorizes actual allocation/merge, implementation must be split from release work.

Preflight must re-check:

```text
Stage-B closure = 2820 / 2820
review queue = 0
selected batch = 0
all decisions current-fingerprint bound
plan truth blobs == current blobs
registry active count / max == plan baseline
all 903 reuse NoteIDs still active
all 1821 new proposals still non-equivalent to current active identities
all 96 held still held
provenance contract resolved
```

Only after preflight may the identity transaction run:

```text
903 reuse-existing
  -> no Stable Registry row change

1821 new-stable-identity
  -> append-only NoteID allocation
  -> no deletion / renumber / reuse of an existing NoteID

96 held
  -> no mutation
```

The identity transaction must not simultaneously generate learner presentation, approve review, release Notes, rewrite publish outputs manually, or touch Anki.

---

## 5. Retry, rollback and concurrency

The allocator must be idempotent against committed state.

A rerun after a successful commit must detect the third-party origin key and perform zero new allocation. A partial or conflicting prior state must fail closed rather than allocate another NoteID.

Git commit is the transaction boundary. Before commit:

- build all proposed registry/source-binding changes in memory;
- run the persistent-state checker and a dedicated third-party allocation checker;
- prove old NoteIDs are byte-for-byte stable unless an explicit migration says otherwise;
- prove only authorized files changed.

If validation fails, no mutation commit is made. After a committed allocation, rollback is **not NoteID reuse**. A bad new identity must be corrected through explicit status/migration history while preserving the allocated NoteID audit trail.

Concurrent Stable Registry changes invalidate the plan. The mutation workflow must fetch/rebase current `main` immediately before commit and re-run preflight; it must never force-push a precomputed NoteID range.

---

## 6. Learner / release / Anki separation

Stable identity allocation does not mean Klose starts studying the identity.

After any future successful allocation, the next layers remain independent:

```text
Stable Identity
→ Learner Presentation at LearnerLevel=4
→ Learning Admission + LearningOrder
→ content review / fingerprint approval
→ Release Registry
→ generated study.csv / anki-import.csv
→ Release Gate
→ Anki Update Existing Notes / add new Notes
```

The current 972-note Vocabulary release remains unchanged during allocation. Existing Anki FSRS / Review History / Due / Interval / Card State must remain untouched.

Even though Stage A currently has 2794 learner candidates, that state does not auto-authorize release of 2794 identities into Anki.

---

## 7. Current gate

The planning layer itself is now VALIDATED / CHECKPOINTED, but it authorizes only read-only validation and plan/document changes.

```text
ActualMutationAuthorized               = false
StableNoteIDAllocationAuthorized       = false
MasterSourceMappingMutationAuthorized  = false
LearnerMutationAuthorized              = false
ReleaseMutationAuthorized              = false
PublishMutationAuthorized              = false
AnkiMutationAuthorized                 = false
```

The provenance blocker remains active. Before any mutation gate can become true, the provenance contract must be resolved, the actual allocator must itself be implemented/validated, and the user must explicitly authorize mutation.

---

## 8. Validation checkpoint

Allocation-plan validation:

```text
initial plan validation run = 34584336799 / PASS
post-fix final validation   = 34584612888 / PASS
```

Independent validation confirmed:

```text
registry persistent rows         = 1194
registry active NoteIDs          = 1189
registry max NoteID              = KV001194
Stage-B closure                  = 2820 / 2820
reuse-existing                   = 903
new-stable-identity proposals    = 1821
held                             = 96
learner-excluded held            = 26
hypothetical append range        = KV001195..KV003015 / NOT RESERVED
enabled third-party adapters     = 20
SourceEdition present            = no
master provenance promotion      = not authorized
allocation / learner / release / publish / Anki mutation = not authorized
validation workspace mutation    = no
```

Adversarial diff-scope review found that the pre-existing Stage-A workflow path filter `tools/check_third_party_*.py` also matched the new allocation-plan checker and caused a metadata-only Stage-A reseal. No Stage-A content fingerprint changed, but the trigger was unnecessarily broad. Commit `b8883e1b4d801567ae46decf503ea9a168cdd807` excludes `tools/check_third_party_allocation_plan.py` from the Stage-A trigger. Stage-A was then fully revalidated by run `34584514294`, which passed and persisted only refreshed seal metadata in commit `fd9ca00301b683e8741fbd20a39c91ea35dfbb8a`.
