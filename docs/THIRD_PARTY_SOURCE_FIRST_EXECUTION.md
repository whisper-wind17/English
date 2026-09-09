# Third-party Vocabulary Source-first Execution Strategy

Status: FROZEN for the current multi-adapter corpus build phase.

## 1. Goal

在与 Klose Stable Vocabulary 做 Stage-B reconciliation 之前，先完成**全部计划 Third-party Source Adapters**，形成完整、稳定、可审计的第三方 Source corpus；随后再基于最终 source evidence 一次性完成全局 Identity closure。

核心顺序：

```text
Phase A1 — Source Adapter Bulk Ingestion
→ SOURCE FREEZE
→ Phase A2 — Global Identity Closure
→ final Stage-A seal
→ Stage-B / Klose reconciliation
```

该顺序优先优化**总工作量、重复审阅次数与 CI 有效吞吐**，而不是追求单个 Adapter 接入后立即 `review_queue=0`。

---

## 2. Phase A1 — Source Adapter Bulk Ingestion

对每一个新 Adapter，执行：

```text
Raw XLSX
→ prepare_third_party_<SourceID>.py
→ source_reference/<SourceID>_staging/occurrences.csv
→ check_third_party_<SourceID>.py
→ source_adapters.csv enable
→ global source-adapter closure
→ generic corpus rebuild
→ Source truth regression check
→ Klose isolation
→ next Adapter
```

### Per-Adapter Definition of Done

一个 Adapter 在 Phase A1 中完成，要求：

1. parser 可确定性重建标准 occurrence；
2. edition-specific checker PASS；
3. 预期 books / occurrences / MatchKeys 基线已冻结；
4. `SourceOccurrenceKey` adapter 内唯一，且与其他 enabled adapters 无 collision；
5. SourceID / Grade / Semester / SourceBook / SourceFile / SourceRow 边界正确；
6. output 不包含 Klose NoteID matching、Identity decision、Learner Admission、Release 或 Anki state；
7. global `check_third_party_source_adapters.py` PASS；
8. corpus rebuild PASS；
9. 已有 Source Fact 无非预期 drift；
10. Klose Master / Learner / Release / Publish / Anki 无变化。

### Phase A1 不要求

接入一个 Adapter 后，**不要求**先完成：

```text
review_queue = 0
NextBatch = 0
all multipart resolved
all audited-defer eliminated
orthographic / morphology / semantic canonicalization closure
Vocabulary / Expression global closure
Stage-B premerge READY
```

这些属于 Phase A2 的全局 Identity 工作。

---

## 3. 什么会阻止继续下一个 Adapter

以下属于 **Source / Adapter blocker**，必须当场修复：

- XLSX/schema 解析异常；
- 计划教材缺册、错误包含非目标学段或 start point；
- occurrences / MatchKeys 计数异常且无法解释；
- `SourceOccurrenceKey` duplicate / cross-adapter collision；
- SourceID / Grade / Semester / SourceBook / SourceFile / SourceRow 错误；
- Edition/source reconciliation 冲突；
- parser 把 Identity/Klose/Learner/Release 字段泄漏进 Source Adapter；
- source rebuild 导致已有 Source Fact 非预期变化；
- Klose Master/Learner/Release/Publish/Anki 被修改。

发现上述问题时，停止接下一个 Adapter，先回到 Source 层修复并重新执行 Validation Gate。

---

## 4. 什么不阻止继续下一个 Adapter

以下属于 **Identity-layer work**，在 Phase A1 中允许保留，并由新 source evidence 继续累积：

- 新 surface 的 semantic review；
- morphology / spelling canonicalization；
- `program / programme` 一类 orthographic duplicate；
- multipart / homograph sense partition；
- Vocabulary / Expression boundary；
- current-context `audited-defer`；
- Klose candidate matching；
- Stage-B premerge `ReadyForPremergeReview=false`。

原因：后续 Adapter 可能增加新的 occurrence/context，使已做过的 Identity 判断重新 reopen。过早逐 Adapter 清空语义 blocker 会增加重复审阅和 fingerprint churn。

例外：如果一个“semantic blocker”实际暴露 parser/source mapping 错误，必须立即升级为 Source blocker，回到 Adapter 修复。

---

## 5. SOURCE FREEZE

只有**所有计划 Adapter**都达到 Phase-A1 Definition of Done，才能进入 Source Freeze。

Source Freeze 至少确认：

```text
all planned adapters = terminal
  terminal = integrated + validated
          OR explicitly excluded with reviewed reason

source-adapter union = deterministic
all enabled adapters = dedicated prepare/check contract
cross-adapter occurrence collision = 0
unexpected Source Fact drift = 0
Klose state mutation = 0
```

在 Source Freeze 前：

```text
DO NOT start final Identity closure.
DO NOT treat NextBatch=0 as final Stage-A completion.
DO NOT start Stage-B reconciliation.
DO NOT mint Stable ThirdPartyID / NoteID.
```

---

## 6. Phase A2 — Global Identity Closure

Source Freeze 后，对**最终 corpus**统一执行：

```text
morphology / form canonicalization
→ orthographic canonicalization
→ cross-source dedup
→ Vocabulary / Expression / source-only boundary
→ learner-relevant polysemy partition
→ evidence-changed re-review
→ audited-defer retirement / refresh
→ targeted duplicate audits
→ learner quarantine check
→ Completion Recheck
→ NextBatch = 0
→ final Stage-A seal
```

此时才要求 Stage-A Identity closure。

最终允许保留的 residual blockers 只能是：

```text
current-context audited-defer
```

不得为了 blocker=0 猜 occurrence partition 或扩大 dictionary sense inventory。

---

## 7. Stage B boundary

Stage B 只能消费 Source Freeze 后、Phase A2 完成后的最终 Stage-A seal。

必须满足：

```text
all planned source adapters closed
Source Freeze complete
EvidenceChangedSurfaces = 0
NextBatch SelectedCount = 0
ExecutionReady = false
final Stage-A seal verified
premerge snapshot bound to final Stage-A CheckpointFingerprint
ReadyForPremergeReview = true
```

之后才允许重新生成并审查 Third-party → Klose reconciliation candidates。

仍然禁止：

```text
exact MatchKey equality == same-sense merge
proposal == durable decision
reconciliation == merge authorization
reconciliation closure 前 mint Stable NoteID
```

---

## 8. Throughput principle

当前阶段的优化目标：

```text
最大安全 Source throughput
+ 最少重复 Identity review
+ 最少无效 Stage-A / Stage-B fingerprint churn
```

因此默认策略是：

```text
能在 Source 层确定的问题立即闭合；
需要最终跨来源 evidence 的 Identity 问题延后到 Source Freeze 后统一处理。
```
