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

## 3. Current checkpoint — STAGE-A FIVE-ADAPTER QUALITY BOUNDARY

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1682
Review/blocker surfaces   = 156
Evidence-changed surfaces = 0
Multipart resolved        = 34
pending                   = 0
```

累计 blocker/Preview 演进：

```text
object-boundary pass      39 → 29 released/routed + 10 audited-defer
policy batch 1            256 → 226 / preview 1594 → 1600
policy batch 2            226 → 207 / preview 1600 → 1615
policy batch 3            207 → 200 / preview 1615 → 1615
split smoke               200 → 197 / preview 1615 → 1621
production split batch 1  197 → 176 / preview 1621 → 1661
production split batch 2  176 → 168 / preview 1661 → 1675
residual split batch 3    168 → 163 / preview 1675 → 1682
scoped reuse smoke        163 → 160 / preview 1682 → 1682
scoped reuse batch        160 → 156 / preview 1682 → 1682
```

当前 generated review bundle：

```text
deferred-high-ambiguity = 110
object-boundary         = 10
policy-executable       = 3
policy-review           = 23
split-resolution        = 10
actionable-semantic     = 0
semantic-review         = 0
```

这 156 个 blocker 当前视为 evidence/policy boundary，而不是“漏审 156 个”。Blocker=0 不是质量目标。

---

## 4. Occurrence-partitioned split mechanism — FROZEN

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint non-empty OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional Stage-A learning identities
```

硬门禁：

```text
union(partitions) = all current occurrences before release
any subgroup unresolved → whole MatchKey remains blocker
new evidence changes cover → requeue
multipart keep key = <MatchKey>#<variant>
TargetSense non-empty
route-expression/source-only subgroup allowed only in complete partition
Stage-A provisional key != Stable ThirdPartyID
```

Residual split 仍约 10 个：

```text
too / french / kind / little / live / look / mouse / plant / right / sound
```

至少一个 current occurrence 无法仅凭 standardized source row + ±8 neighborhood 安全归属；无新 evidence 不重复强拆。

---

## 5. Scoped multipart canonical reuse — FROZEN

当 base surface 已完成 multipart partition 后，form/alias 可以显式复用某一个 reviewed subgroup：

```text
form/alias
→ reviewed reuse-identity
→ explicit <base>#<variant>
```

硬约束：

```text
#variant 必须已存在于 complete reviewed multipart keep partition
alias 必须绑定全部 current OccurrenceKeys
alias 不得创建新 #variant
alias 不得覆盖 subgroup Display / TargetSense
Preview 合并 alias provenance + occurrence count
source evidence 变化仍 requeue
```

已验证：

```text
broke    → break#damage
drank    → drink#verb
flew     → fly#verb
fell     → fall#verb
cooking  → cook#verb
drinking → drink#verb
playing  → play#general
```

独立 Preview 抽查：

```text
fall#verb   SourceMatchKeys = fall|fell      / occurrences = 4
cook#verb   SourceMatchKeys = cook|cooking   / occurrences = 4
drink#verb  SourceMatchKeys = drink|drank|drinking / occurrences = 9
play#general SourceMatchKeys = play|playing  / occurrences = 7
```

这些 alias reuse 不增加 learning identity 数，因此 Preview 保持 1682，只减少 blocker。

---

## 6. Scheduler correction — CLOSED

旧 review-bundle scoring 会把已有 `audited-defer / canonical-blocked-defer / canonical-missing-defer` 的 semantic rows 再标成 `actionable-semantic`，导致重复审查。

已修复：semantic stable-defer 在 source/canonical evidence 未变化时直接进入 deferred lane，并增加 regression guard，禁止 stable defer 回流 active semantic lanes。

当前结果：

```text
actionable-semantic = 0
semantic-review     = 0
```

因此 five-adapter blocker audit 已达到 evidence-quality boundary。

---

## 7. Latest validation

```text
scheduler fix commit                 = 5ae44d54fb775b39706a9dbcb46d8f27f68cc4de
scoped reuse architecture commit     = 195adb3bcc6ee363cd930ab72b32440e1188727e
scoped reuse smoke decision commit   = 7e64a34343afafa85aed93036b01834746b2963e
scoped reuse smoke workflow          = 34168194013 SUCCESS
scoped reuse smoke bot commit        = b67e5fdd9957e92b14e4be823a8557d8d5ae0329
scoped reuse batch decision commit   = d852a45bc7244e79cde3b06bc65fee9d3b466180
scoped reuse batch workflow          = 34168312268 SUCCESS
scoped reuse batch bot commit        = 8f93eea74f419dd8187abb5f747672a57ad49709
```

Latest batch Completion Recheck：

```text
Decision-only fast path                    PASS
Source adapters reparsed                   NO
Core Completion Recheck                    PASS
Split-aware batch Completion Recheck       PASS
Scoped #variant canonical integrity        PASS
Preview TargetSense                        1682 / 1682
Explicit reviewed OccurrenceKeys           PASS
Changed evidence requeue                   PASS
Transient inbox removed                    PASS
Klose Master/Learner/Publish/Anki touched  NO
Stable ThirdPartyID minted                 NO
Final Klose diff executed                  NO
```

`policy-executable=3` 当前 proposal engine 仍输出 0：1 个 grammar-special + 2 个 multi-POS/lexicalization-risk，不机械 AutoApply。

---

## 8. NEXT TASK — USER GATE BEFORE NEXT SOURCE ADAPTER

Five-adapter Stage-A quality boundary 已形成。下一步不要继续为了减少 blocker 数重复扫描 156 个 evidence/policy-bound rows。

在继续扩大 source corpus 前，先向用户展示当前结构与质量边界，由用户确认是否启用下一 planned adapter：

```text
waiyan_start3
```

若用户确认启用：

```text
1. 启用 waiyan_start3 adapter。
2. 完整重跑 source parsing / validation，不走 decision-only fast path。
3. 新 source evidence 与现有 durable decisions 做 exact OccurrenceKeys revalidation。
4. evidence changed 的 MatchKey 必须自动 requeue，不静默沿用旧结论。
5. 重新生成 review_queue / review_bundle / Preview。
6. 独立核对 source occurrence closure、blocker delta、multipart partition 与代表性高风险 surface。
7. 更新 NEXT.md。
```

仍禁止：

```text
Stage-B Klose diff
Stable ThirdPartyID minting
修改 Klose Master/Learner/Publish/Anki
为了 blocker=0 强行解释 evidence-bound rows
```

---

## 9. Completion Recheck contract

每批必须验证：

```text
Source occurrence closure
Explicit reviewed OccurrenceKeys
Split subsets disjoint + complete
Partial split remains blocker
Completed split leaves review_queue
TargetSense non-empty
Canonical/scoped reuse ready
Changed source evidence requeues
Review Bundle closes over blockers
Stable defer 不回流 active semantic lanes
Policy proposals derived-only / AutoApply=no
Transient inbox removed
Diff scope only intended third-party/docs layers
Klose Master/Learner/Publish/Anki untouched
```

CI success 不能单独作为结果正确；必须 independent sample + high-risk boundary + diff recheck。

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
