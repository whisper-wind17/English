# NEXT — Klose Learning

Last updated: 2026-09-12

## 1. Current checkpoint

```text
Grade 5–6 Vocabulary GitHub Release              = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated                          = true / DEVICE IMPORT + SYNC USER-CONFIRMED
Grade 5–6 Expressions GitHub Release             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Anki Updated                         = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation               = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract                  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Actual third-party Stable allocation             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Stable learner scope / admission preparation     = IMPLEMENTED / VALIDATED / CHECKPOINTED
LearnerLevel=4 content generation + content gate = IMPLEMENTED / VALIDATED / CHECKPOINTED
Official third-party learner materialization     = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party Learning Admission materialization   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Fingerprint-bound review registry sync           = IMPLEMENTED / VALIDATED / CHECKPOINTED

Third-party review approval                      = NOT STARTED / pending=1981
Third-party pronunciation debt resolution        = NOT STARTED / debt=484 new Stable rows
Third-party Release / Publish                    = NOT READY / NOT STARTED
Third-party Anki merge                           = NOT READY / NOT STARTED
```

总目标：

```text
完成第三方 Vocabulary 的 Source / Identity / Learner / Review / Release 全部前置处理
→ 生成可正式合入 Klose 当前 Vocabulary Anki 的发布状态
→ 到“只剩最终 Anki 合入”时停止自动推进并给出设备侧合入动作
```

用户 standing directive：在达到最终 Anki 合入前，`继续` / `继续处理` = 授权执行当前流水线下一步；每一步仍必须经过 truth-boundary / diff-scope / Completion Recheck / `IMPLEMENTED → VALIDATED → CHECKPOINTED`。

---

## 2. Startup order

```text
AGENTS.md
→ NEXT.md
→ anki/klose/third_party_vocabulary/allocation/execution_receipt.json
→ anki/klose/third_party_vocabulary/learner/stable_learner_plan.json
→ anki/klose/third_party_vocabulary/learner/stable_learner_scope.csv
→ anki/klose/third_party_vocabulary/learner/stable_presentation_candidates.csv
→ anki/klose/third_party_vocabulary/learner/stable_learning_admission_plan.csv
→ anki/klose/third_party_vocabulary/learner/content_corrections.csv
→ anki/klose/learner/current.csv
→ anki/klose/learner/learning_admission.csv
→ anki/klose/learner/presentation_review_registry.csv
→ docs/LEARNER_REVIEW_REGISTRY.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ relevant review/release tools
```

`stable_learner_plan.json` 是 preparation snapshot；当前 lifecycle 状态以本文件和 canonical learner/admission/review state 为准。

---

## 3. Stable / allocation truth

```text
allocation commit                 = fe0d1f04c2eae1cf5d492673dd79aef302691d39
allocation execution run          = 34608158097 / PASS
persistent Stable rows            = 3015
active Stable NoteIDs             = 3010
current max NoteID                = KV003015
third-party Stable rows           = 1821 / KV001195..KV003015
external evidence bindings        = 15791
held identities allocated/bound   = 0
```

Historical Stage-B closure：

```text
reuse-existing                    = 903
new-stable-identity               = 1821
held                              = 96
TOTAL                             = 2820
```

Allocation committed-state checker is bound to the Stage-B decision snapshot at the allocation commit, not to mutable downstream reconciliation metadata. Final allocation-plan validation：`34656494168 / PASS`.

---

## 4. LearnerLevel=4 content — CHECKPOINTED

Durable content：

```text
anki/klose/third_party_vocabulary/learner/content_reviewed/batch_01.csv ... batch_19.csv
anki/klose/third_party_vocabulary/learner/content_corrections.csv
```

```text
new Stable learner contents       = 1821 / 1821
review batches                    = 19
content provenance                = model-curated / third-party-learner-content-v1
correction overlay                = 14 duplicate-example corrections
unique English examples           = 1821
blank bilingual examples          = 0
content gate                      = PASS
```

`tools/check_third_party_learner_content.py` checks exact coverage, bilingual completeness, provenance, sentence length, lemma-aware target use, reflexive equivalence and duplicate closure. Meaning remains bound to Stable `SenseLabel / MeaningPrimary`; third-party dictionary gloss is evidence, not learner truth.

---

## 5. Official Master / Learner materialization — CHECKPOINTED

Canonical upstream commit：

```text
5fd84a98cdf2c7c911f22986320b47bf12ba0b1b
```

It changed exactly：

```text
anki/klose/master/build_stats.csv
anki/klose/master/vocabulary_master.csv
anki/klose/learner/current.csv
anki/klose/learner/learning_admission.csv
anki/klose/learner/presentation_review_registry.csv
```

New third-party derived Master rows：

```text
rows                               = 1821
FirstSource                        = third-party-vocabulary
FirstSourceBook                    = external-evidence-corpus
FirstGrade / FirstSemester         = blank
Released                           = no
provenance tag                     = external-unverified-edition
textbook source-map leakage        = 0
```

New learner rows：

```text
rows                               = 1821
LearnerProfile / LearnerLevel      = klose / 4
PresentationStatus                 = model-curated-pending-review
PresentationSource                 = third-party-learner-content-v1
```

903 `reuse-existing` identities preserve existing learner presentation; third-party gloss never overwrites it.

---

## 6. Learning Admission / LearningOrder — CHECKPOINTED

```text
resolved third-party learner scope = 2720 unique Stable NoteIDs
existing allowed preserved         = 453
new / held→allowed                 = 2267
  admission new rows               = 1981
  held → allowed                   = 286
current allowed total              = 2894
review-scope released∪allowed      = 2953
LearningOrder                      = unique / continuous
```

Existing 453 LearningOrder values remain exact. New/promoted rows use `stage::third-party-primary` and append deterministically.

`tools/check_klose_learner.py` now enforces the correct invariant：

```text
explicit Learning Admission = learner-suitability truth
Source Grade                 = fallback difficulty signal only
Source Grade ≠ LearnerLevel
```

Final auxiliary gate：released=972 / allowed=2894 / union=2953 / admitted lemmas=2608 / unadmitted later auxiliaries=0.

---

## 7. Review / pronunciation state

Review registry：

```text
required keys                       = 2953
model-reviewed existing             = 972
human-reviewed                      = 0
pending                             = 1981
```

Pending = 1821 new third-party presentations + 160 reused Stable Notes newly entering allowed scope. `model-curated` is not approval; release approval must remain fingerprint-bound.

Pronunciation promotion policy：only external evidence status `consistent` may populate IPA. Conflict/missing remains blank.

```text
new Stable conflicting-evidence rows        = 36
new Stable missing one/both IPA candidates  = 448
new Stable pronunciation debt rows          = 484
newly-promoted existing allowed IPA debt    = 72
released-library held IPA debt              = 18
```

Never invent IPA merely to satisfy release.

---

## 8. Validation / idempotency evidence

```text
strict content gate first fail-closed        = 34655727376
lemma-aware pre-correction fail-closed       = 34655780334
integrated materialization                   = 34656169853 / PASS as Build Valid
final Stage-A isolation recheck              = 34656411036 / PASS
final Stage-B readiness                      = 34656441086 / PASS
final Stage-B reconciliation                 = 34656464762 / PASS
final allocation committed-state             = 34656494168 / PASS
committed-state idempotency rebuild          = 34656582893 / PASS
```

Idempotency rebuild `34656582893` confirmed：

```text
Persistent registry / release       = 3015 / 972
Third-party content                 = 1821 / unique examples 1821
Master/Learner new rows             = 1821 / 1821
Admission plan preserve/new         = 453 / 2267
Allowed total                       = 2894
Review required/model/pending       = 2953 / 972 / 1981
Auxiliary vocabulary blockers       = 0
Pronunciation debt new Stable       = 484
Textbook source leakage             = 0
Publish study / anki-import         = 972 / 972
Canonical upstream rebuild          = No upstream review-state changes
```

Release diagnostics intentionally remain blocked because expanded third-party curriculum is not yet release-ready; generated publish and Anki were not changed.

---

## 9. Lifecycle isolation + diff-scope cleanup

During implementation, broad Stage-A triggers initially caused downstream learner checker changes to reseal Stage A and cascade Stage-B/premerge regeneration. This was treated as an out-of-scope side effect, not accepted as learner-stage truth.

Fixes：

1. learner content builder renamed out of `prepare_third_party_*` source-adapter namespace;
2. Stage-A push paths no longer generically match every `tools/check_third_party_*.py`;
3. allocation committed-state checker now validates the historical Stage-B snapshot at the allocation commit;
4. after validation, all accidental Stage-A status / premerge / reconciliation mutations were restored byte-exact to the step-start checkpoint `bac19a8d3279d16e976c01dcae9a04fa6be564b0` by one atomic self-deleting transaction.

Restore evidence：

```text
restore run                         = 34656726278 / PASS
restore commit                      = 661e7ac4398e6322be7e3b1b4917a12565e57114
temporary restore workflow          = self-deleted
```

Final diff from `bac19a8d...` confirms **no net mutation** to：

```text
Stage-A status
premerge / reconciliation decision artifacts
note_registry / note_registry_extensions
source_identity_extensions.csv
release_registry / release_registry_extensions
publish/study.csv
publish/anki-import.csv
anki/ learning-state files
Expressions
```

The learner step therefore changed only learner content/tooling, canonical derived Master/Learner/Admission/Review state, workflow isolation logic and checkpoint documentation.

---

## 10. Immediate next pipeline step

```text
THIRD-PARTY REVIEW APPROVAL
+ PRONUNCIATION DEBT RESOLUTION
→ RELEASE PREPARATION
```

Next `继续` / `继续处理` directly executes：

1. independently model-review current 1981 fingerprint-bound pending keys;
2. review 1821 new presentations for meaning/example/translation/target-sense/age appropriateness;
3. review 160 reused newly-admitted Notes as guardrails only; do not overwrite existing presentation from third-party evidence;
4. build and resolve pronunciation debt queue: 484 new Stable rows + promoted existing allowed IPA debt;
5. pronunciation must come from auditable evidence; unresolved Notes cannot release;
6. bind approval to current content fingerprint;
7. extend release curriculum contract to explicitly understand `stage::third-party-primary` without inventing Source Grade/Edition;
8. rerun completeness / review / source / identity / publish-derivation gates;
9. write Release registry / generated publish only for rows that pass all gates;
10. do not execute final device-side Anki merge yet; stop when Publish + Release Gate are ready.

---

## 11. Permanent boundaries

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
third-party Stable rows              = 1821
third-party learner content          = 1821 / CHECKPOINTED
resolved third-party learner scope   = 2720
current allowed                      = 2894
current review scope                 = 2953
review pending                       = 1981
new Stable pronunciation debt        = 484
current Vocabulary release           = 972
publish/study.csv                    = 972
publish/anki-import.csv              = 972
Anki FSRS / review state changed     = no
next step                            = review approval + pronunciation debt resolution + release preparation
execution trigger                    = next user “继续” / “继续处理”
```
