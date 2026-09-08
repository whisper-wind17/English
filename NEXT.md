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
Total            = 4848
```

`waiyan_start3` Source Inventory 已完成，但 **未启用**。

---

## 3. Current checkpoint — V4 LEARNER-FIRST / FIVE-ADAPTER ACTIVE REVIEW CLOSED

当前 corpus：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1823
Review/blocker surfaces   = 7
Evidence-changed surfaces = 0
Multipart resolved        = 35
Durable decisions         = 2097
```

当前 7 个 blocker：

```text
too
french
kind
mouse
plant
right
sound
```

它们全部是：

```text
Action      = split-required
Status      = held
Basis       = split-audited-defer
ReviewLane  = deferred-high-ambiguity
Batch size  = 0
```

含义不是“尚未处理”，而是：

```text
- current evidence 已证明存在多个真实小学 learning units；
- 至少一个 current occurrence 无法用 flat source evidence 安全归组；
- multipart release 要求 complete occurrence cover；
- 因此不能为了 blocker=0 猜 partition；
- evidence/canonical/policy context 未变化前禁止重复 review。
```

当前 deterministic planner：

```text
ReviewLane         = none
SelectedMatchKeys  = []
SelectedCount      = 0
ExecutionReady     = false
GateReason         = no active review batch
```

因此 **five-adapter Stage A 当前没有可执行 review batch**。

---

## 4. V4 learner-first finalization — FROZEN

V4 的核心变化不是降低 identity 门槛，而是结束“没有 sentence context 就永久 held”的旧模式。

现在：

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

Semantic-review lane 与 object-boundary lane 已完成。

最近 object-boundary 10/10 review：

```text
get through   → 通过；穿过
in one hour   → 一小时后
keep on       → 继续；坚持
out of        → 从……出来；离开
see the world → 看看世界；见世面
take away     → 拿走；带走
take down     → 取下；拿下
take off      → 脱下；摘下
all over      → 到处；遍及
a lot         → 很；非常
```

该批：

```text
Review throughput   = 10
Net blocker release = 10
Preview             = 1813 → 1823
Blockers            = 17 → 7
```

Workflow run `34177044466` / run #183 = SUCCESS。

---

## 5. Residual split adjudication

最后 residual split batch：

```text
mouse / plant / right / sound
```

4/4 已完整 adjudicate，但均因 complete partition 不可证明而进入 `split-audited-defer`。

```text
Review throughput   = 4
Net blocker release = 0
```

关键结论：

- `mouse`：3 个 occurrence 明确是动物；Waiyan g4 occurrence 无法安全区分动物 / computer mouse。
- `plant`：noun plant 与 verb plant 都有证据；多条 standalone occurrence 仍无法完整归组；已有 `plant trees` 不能替代 standalone provenance。
- `right`：多条方向义明确，但其余 date/health/description/invention neighborhood 无法可靠区分“正确”/“右侧”。
- `sound`：至少 noun `声音` 与 linking verb `听起来` 两个真实 target；两条 Renjiao occurrence 无法安全归组。

Workflow run `34176845351` / run #182 = SUCCESS。

---

## 6. P0 audited-defer scheduler fix — IMPLEMENTED / VALIDATED

曾发现 v4 normalizer 的严重回归：

```text
audited-defer 已完成
→ 下一 planner 又重新选中
```

根因：`tools/normalize_third_party_review_lanes.py` 虽读取 `defer_context.csv`，但旧 v4 实现没有使用 previous accepted context 抑制 unchanged defer，导致 held/split 被无限重新激活。

修复 commit：

```text
1332d47958488d7c327fd329529a24fca949df0f
fix: restore audited-defer zero-scan state
```

当前状态机：

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
→ 保留 old accepted fingerprint，直到 durable decision 真正变化

decision changed after re-review
→ accept current context
→ 可再次 zero-scan
```

修复同时纠正了 buggy v4 提前给旧 v3 defer 盖章的问题：旧 accepted context 恢复后，10 个 object-boundary row 正确重新 active；新 v4 defer `too / french / kind` 保持 zero-scan。

Validation workflow：

```text
run 34176626876 / #181 = SUCCESS
```

随后 split/object batches 继续验证该状态机：

```text
run #182 → new defer mouse/plant/right/sound 正确 stamp + retire
run #183 → unchanged 7 defer 正确 zero-scan
```

当前 machine-enforced：

```text
changed evidence cannot be hidden
unchanged accepted defer cannot reactivate
stale-context defer cannot be hidden
deferred row must match accepted decision/context fingerprint
```

---

## 7. High-throughput execution mechanism — FROZEN

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
```

Evidence workload 同时受 surface cap + weight budget 控制。

必须持续区分：

```text
Review throughput
Net blocker release
```

不得用低 release 率否定一个完整、安全的 review batch。

---

## 8. Five-adapter Stage-A validation baseline

最近最终 workflow #183 验证：

```text
Third-party Simplified Completion Recheck = PASS
TargetSense                               = 1823 / 1823
Source occurrence closure                 = PASS
Explicit reviewed OccurrenceKeys          = PASS
Changed source evidence requeue           = PASS
Split subsets disjoint                    = PASS
Split complete before release             = PASS
Partial split remains blocker             = PASS
Canonical blocker bypass                  = NO
Review blockers                           = 7
Active review batch                       = NONE
Deferred zero-scan                        = 7
Stable ThirdPartyID minted                = NO
Final Klose diff executed                 = NO
Klose Master/Learner/Publish/Anki touched = NO
```

当前 bot-persist checkpoint：

```text
0db5061e17ab1d4419a3928723da607501ad59ed
data: refresh simplified third-party Stage A workspace
```

---

## 9. NEXT TASK — EXPLICIT USER GATE BEFORE `waiyan_start3`

Five-adapter Stage A 当前 active review 已关闭。

下一 planned evidence expansion 是：

```text
waiyan_start3
```

但 **不得自动启用**。必须由用户明确确认。

用户明确确认后：

```text
1. source_adapters.csv 中启用 waiyan_start3。
2. 单独完成 source parse + validation；不得与 decision batch 混合。
3. rebuild corpus / review queue / review bundle。
4. source evidence 变化导致 OccurrenceKeys mismatch 时自动 requeue。
5. defer ContextFingerprint 变化时自动进入 active re-review。
6. 重新生成 proposals / next_batch。
7. 所有 active batch 继续使用 deterministic planner + manifest 100% closure。
8. 独立核对 blocker delta、multipart partitions、canonical/scoped reuse、高风险 surface。
9. 仍不做 Stage B。
10. 更新 NEXT.md。
```

在用户确认前：

```text
DO NOT re-review the 7 unchanged deferred split surfaces.
DO NOT enable waiyan_start3.
DO NOT mint Stable ThirdPartyID.
DO NOT run Stage-B Klose diff.
DO NOT modify Klose Master/Learner/Publish/Anki.
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
