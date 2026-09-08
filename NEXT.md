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
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
→ anki/klose/third_party_vocabulary/audit/review_bundle.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
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
→ Third-party Unified Vocabulary
```

内容决策真源：

```text
anki/klose/third_party_vocabulary/review/identity_decisions.csv
```

Reviewed decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

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

`waiyan_start3` 已于 2026-09-08 经用户显式确认后启用。其 Source Adapter 独立 parse + validation 后冻结真实基线：

```text
Source books       = 8
Source occurrences = 1157
Distinct MatchKeys = 1023
```

---

## 3. Current checkpoint — SIX-ADAPTER SOURCE EXPANSION VALIDATED

当前 corpus：

```text
Enabled adapters          = 6
Source occurrences        = 6005
Normalized surfaces       = 2161
Durable decisions         = 2097
Vocabulary preview        = 984
Review/blocker surfaces   = 1024
Evidence-changed surfaces = 924
Multipart resolved        = 7
```

从 five-adapter `1823 preview / 7 blockers` 变为 `984 preview / 1024 blockers` **不是内容丢失**。新增 `waiyan_start3` 后：

```text
924 个已有 surface 的 OccurrenceKeys 发生变化
→ 旧 reviewed decision 自动失效并 requeue

99 个新 surface
→ 首次进入 pending review

1 个 unchanged audited-defer
→ mouse 继续 zero-scan
```

因此当前闭合关系：

```text
1024 blockers
= 924 evidence-changed
+ 99 new pending surfaces
+ 1 unchanged audited-defer
```

旧 7 个 audited-defer 中，只有 `mouse` 当前 evidence/context 未变化并继续 zero-scan；`too / french / kind / plant / right / sound` 已因 source evidence 变化重新进入 active review。旧 accepted defer fingerprint 仍保留，直到 explicit re-review 真正更新 durable decision。

---

## 4. Source-expansion hardening — VALIDATED

本次 sixth-source expansion 暴露并修复了两个状态机边界问题。

### Scoped reuse dependency invalidation

新增 evidence 使 multipart canonical（例如 `cook`）暂时 stale/requeue 时，依赖 alias（例如 `cooking → cook#verb`）不能：

```text
- 绕过 unresolved canonical 继续进入 Preview；
- 因 canonical 暂时 unresolved 就被误判成永久非法；
- 被静默重写 durable decision。
```

当前行为：

```text
canonical split unresolved
→ dependent scoped reuse 暂时退出 Preview
→ durable alias decision 保留
→ canonical 复审后再恢复/验证
```

若 base 已 resolved 但请求的 `#variant` 不存在，仍 hard FAIL。

相关修复：

```text
c3ad9409024899382568eee55db1ca3a5a8ca902
fix: defer scoped reuse behind stale multipart canonical
```

### New pending blocker scheduling

曾发现 source expansion 产生的全新 pending surface 可能继承 low-actionability `deferred-high-ambiguity` lane。该状态不合法：未审 pending 不能伪装成 accepted audited-defer。

当前 normalizer 强制：

```text
decision-evidence-changed → always active
new pending               → always schedulable
accepted audited-defer + same context → zero-scan
accepted audited-defer + changed context → active re-review
```

相关修复：

```text
5a32e1d18b2e7b54fe2b30e3c7653a1ac8f40e73
fix: activate new pending blockers after source expansion
```

Core checker 同时扩展为 source-expansion aware，并冻结 `waiyan_start3=1157`：

```text
6dadcb1d16ce15cffb18299210d23aa27fad8536
test: validate source-expansion dependency invalidation
```

---

## 5. Validation checkpoint

最终 workflow：

```text
run 34179654152 / #189 = SUCCESS
job 101915966237          = SUCCESS
```

核心验证：

```text
Third-party Simplified Completion Recheck = PASS
Vocabulary Preview TargetSense             = 984 / 984
Source occurrence closure                  = PASS
Explicit reviewed OccurrenceKeys           = PASS
Changed source evidence requeue             = PASS
Split subsets disjoint                      = PASS
Split complete before release               = PASS
Partial split remains blocker               = PASS
Stale source excluded from Preview          = PASS
Scoped reuse waits for unresolved canonical = PASS
Canonical blocker bypass                    = NO
Unreviewed pending hidden as defer           = NO
Stable ThirdPartyID minted                  = NO
Final Klose diff executed                   = NO
Klose Master/Learner/Publish/Anki touched   = NO
```

Normalizer validation：

```text
source-evidence-changed reactivated = 924
new/non-defer blockers reactivated  = 99
unchanged audited-defer retired     = 1 (mouse)
active rows                         = 1023
deferred zero-scan                  = 1
```

最终 generated Stage-A workspace 已由 bot persist：

```text
7099f7d0765408059cbca281d747d56f39d4c7ce
data: refresh simplified third-party Stage A workspace
```

独立 diff-scope recheck：task-start `aefbf4e43c6b4763ec8a1966e0ea44a14255b340` → `7099f7d...` 只涉及 third-party Source/Stage-A workflow/generated workspace 及对应 checker/state-machine hardening；Klose Master/Learner/Publish/Anki 不在 diff 中。

---

## 6. V4 learner-first policy — FROZEN

```text
明显小学核心义 / 稳定 fixed lexical unit
→ learner-first narrow TargetSense
→ keep-identity

高频、直接有 recall value 的 pedagogical form
→ 可显式 keep，必须有 rationale

显式 slot / reusable grammar pattern / communicative formula
→ route-expression

event / tense-specific source chunk
→ source-only

已证明存在多个真实 target senses
→ occurrence split
→ complete cover 前不能 release
```

Source evidence 变化不能由旧 decision 静默继承；所有 decision 仍以 exact current `OccurrenceKeys` 为 validity boundary。

---

## 7. Audited-defer state machine — FROZEN

```text
decision-evidence-changed
→ always active
→ 不提前接受新 context

new audited-defer
→ stamp current context
→ zero-scan

same decision + same context
→ zero-scan

same decision + context changed
→ active re-review
→ 保留 old accepted fingerprint

decision changed after re-review
→ accept current context
→ 若仍 defer，可再次 zero-scan
```

Machine-enforced：

```text
changed evidence cannot be hidden
new pending cannot be hidden as deferred
unchanged accepted defer cannot reactivate
stale-context defer cannot be hidden
deferred row must match accepted decision/context fingerprint
```

---

## 8. High-throughput execution mechanism — FROZEN

执行链：

```text
review_bundle.csv
→ normalize lanes
→ decision proposals
→ deterministic next_batch.json
→ batch_manifest.json + decision_updates.csv
→ manifest closure check
→ apply/build
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

必须持续区分 `Review throughput` 与 `Net blocker release`。

---

## 9. NEXT TASK — SEPARATE DECISION-ONLY BATCH

Six-adapter source expansion 已完成并 checkpoint。**不要在 source-expansion commit 中继续做内容 decision。**

当前 deterministic planner：

```text
ReviewLane         = policy-review
SelectedCount      = 14
EvidenceWeight     = 60 / 60
ExecutionReady     = true
SelectedMatchKeys  =
  did
  ate
  became
  bought
  brought
  came
  drew
  gave
  got
  learnt
  met
  ran
  rode
  sent
```

下一任务按 decision-only fast path 完整处理这 14 个 surface：

```text
1. 读取 current review_bundle.csv / next_batch.json。
2. 不重新修改 source/raw/parser/config。
3. 为 planner 精确选中的 14 个 MatchKey 生成 batch_manifest.json + decision_updates.csv。
4. manifest set == planner set；decision_updates MatchKey set == planner set。
5. selected active batch closure = 100%，不得只处理容易项。
6. apply durable decisions 后 rebuild corpus。
7. 执行 core Completion Recheck + batch Completion Recheck + Klose isolation。
8. 重新 normalize/propose/plan，得到下一 deterministic batch。
9. 更新 NEXT.md。
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
DO NOT bypass evidence-changed re-review with old TargetSense.
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
