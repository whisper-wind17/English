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

总目标不变：

```text
完成第三方 Vocabulary 的 Source / Identity / Learner / Review / Release 全部前置处理
→ 生成可正式合入 Klose 当前 Vocabulary Anki 的发布状态
→ 到“只剩最终 Anki 合入”时停止自动推进并给出设备侧合入动作
```

---

## 2. Standing execution directive — CURRENT USER RULE

在第三方 Vocabulary 尚未达到“只剩最终合入 Klose 当前 Anki”之前：

```text
用户说“继续” / “继续处理”
→ 授权执行当前流水线的下一步动作
→ 不再对内部 learner / review / release step 重复询问确认
```

每一步仍必须通过 truth-boundary / diff-scope / Completion Recheck / `IMPLEMENTED → VALIDATED → CHECKPOINTED`。

---

## 3. Startup order

继续本任务时固定读取：

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

`stable_learner_plan.json` 是 learner-preparation snapshot；当前 lifecycle 状态以本文件和 canonical learner/admission/review state 为准。

---

## 4. Current Stable / allocation truth

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

Stage-B historical closure remains：

```text
reuse-existing                    = 903
new-stable-identity               = 1821
held                              = 96
TOTAL                             = 2820
```

Allocation committed-state checker is now correctly bound to the Stage-B decision snapshot at the allocation commit; later Stage-A/Stage-B metadata reseals do not invalidate the historical allocation basis. Final allocation-plan validation after this fix：

```text
run = 34656494168 / PASS
```

---

## 5. LearnerLevel=4 content — CHECKPOINTED

Durable reviewed content：

```text
anki/klose/third_party_vocabulary/learner/content_reviewed/batch_01.csv ... batch_19.csv
anki/klose/third_party_vocabulary/learner/content_corrections.csv
```

Content truth：

```text
new Stable learner contents       = 1821 / 1821
review batches                    = 19
content provenance                = model-curated / third-party-learner-content-v1
correction overlay                = 14 duplicate-example corrections
unique English examples           = 1821
blank bilingual examples          = 0
content gate                      = PASS
```

`tools/check_third_party_learner_content.py` verifies exact coverage, non-empty bilingual examples, content provenance, short sentence length, lemma-aware target use, reflexive equivalence and duplicate-example closure.

Meaning remains bound to Stable `SenseLabel / MeaningPrimary`; third-party dictionary gloss is evidence, not learner truth.

---

## 6. Official Master / Learner materialization — CHECKPOINTED

Canonical upstream commit：

```text
commit = 5fd84a98cdf2c7c911f22986320b47bf12ba0b1b
```

The commit changed exactly these five canonical upstream files：

```text
anki/klose/master/build_stats.csv
anki/klose/master/vocabulary_master.csv
anki/klose/learner/current.csv
anki/klose/learner/learning_admission.csv
anki/klose/learner/presentation_review_registry.csv
```

Materialized third-party Master inventory：

```text
new derived Master rows            = 1821
FirstSource                        = third-party-vocabulary
FirstSourceBook                    = external-evidence-corpus
FirstGrade / FirstSemester         = blank
Released                           = no
provenance tag                     = external-unverified-edition
textbook source-map leakage        = 0
```

No unverified third-party occurrence was promoted into `master/source_identity_extensions.csv`.

Materialized learner presentation：

```text
new learner rows                   = 1821
LearnerProfile / LearnerLevel      = klose / 4
PresentationStatus                 = model-curated-pending-review
PresentationSource                 = third-party-learner-content-v1
```

903 `reuse-existing` identities keep their existing learner presentation; third-party gloss does not overwrite it.

---

## 7. Learning Admission / LearningOrder — CHECKPOINTED

Checkpointed Stable NoteID plan：

```text
third-party resolved learner scope = 2720 unique Stable NoteIDs
existing allowed preserved         = 453
new / held→allowed                 = 2267
  canonical admission new rows     = 1981
  existing held → allowed          = 286
```

Current full Klose learner admission：

```text
allowed total                      = 2894
review-scope union released∪allowed= 2953
LearningOrder                      = unique / continuous
```

Existing 453 allowed LearningOrder values were preserved exactly. New/promoted third-party curriculum rows use `stage::third-party-primary` and append deterministically after the existing curriculum order.

`tools/check_klose_learner.py` was corrected to honor the project invariant：

```text
explicit Learning Admission = learner-suitability truth
Source Grade                 = fallback difficulty signal only
Source Grade ≠ LearnerLevel
```

Final auxiliary-vocabulary gate：

```text
released                     = 972
allowed                      = 2894
union                        = 2953
admitted lemmas              = 2608
unadmitted later auxiliaries = 0
```

---

## 8. Review registry state

After canonical materialization and fingerprint sync：

```text
required review keys                = 2953
existing model-reviewed             = 972
human-reviewed                      = 0
pending                             = 1981
new review rows added initially     = 1981
```

The 1981 pending keys consist of：

```text
1821 new third-party Stable learner presentations
+ 160 reused existing Stable Notes newly entering allowed review scope
= 1981 pending
```

Do not equate `model-curated learner content` with fingerprint-bound review approval. Approval remains an explicit next lifecycle step.

---

## 9. Pronunciation boundary / debt

For the 1821 new Stable rows, IPA is promoted only when external evidence status is `consistent`.

```text
conflicting-evidence rows           = 36
rows missing one/both candidates    = 448
new Stable pronunciation debt rows  = 484
```

For conflict/missing evidence, Master British/American remains blank. Never invent IPA merely to satisfy release.

Current release-completeness diagnostic also identifies 72 newly-promoted existing allowed Notes lacking British/American IPA; these require resolution before those Notes can become release-visible under the expanded curriculum.

---

## 10. Validation evidence / idempotency

Important runs：

```text
first strict content gate           = 34655727376 / correctly failed closed
lemma-aware gate before corrections = 34655780334 / correctly failed closed on 14 duplicates + reflexive case
integrated materialization          = 34656169853 / PASS as Build Valid; Release blocked
final Stage-A isolation recheck     = 34656411036 / PASS
final Stage-B readiness             = 34656441086 / PASS
final Stage-B reconciliation        = 34656464762 / PASS
final allocation committed-state    = 34656494168 / PASS
committed-state idempotency rebuild = 34656582893 / PASS
```

Final idempotency rebuild `34656582893` confirmed：

```text
Persistent state                    = PASS / registry 3015 / released 972
Third-party content                 = PASS / 1821 / unique examples 1821
Third-party materialization         = PASS
  master_new                        = 1821
  learner_new                       = 1821
  plan                              = 2720
  preserve                          = 453
  new_or_promoted                   = 2267
  allowed_total                     = 2894
  pronunciation_debt_rows           = 484
  release                           = 972
  publish                           = 972
  textbook_source_leak              = 0
Review registry sync                = required 2953 / model 972 / pending 1981 / added 0 / invalidated 0
Auxiliary vocabulary gate           = items 0
Canonical upstream idempotency      = No upstream review-state changes
```

Release diagnostics intentionally remain blocked：

```text
allowed existing promoted rows with stale old publish LearningOrder = 286
of those with British/American IPA debt                            = 72
held released-library IPA debt                                      = 18
release checker third-party curriculum contract                     = not yet extended
```

Therefore the workflow correctly persisted no further upstream change and skipped the releasable generated-data commit.

---

## 11. Isolation fixes completed

Two lifecycle bugs found during this step were fixed：

1. learner content batch builder was renamed out of `prepare_third_party_*` source-adapter namespace;
2. Stage-A push paths no longer generically match every `tools/check_third_party_*.py`; downstream allocation/learner/release checkers no longer reseal Stage A.

The final deliberate Stage-A workflow change caused one last reseal (`34656411036`); after that, downstream learner/release checker changes are isolated from Stage A.

---

## 12. Immediate next pipeline step

下一步：

```text
THIRD-PARTY REVIEW APPROVAL
+ PRONUNCIATION DEBT RESOLUTION
→ RELEASE PREPARATION
```

下一次用户说 `继续` / `继续处理` 时，直接执行：

1. 对当前 1981 fingerprint-bound `pending` review keys 做独立 model review；
2. 1821 new presentations 检查 meaning / example / translation / target sense / age appropriateness；
3. 160 reused newly-admitted Notes 只做 guardrail review，不因第三方 evidence 覆盖已有 presentation；
4. 建立并处理 pronunciation debt queue：新 Stable 484 rows + newly promoted existing allowed IPA debt；
5. pronunciation 必须来自可审计 evidence；无法安全 resolve 的 Note 不能进入 release；
6. review approval 必须绑定当前 content fingerprint；
7. 扩展 release curriculum contract 以显式识别 `stage::third-party-primary`，不能伪造成 Grade4/5/6 textbook source；
8. 重新跑 release completeness / review / source / identity / publish-derivation gates；
9. 只有全部 releasable rows 满足 gate 后才写 Release registry / generated publish；
10. 本步骤仍不执行最终设备侧 Anki merge；到 publish + Release Gate 全部 ready 后停止并交给最终 Anki 合入步骤。

---

## 13. Permanent boundaries

始终禁止：

```text
promoting unverified third-party occurrence into Master textbook source map
inventing Source Grade / SourceEdition for external evidence
automatically allocating Stage-B held identities
overwriting reused learner presentation from third-party definitions
silently promoting conflicting/missing pronunciation evidence
approving learner content without current fingerprint binding
manual edit generated publish files
renumber/reuse Stable NoteID / ExpressionID
resetting or rebuilding Anki FSRS / Review History / Due / Interval
mixing Expression operations into Vocabulary update
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
