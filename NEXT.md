# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

```text
Grade 5–6 Vocabulary GitHub Release          = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated                      = true / DEVICE IMPORT + SYNC USER-CONFIRMED
Grade 5–6 Expressions GitHub Release         = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Anki Updated                     = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation           = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract              = IMPLEMENTED / VALIDATED / CHECKPOINTED
Actual third-party Stable allocation         = IMPLEMENTED / VALIDATED / CHECKPOINTED
Stable learner scope preparation             = IMPLEMENTED / VALIDATED / CHECKPOINTED
LearnerLevel=4 presentation candidate prep   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Learning Admission / LearningOrder plan      = IMPLEMENTED / VALIDATED / CHECKPOINTED

Official third-party learner materialization = NOT STARTED
Third-party content review / approval        = NOT STARTED
Third-party Release / Publish                = NOT STARTED
Third-party Anki merge                       = NOT READY / NOT STARTED
```

总目标：

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
→ 不再对内部 allocation / learner / review / release step 重复询问确认
```

仍必须逐步经过：truth-boundary / diff-scope / Completion Recheck / `IMPLEMENTED → VALIDATED → CHECKPOINTED`。

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
→ docs/LEARNER_REVIEW_REGISTRY.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ relevant learner/review/release tools and files
```

Pre-allocation `KV001194` 仅是 audit baseline，不再是 current Stable truth。

---

## 4. Current Stable Vocabulary truth

Actual allocation：

```text
allocation commit                 = fe0d1f04c2eae1cf5d492673dd79aef302691d39
execution run                     = 34608158097 / PASS
committed-state validation        = 34608453454 / PASS
persistent Stable rows            = 3015
active Stable NoteIDs             = 3010
current max NoteID                = KV003015
new third-party Stable rows       = 1821
new range                         = KV001195..KV003015
external evidence bindings        = 15791
held identities allocated/bound   = 0
```

Stage-B remains：

```text
reuse-existing                    = 903
new-stable-identity               = 1821
held                              = 96
TOTAL                             = 2820
```

Current release remains unchanged：

```text
released Vocabulary Notes         = 972
publish/study.csv                  = 972
publish/anki-import.csv            = 972
```

FSRS / Review History / Due / Interval / Card State 未被第三方工作修改。

---

## 5. Stable learner preparation — CHECKPOINTED

Preparation artifacts：

```text
anki/klose/third_party_vocabulary/learner/stable_learner_plan.json
anki/klose/third_party_vocabulary/learner/stable_learner_scope.csv
anki/klose/third_party_vocabulary/learner/stable_presentation_candidates.csv
anki/klose/third_party_vocabulary/learner/stable_learning_admission_plan.csv
```

Build / validation：

```text
persist run                       = 34610843938 / PASS
persist commit                    = fa6aa2b
independent Completion Recheck    = 34610954466 / PASS
```

Current scope：

```text
Stage-A identity candidates                     = 2820
Stage-A learner candidates                      = 2794
resolved learner provisional identities         = 2724
learner-admitted but Stage-B held               = 70
learner-excluded identities                     = 26
unique resolved Stable learner NoteIDs          = 2720
new Stable presentation candidates              = 1821
reuse actions                                    = 903
duplicate reuse contributions collapsed by ID   = 4
```

关键含义：

- 2724 个 resolved learner provisional identities 只对应 2720 个 Stable NoteIDs；4 个 reuse contribution 收敛到既有同一 NoteID，必须按 Stable identity 去重，不能重复造卡。
- 96 held 中有 70 个仍符合 learner policy，但因为 Identity 尚未安全 resolve，所以本轮不进入 Stable learner scope；其余 26 是 learner-excluded。
- 1821 个新 Stable Note 已建立 presentation candidate，但 `ExampleSentence / ExampleTranslation` 仍为空，状态为 `third-party-content-pending`；不能提前 materialize 为正式 learner content。
- 903 reuse-existing 对应既有 learner presentation 只允许 preserve，不使用第三方 Definition 覆盖现有 Klose 内容。

---

## 6. Admission / LearningOrder preparation — CHECKPOINTED

Stable NoteID 级 admission plan：

```text
planned admission rows             = 2720
existing allowed preserved         = 453
new / held→allowed planned         = 2267
ProposedStatus                     = allowed
LearnerProfile / LearnerLevel      = klose / 4
```

Ordering policy：

```text
1. 已有 allowed LearningOrder 原值完全保留；
2. 新进入 third-party curriculum 的 NoteID 追加在现有 allowed 序列之后；
3. 新增部分按：
   distinct source count DESC
   → occurrence count DESC
   → token count ASC
   → MatchKey lexical
   → NoteID
4. Source Grade 不参与 admission 或 ordering。
```

该 order 是 GitHub curriculum order，不是 Anki Due / FSRS scheduling。

当前这只是 **materialization plan**，尚未修改 canonical：

```text
anki/klose/learner/learning_admission.csv
```

---

## 7. Preparation isolation / Completion Recheck

Final recheck `34610954466 / PASS` confirmed deterministic regeneration and exact protection of：

```text
anki/klose/learner/current.csv
anki/klose/learner/learning_admission.csv
anki/klose/learner/presentation_review_registry.csv
anki/klose/master/release_registry.csv
anki/klose/master/release_registry_extensions.csv
anki/klose/publish/study.csv
anki/klose/publish/anki-import.csv
```

因此本阶段没有偷偷进入 Release / Publish / Anki 生命周期。

---

## 8. Provenance boundary

Third-party evidence remains：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

`stable_evidence_bindings.csv` 只解释 external evidence → Stable NoteID；仍禁止把未验证 occurrence 写入 `master/source_identity_extensions.csv`。

Presentation candidate 中的 pronunciation 仅是 external-evidence candidate；多值冲突会显式标成 `conflicting-evidence`，不能静默当作 verified textbook fact。

---

## 9. Immediate next pipeline step

下一步：

```text
THIRD-PARTY LEARNERLEVEL=4 CONTENT GENERATION + REVIEW
→ OFFICIAL LEARNER / ADMISSION MATERIALIZATION
```

下一次用户说 `继续` / `继续处理` 时，直接执行：

1. 对 1821 个 `third-party-content-pending` 新 Stable Note 生成适合 Klose LearnerLevel=4 的双语 learner content；
2. Meaning 必须与 Stable SenseLabel 对齐，不能被原始第三方 gloss 反向改义；
3. 例句自然、短、目标义项清楚，辅助词汇难度受 learner gate 约束；
4. pronunciation evidence 冲突不得无审校静默写入正式 Master/Learner；
5. 903 reuse-existing 默认保持既有 presentation，仅在独立 guardrail review 证明需要时才允许窄范围 override；
6. 完成 content review / adversarial checks 后，把 1821 新 presentation materialize 到正式 learner state；
7. 按已 checkpoint 的 admission plan materialize 2720 NoteID 的 Learning Admission / LearningOrder；
8. 同步 learner review registry，使新增/变化内容进入 fingerprint-bound `pending`；
9. Completion Recheck + CHECKPOINT；
10. 本步仍不自动 Release / Publish / Anki，下一 lifecycle 再处理 review approval / release。

---

## 10. Permanent boundaries

始终禁止：

```text
promoting unverified third-party occurrence into Master textbook source map
turning Stage-B held into automatic merge/allocation
surface-word-only dedup when senses differ
overwriting reuse-existing learner presentation from third-party definitions
approving learner content without fingerprint-bound review
manual edit generated publish files
renumber/reuse Stable NoteID / ExpressionID
rebuilding or resetting Anki FSRS / Review History / Due
mixing Expression operations into Vocabulary update
```

Current authoritative state：

```text
Stable max NoteID                    = KV003015
persistent / active Stable Notes     = 3015 / 3010
third-party Stable rows              = 1821
resolved learner Stable NoteIDs      = 2720
new presentation candidates          = 1821
planned new/promoted admissions      = 2267
current release                      = 972
learner prep                         = CHECKPOINTED
next step                            = content generation/review + learner/admission materialization
execution trigger                    = next user “继续” / “继续处理”
```
