# NEXT — Klose Learning

Last updated: 2026-09-12

## 1. Current checkpoint

```text
Grade 5–6 Vocabulary GitHub Release              = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated (previous 972 release)    = true / DEVICE IMPORT + SYNC USER-CONFIRMED
Grade 5–6 Expressions GitHub Release             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Anki Updated                         = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation               = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract                  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Actual third-party Stable allocation             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Stable learner scope / admission preparation     = IMPLEMENTED / VALIDATED / CHECKPOINTED
LearnerLevel=4 content generation + content gate = IMPLEMENTED / VALIDATED / CHECKPOINTED
Official third-party learner materialization     = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party Learning Admission materialization   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Fingerprint-bound review approval                = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party pronunciation resolution             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party Release / Publish                    = IMPLEMENTED / VALIDATED / CHECKPOINTED

Current 2953-note Vocabulary Anki merge           = NOT STARTED
```

总目标已经达到自动流水线停止点：

```text
第三方 Vocabulary Source / Identity / Learner / Review / Release 前置处理完成
→ 当前正式 publish 已生成并通过 Release Gate
→ 现在只剩最终设备侧 Anki 合入
```

按 standing directive，**到此停止自动推进**。不得从 GitHub 自动修改 Anki Collection；下一步必须由用户在 Anki Desktop 上按正式 SOP 导入并同步。

---

## 2. Startup order for next conversation

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_CURRENT_RELEASE_IMPORT.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ anki/klose/publish/anki-import.csv
→ anki/klose/learner/learning_admission.csv
```

GitHub 管当前发布内容；Anki 继续作为 FSRS / Review History / Due / Interval / Card State 真源。

---

## 3. Stable / learner truth

```text
persistent Stable rows            = 3015
active Stable NoteIDs             = 3010
current max NoteID                = KV003015
third-party Stable rows           = 1821 / KV001195..KV003015
resolved third-party learner scope= 2720
current allowed                   = 2894
current held                      = 59
LearningOrder                     = 000001..002894 / unique / continuous
```

Source Grade 与 LearnerLevel 仍独立；第三方 learner admission 不制造 Source Grade / SourceEdition。

---

## 4. Review / pronunciation — CHECKPOINTED

```text
review required                   = 2953
model-reviewed                    = 2953
human-reviewed                    = 0
pending                           = 0
```

Pronunciation：

```text
reviewed pronunciation rows       = 616
allowed pronunciation debt        = 0
released-library held IPA debt    = 18
```

18 条 held-library IPA 缺口不属于当前 allowed learning blocker；未通过审计的冲突/缺失 IPA 没有被凭空发明。

---

## 5. Release / Publish — CHECKPOINTED

Release transaction：

```text
release commit                    = 9c7beb510122202a523725c03b6a873291321025
ReleasedAt                        = 2026-09-12
ReleaseReason                     = third-party-primary-reviewed-v1
append-only rows                  = 1981
historical byte prefix            = exact
```

Current release：

```text
legacy release                    = 518
release extensions                = 2435
TOTAL released                    = 2953
allowed ∩ unreleased              = 0
```

Generated publish：

```text
anki/klose/publish/study.csv       = 2953 rows
anki/klose/publish/anki-import.csv = 2953 rows
Note Type                          = Klose Vocabulary
Deck                               = Klose-English::Vocabulary
Identity                           = NoteID
PromptHint nonempty                = 4
```

Generated data commit：

```text
b434bf9c3588fddd170ce690b56f5a3c137a2d92
```

---

## 6. Blocking incident and permanent fix

Post-release rebuild initially failed at：

```text
Learning admission references unknown NoteID: KV001195
```

Root cause was lifecycle ordering, not bad identity/release data：

```text
build_klose_learning_admission.py
→ sees committed 2953 release IDs
→ baseline derived Master still lacks 1821 third-party rows
→ old workflow ran apply_klose_learner_overrides.py too early
→ unknown NoteID fail-closed
```

Permanent fix：

```text
Build admission
→ Grade 5–6 learner presentation
→ materialize third-party Stable Master/Learner + admission overlay
→ only then run first learner/admission consumer
```

The unknown-NoteID validation was preserved; no gate was weakened.

Workflow fix commit：

```text
a1c24281a54e12aee152bc8fbef23ce3e85c9478
```

One-shot release/rebuild workflows were removed after use.

---

## 7. Validation / Completion Recheck

Release transaction：

```text
34668245756 / PASS
```

The first post-release canonical rebuild exposed the ordering bug and correctly failed closed：

```text
34668334029 / FAIL / expected during bug discovery
```

Integrated fix + full rebuild：

```text
34669232739 / PASS
release ready                      = PASS
released                           = 2953
allowed / held                     = 2894 / 59
pending reviews                    = 0
allowed IPA debt                   = 0
study / anki-import                = 2953 / 2953
textbook source leakage            = 0
```

Independent Completion Recheck：

```text
34669381139 / PASS
```

It additionally proved：

```text
third-party committed release checker = PASS
2720 learner-plan IDs all released
1821 new Stable IDs all released
1981 transaction rows exactly equal plan IDs not previously released
admission/order checkpoint preserved
review approval checkpoint preserved
release_ready PASS
idempotent rebuild produced no generated commit / no drift
```

Durable checker：

```text
tools/check_third_party_release_committed_state.py
```

Final validation/checkpoint code state before this NEXT update：

```text
0af78797c04f46699497badb623f59c88f670892
```

---

## 8. Immediate next step — FINAL ANKI MERGE

**Do not auto-execute.** Follow：

```text
docs/ANKI_CURRENT_RELEASE_IMPORT.md
```

Current device transition, assuming the previously confirmed 972-note release is already on Anki：

```text
Existing Notes updated in place    = 972
New Notes created                  = 1981
Final Vocabulary Notes / Cards     = 2953 / 2953
```

Critical device-side rules：

```text
use the existing Note Type: Klose Vocabulary
import only anki/klose/publish/anki-import.csv
Existing Notes = Update
identity = NoteID
never create a second Note Type
never delete/recreate existing Cards
preserve Review History / FSRS / Due / Interval / UserMemo
only materialize suspension/admission for Cards that are still is:new
allowed / held target = 2894 / 59
only reposition still-New allowed Cards by LearningOrder
Desktop -> AnkiWeb -> iPad sync after validation
```

Only after the user confirms successful Desktop import, old-card history preservation, suspension/order materialization and AnkiWeb/iPad sync may `Vocabulary Anki Updated (current 2953 release)` become true.

---

## 9. Permanent boundaries

```text
no unverified third-party occurrence → textbook source map
no invented Source Grade / SourceEdition
no automatic allocation of Stage-B held identities
no third-party overwrite of reused learner presentation
no silent promotion of conflicting/missing pronunciation evidence
no review approval without current fingerprint
no manual edit of generated publish files
no Stable NoteID / ExpressionID renumber/reuse
no GitHub reset/rebuild of Anki FSRS / Review History / Due / Interval
no Vocabulary/Expression lifecycle mixing
```

Current authoritative state：

```text
Stable max NoteID                    = KV003015
persistent / active Stable Notes     = 3015 / 3010
current Vocabulary release           = 2953
current allowed / held               = 2894 / 59
review pending                       = 0
allowed pronunciation debt           = 0
publish/study.csv                    = 2953
publish/anki-import.csv              = 2953
current 2953-note Anki merge         = NOT STARTED
Anki FSRS / review state changed     = no
next step                            = FINAL DEVICE-SIDE ANKI MERGE
execution trigger                    = explicit user device-side action / confirmation
```
