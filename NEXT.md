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
→ anki/klose/third_party_vocabulary/audit/decision_proposals.csv
→ anki/klose/third_party_vocabulary/audit/defer_context.csv
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/staging/unified_vocabulary_preview.csv
```

动态进度只以 repo 当前文件为准；旧 checkpoint 仅作历史记录。

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

当前未进入 Stage B；不得因 Klose 已有某词而删除第三方 learning unit；不得 mint Stable ThirdPartyID。

`identity_decisions.csv` 是唯一内容决策真源。Reviewed decision 必须绑定 exact JSON `OccurrenceKeys`；source evidence 变化必须 requeue。

Enabled adapters：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
Total            = 4848
```

`waiyan_start3` Source Inventory 已完成，但尚未启用。

---

## 3. Current checkpoint — HIGH-THROUGHPUT V3 HARDENED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1685
Review/blocker surfaces   = 153
Evidence-changed surfaces = 0
Multipart resolved        = 34
pending                   = 0
```

累计演进：

```text
policy/object passes      blockers 256 → 200 / preview 1594 → 1615
split smoke               200 → 197 / preview 1615 → 1621
production split batch 1  197 → 176 / preview 1621 → 1661
production split batch 2  176 → 168 / preview 1661 → 1675
residual split batch 3    168 → 163 / preview 1675 → 1682
scoped reuse smoke        163 → 160 / preview 1682 → 1682
scoped reuse batch        160 → 156 / preview 1682 → 1682
full policy-review pass   156 → 153 / preview 1682 → 1685
v3 hardening              counts unchanged
```

高吞吐指标必须分开：

```text
Review throughput   = 本批实际完成 adjudication 的 surface 数
Net blocker release = 本批最终安全离开 blocker 的 surface 数
```

最近 full policy pass：

```text
Original policy-review lane = 23
Reviewed end-to-end         = 23 / 23
Released                    = 3
Audited-defer               = 20
policy-review after pass    = 0
```

本轮 release：

```text
a        → keep-identity / 一个；一（用于辅音音素前）
mice     → keep-identity / 老鼠（mouse 的复数）
sometime → keep-identity / 在某一时候；改天
```

`sweets` 曾被尝试 release，但 core checker 正确拦截 `Protected form-policy blocker lost: sweets`；未削弱 checker，最终保持 blocker。

---

## 4. High-throughput v3 execution mechanism — FROZEN

长期规则已写入 `docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md`。

### 4.1 Full-batch closure is executable

不再只靠 Prompt 要求“整批处理”。当前执行链：

```text
normalized review_bundle.csv
→ tools/propose_third_party_policy_decisions.py
→ tools/plan_third_party_review_batch.py
→ audit/next_batch.json
→ review/batch_manifest.json + review/decision_updates.csv
→ tools/check_third_party_batch_manifest.py
→ apply/build/recheck/persist
```

真正执行 decision batch 时：

```text
manifest SelectedMatchKeys == deterministic next_batch SelectedMatchKeys
set(decision_updates.MatchKey) == selected MatchKeys
ExecutionReady == true
→ selected active batch closure = 100%
```

少处理、额外处理、stale plan、lane/fingerprint 不一致或 `ExecutionReady=false` 均 FAIL。成功 apply 后 transient manifest/inbox 删除。

### 4.2 Evidence-weighted batch sizing

仍保留高 surface cap，但同时限制 evidence workload：

```text
SurfaceCount <= lane cap
AND
EvidenceWeight <= lane budget
```

简单 policy / semantic 不退回 2–3 item 微批次；复杂 split/cross-source batch 会按 occurrence/source/canonical/evidence payload 动态缩小。

`policy-executable` 只有 proposal engine 实际产生 confirm-or-reject proposal 时才进入计划；当前 `were / pleased / lost` proposal=0，因此不会阻塞后续 lane。

### 4.3 Audited-defer context invalidation

`tools/normalize_third_party_review_lanes.py` 维护 derived-only：

```text
anki/klose/third_party_vocabulary/audit/defer_context.csv
```

每个显式 audited defer 记录：

```text
DecisionSignature
ContextFingerprint
DeferReasonCode
DeferDependency
PolicyVersion=v3
```

ContextFingerprint 包含当前 source occurrence evidence + directional canonical state + policy version。

```text
same decision + same context
→ deferred / no rescan

same decision + changed context
→ active re-review

decision-evidence-changed
→ 始终 active re-review，不允许藏在 deferred
```

`defer_context.csv` 只是 derived scheduling/audit metadata；`identity_decisions.csv` 仍是唯一内容决策真源。

### 4.4 Source mutation and decision mutation cannot mix

Source/raw/parser/config 变化必须先完成 parse/rebuild/requeue/plan，再做新的 decision batch。Workflow 已禁止同一 source-changing commit 携带 `decision_updates.csv`，避免 stale plan 审核新 evidence。

### 4.5 Workflow serialization

Stage-A workflow 已加入：

```text
concurrency group = third-party-stage-a-${ref}
cancel-in-progress = false
```

同一 branch 的 mutation 串行执行；不再允许两个 bot persist 相互 push race，也不取消已启动 decision batch。

---

## 5. Current normalized review boundary

```text
deferred-high-ambiguity = 140
policy-executable       =   3
split-resolution        =  10
policy-review           =   0
object-boundary         =   0
actionable-semantic     =   0
semantic-review         =   0
Total blockers          = 153
```

140 个 deferred 不是“未审”；无 context/evidence 变化时禁止重复扫描。

`policy-executable=3`：

```text
were / pleased / lost
```

proposal engine 输出 0：1 个 grammar-special + 2 个 multi-POS/lexicalization-risk。v3 planner 会跳过这些 guarded rows，不允许 lane starvation。

Residual split：

```text
too / french / kind / little / live / look / mouse / plant / right / sound
```

这些至少有一个 current occurrence 无法用当前 flat source evidence 安全归属；无新 evidence 不重复强拆。

当前 deterministic next-batch candidate：

```text
ReviewLane         = split-resolution
SelectedMatchKeys  = too / french / kind / little / live / look
SelectedCount      = 6
EvidenceWeight     = 65 / 70
SurfaceCap         = 25
SkippedGuardedRows = 3
ExecutionReady     = false
```

GateReason：`unchanged residual split requires stronger source evidence or explicit user gate`。

因此这 6 个只是 planner 给出的下一候选，不允许直接生成 decision batch。

---

## 6. Raw source evidence ceiling — VERIFIED

2026-09-08 已对 5 个 enabled adapter 的 48 册原始 XLSX 做只读 workbook XML 审计：

```text
Sheets/book       = 1
Max non-empty col = 4
Columns           = A 单词 | B 英音 | C 美音 | D 释义
Rows with E+ data = 0
Unit/Module/Lesson structural metadata = 0
```

结论：raw source 本身就是 flat vocabulary list；当前歧义不是 adapter 丢失 Unit 字段。

因此：

```text
- 不虚构 Unit/Module；
- 不从固定 row window 推导伪 Unit；
- ±8 neighborhood 只能作弱 contextual evidence；
- evidence-bound blocker 保持 held/split-required；
- 要继续降低这部分 blocker，需要更强教材证据或新 adapter evidence。
```

---

## 7. Occurrence-partitioned split + scoped reuse — FROZEN

Occurrence split：

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint non-empty OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional Stage-A learning identities
```

Scoped multipart reuse 已验证：

```text
broke    → break#damage
drank    → drink#verb
flew     → fly#verb
fell     → fall#verb
cooking  → cook#verb
drinking → drink#verb
playing  → play#general
```

`broken / watches / felt` 仍有真实 lexical/form ambiguity，不做 scoped reuse。

---

## 8. V3 validation checkpoint

主要实现：

```text
full-batch policy freeze       = cdefc87546969ee6ac74244a1b9c21332b7b5f8e
batch planner                  = tools/plan_third_party_review_batch.py
batch manifest checker         = tools/check_third_party_batch_manifest.py
defer context normalizer       = tools/normalize_third_party_review_lanes.py
workflow serialization/mixing  = .github/workflows/prepare-third-party-renjiao-start1.yml
execution-ready gate commit    = 942fb5db59407a9fb370abe1ce5c15cfe85dbc36
policy v3 doc commit           = d3250a735267df8ead994eeaa3b0ebcd97cf5d98
```

Final regression workflow：

```text
run = 34170966959
status = SUCCESS
```

前一完整 v3 regression `34170814246` 也 SUCCESS，并验证：

```text
Decision-only fast path                  PASS
Source parser skip on decision/code-only PASS
Core Completion Recheck                  PASS
Audit-batch Completion Recheck           PASS
Preview TargetSense                      1685 / 1685
Source occurrence closure                PASS
Explicit reviewed OccurrenceKeys         PASS
Changed source evidence active requeue   PASS
Audited defer context tracking           PASS
Guarded policy rows skipped by planner   PASS
Evidence-weighted batch planning         PASS
Klose Master/Learner/Publish/Anki touched NO
Stable ThirdPartyID minted               NO
Final Klose diff executed                NO
```

V3 hardening 未改变 corpus content baseline：仍为 `1685 Preview / 153 blockers / 34 multipart resolved`。

---

## 9. NEXT TASK — USER GATE BEFORE `waiyan_start3`

Five-adapter Stage-A 当前没有可安全自动执行的 active review batch。剩余：

```text
140 = deferred evidence/policy rows
  3 = guarded policy rows, proposal=0
 10 = residual split requiring stronger occurrence evidence
```

下一 planned evidence expansion 是 `waiyan_start3`，但不得自动启用。用户确认后：

```text
1. Enabled=yes 接入 waiyan_start3。
2. 完整 source parse + validation；不能与 decision batch 混在同一次 mutation。
3. rebuild corpus / review bundle / defer context / proposals / next_batch。
4. 新增 occurrence evidence 导致 durable OccurrenceKeys 不匹配时自动 requeue。
5. canonical/context fingerprint 变化导致 audited-defer 自动 re-review。
6. 新 active batch 使用 v3 planner + manifest，100% closure；不退回逐项 review。
7. 独立核对 source closure、blocker delta、multipart partition、scoped reuse、高风险 surface。
8. 更新 NEXT.md。
```

仍禁止：Stage-B Klose diff、Stable ThirdPartyID minting、修改 Klose Master/Learner/Publish/Anki、为了 blocker=0 强行解释 evidence-bound rows。

---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
