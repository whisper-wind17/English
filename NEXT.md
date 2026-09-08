# NEXT — Klose Learning

Last updated: 2026-09-08

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary Stage A 继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
→ anki/klose/third_party_vocabulary/learner/learner_vocabulary_preview.csv
→ anki/klose/third_party_vocabulary/learner/grammar_form_quarantine_view.csv
```

动态进度只以 repo 当前文件为准。

---

## 1. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 identities
Expressions Stable = 66
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus / Stage A

```text
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary Identity View
→ current Learner Admission gate
→ Klose learner-stage vocabulary view
```

两份 durable truth 必须分层：

```text
review/identity_decisions.csv
= Identity content truth

learner/grammar_form_quarantine.csv
= current Klose Learner Admission gate
```

Reviewed identity decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

Enabled adapters：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
```

---

## 3. Current checkpoint — SIX-ADAPTER / GRAMMAR-STAGE GATE VALIDATED

Identity-level corpus 未被 learner gate 改写：

```text
Enabled adapters                   = 6
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2098
Identity-level Vocabulary Preview  = 985
Review/blocker surfaces            = 1010
Evidence-changed surfaces          = 911
Multipart resolved                 = 7
```

新增 current learner-stage projection：

```text
Grammar-form quarantine gates      = 56
Learner-stage Vocabulary Preview   = 979
Identity rows suppressed by gate   = 6
Preview occurrence contributions removed = 11
```

这里 `985 → 979` 不是删除 Identity：

```text
staging/unified_vocabulary_preview.csv
= Stage-A Identity-level reviewed candidates

learner/learner_vocabulary_preview.csv
= 当前 Klose 可继续进入 learner pipeline 的视图
```

---

## 4. Klose grammar-stage quarantine — FROZEN

用户确认：Klose 当前对过去式、过去分词/完成时相关语法仍处于较早阶段，因此 one-word past/past-participle forms 暂不进入当前 learner vocabulary。

核心规则：

```text
went → go
ate → eat
broke → break#damage
was → be

Identity relation
→ 保留 / 正常 resolved

Learner Admission
→ grammar-form quarantine
→ 当前不进入 learner_vocabulary_preview.csv
```

这不是 `held`，也不是 blocker。以后 grammar stage 提升时解除 learner gate 即可，不需要重做 Identity。

当前 gate 同时暂缓 `could / would` 这类明显超出当前阶段的 modal-past / hypothetical forms。

### Boundary guards

不得按 `-ed` / dictionary gloss 粗暴过滤：

```text
scared = 害怕的；受惊的
broken = 坏的；破损的
lost   = 迷路的 / 丢失的
```

若已 lexicalized 为独立 adjective/noun learning unit，正常保留。

普通复数、第三人称单数、`-ing` 不受本规则自动影响；`goes` 不 quarantine。

Homograph 必须 decision-scoped：

```text
left = 左边/左侧           → 保留
left = leave 的过去式      → quarantine

saw = 锯子                → 保留
saw = see 的过去式         → quarantine
```

Machine checker 不允许把 free-text dictionary `Definition` 当 grammar identity truth；否则 `go / hold / party / ground` 等会产生 false positive。

---

## 5. Validation checkpoint

Learner-gate architecture / policy / checker / workflow 已实现并通过完整 Stage-A 集成验证。

最终 successful workflow：

```text
run 34183172105 / #193 = SUCCESS
head = 2bbff1e9acc7ce25862c4e1651bc386a576aefd5
```

bot generated learner views：

```text
177d220e616522703839aa4412427d45ce8a204a
data: refresh simplified third-party Stage A workspace
```

核心验证：

```text
Third-party Simplified Completion Recheck     = PASS
Identity Preview TargetSense                  = 985 / 985
Third-party learner-stage grammar quarantine  = PASS
Learner-stage Vocabulary Preview              = 979
Grammar-form quarantine gates                 = 56
Past-form leak into learner preview           = NO
Lexicalized participle/adjective over-gating  = NO
Homograph decision-scope gate                 = ENFORCED
Source-definition heuristic as identity truth = NO
Identity truth mutated by learner gate        = NO
Klose Master/Learner/Publish/Anki             = UNTOUCHED
Stable ThirdPartyID minted                    = NO
Final Klose diff executed                     = NO
```

Spot-check：

```text
got / was / took
→ learner preview 中不存在

scared = 害怕的；受惊的
→ Identity + learner view 均保留

break#damage
Identity provenance = break|broke / 2
Learner provenance  = break       / 1
→ broke 被隔离，break 本体保留
```

Quarantine audit 明确记录 `left#leave-past`、`saw=see past` 为 `Scope=decision`，不会对整个 surface 一刀切。

独立 diff-scope：task-start `99e9de33...` → bot checkpoint `177d220...` 只涉及：

```text
third_party_vocabulary/learner/*
learner-view builder/checker
Stage-A workflow wiring
review policy
```

Klose Master/Learner/Publish/Anki 不在 diff 中。

架构文档已同步更新：

```text
75697daf15b522f6958b69e32128087f1e8e01bc
docs: separate third-party identity and learner views
```

---

## 6. Identity / Learner separation — HARD INVARIANT

```text
Source Fact
≠ Vocabulary Identity
≠ Learner Admission
≠ Anki learning state
```

因此：

```text
reuse-identity ≠ 当前必须学习
keep-identity  ≠ 当前必须学习
learner quarantine ≠ Identity unresolved
```

Future Stage B 不能直接消费 `unified_vocabulary_preview.csv` 作为当前学习清单；Identity reconciliation 后必须再经过 learner-stage gate。

---

## 7. V4 learner-first Identity policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频 pedagogical form
→ Identity 层可显式 keep，必须有 rationale
→ 是否当前学习仍由 Learner Admission 独立决定

显式 slot / reusable grammar pattern / communicative formula
→ route-expression

event / tense-specific source chunk
→ source-only

多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

所有 reviewed identity decision 仍以 exact current `OccurrenceKeys` 为 validity boundary。

---

## 8. High-throughput execution mechanism — FROZEN

```text
review_bundle.csv
→ normalize lanes
→ decision proposals
→ deterministic next_batch.json
→ batch_manifest.json + decision_updates.csv
→ manifest closure check
→ apply/build identity view
→ build/check learner-stage view
→ core Completion Recheck
→ batch Completion Recheck
→ Klose isolation
→ bot persist
```

硬规则：

```text
ExecutionReady must be true
manifest set == planner selected set
decision_updates MatchKey set == selected set
selected active batch closure = 100%
source mutation 与 decision mutation 不得混合
```

---

## 9. NEXT TASK — POLICY-REVIEW BATCH #2

当前 deterministic planner 仍是 Identity review；learner quarantine 不替代 Identity adjudication。

```text
ReviewLane         = policy-review
SelectedCount      = 10
EvidenceWeight     = 53 / 60
ExecutionReady     = true
SelectedMatchKeys  =
  swam
  taught
  told
  took
  went
  were
  won
  wore
  wrote
  goes
```

其中：

```text
swam / taught / told / took / went / were / won / wore / wrote
→ 继续完成 exact-evidence Identity re-review
→ 即使 resolved，current Learner Admission 仍 quarantine

goes
→ 正常 form-policy Identity review
→ 不属于 current past-form quarantine
```

执行要求：

```text
1. 读取 current review_bundle.csv / next_batch.json 与 exact source evidence。
2. 不修改 source/raw/parser/config。
3. 精确生成 planner 对应 batch_manifest.json + decision_updates.csv。
4. selected active batch closure = 100%。
5. apply 后 rebuild Identity + Learner views。
6. core Completion Recheck + learner gate checker + batch Completion Recheck 全部 PASS。
7. 核对 blocker / Identity Preview / Learner Preview delta。
8. Klose isolation 必须 PASS。
9. 更新 NEXT.md。
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
DO NOT admit grammar-quarantined forms into current learner view.
```

---

## 10. Long-term invariants

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 用于回溯，不等于学习优先级；
- MatchKey / morphology / alias 只做 candidate evidence；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- complete cover 前 partial split 不得 release；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
