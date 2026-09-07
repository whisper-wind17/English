# NEXT — Klose Learning

Last updated: 2026-09-08

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary blocker audit 继续读取：

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

动态进度/当前计数只以本 `NEXT.md` 为准；旧 checkpoint 只作历史记录。

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

`identity_decisions.csv` 是唯一内容决策真源。Reviewed decision 必须绑定 exact JSON `OccurrenceKeys`；evidence 变化必须 requeue。

Enabled adapters：

```text
beijing_start1   808
renjiao_start1   908
renjiao_start3   851
hujiao_start3   1111
waiyan_start1   1170
Total           4848
```

`waiyan_start3` 尚未启用。

---

## 3. Current checkpoint — RESIDUAL SPLIT BATCH 3 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1682
Review/blocker surfaces   = 163
Evidence-changed surfaces = 0
Multipart resolved        = 34
pending                   = 0
```

累计进展：

```text
object-boundary pass      39 → 29 released/routed + 10 audited-defer
policy batch 1            blockers 256 → 226 / preview 1594 → 1600
policy batch 2            blockers 226 → 207 / preview 1600 → 1615
policy batch 3            blockers 207 → 200 / preview 1615 → 1615
split smoke (3 surfaces)  blockers 200 → 197 / preview 1615 → 1621
production split batch 1  blockers 197 → 176 / preview 1621 → 1661
production split batch 2  blockers 176 → 168 / preview 1661 → 1675
residual split batch 3    blockers 168 → 163 / preview 1675 → 1682
```

Residual split batch 3：5 Source MatchKeys / 7 durable decisions。

```text
exercise → single learning unit: 锻炼；运动
letter   → single learning unit: 信；信件
present  → single learning unit: 礼物
Chinese  → chinese#language / chinese#national
taste    → taste#sample / taste#flavour
```

重要修正：`exercise / letter / present` 的旧 `split-required` 来自 dictionary polysemy，而不是当前 source occurrence evidence。当前五-adapter corpus 只支持一个 elementary learning unit，因此撤销伪 split；不人为制造教材未实际教授的第二义项。

---

## 4. Occurrence-partitioned split mechanism — FROZEN

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint explicit OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional Stage-A learning identities
```

硬门禁：

```text
subsets non-empty + disjoint
union = all current occurrences before release
any subgroup unresolved → whole MatchKey remains blocker
new evidence changes cover → requeue
multipart keep uses <MatchKey>#<variant>
multipart TargetSense non-empty
multipart reuse cannot bypass canonical blocker
route-expression/source-only subgroup allowed only in complete resolved partition
Stage-A provisional key != Stable ThirdPartyID
```

---

## 5. Latest validation

```text
production batch 2 decision commit  = 4edffce6b845a78e5c8f94848549da86a3badcf7
production batch 2 workflow         = 34167269958 SUCCESS
production batch 2 bot data commit  = d94cc6d4cdaddc0fd34ee974472cf4577acb0410
residual batch 3 decision commit    = bfac12b6e4921478db659b63ab806376a60d4903
residual batch 3 workflow           = 34167550721 SUCCESS
residual batch 3 bot data commit    = 63faa0ce74af7c3d1f1ca7bef89c44a8cfb60301
```

Batch 3 Completion Recheck：

```text
Decision-only fast path                    PASS
Source adapters reparsed                   NO
Core Completion Recheck                    PASS
Split-aware batch Completion Recheck       PASS
Source-only single-unit correction         PASS
True multipart partition                   PASS
Chinese preview 3 + 3 occurrences          PASS
Taste preview 1 + 1 occurrences            PASS
Transient inbox removed                    PASS
Independent review-queue sample            PASS
Independent Preview sample                 PASS
Independent diff-scope recheck             PASS
Klose Master/Learner/Publish/Anki touched  NO
Stable ThirdPartyID minted                 NO
Final Klose diff executed                  NO
```

Protected invariants：

```text
were / sweets / pleased / lost = held
slept -> sleep reuse
swam  -> swim reuse
won   -> win reuse
```

---

## 6. Residual split lane — EVIDENCE-BOUND

当前 generated `review_bundle.csv` 剩余 split-resolution 约 10 个：

```text
too / french / kind / little / live / look / mouse / plant / right / sound
```

这些 surface 的部分 occurrence 可以判断，但至少一个 current occurrence 不能仅凭现有 standardized source row + ±8 neighborhood 安全归属。当前 `occurrences.csv` 也没有 Unit 字段，因此不允许为了降低 blocker 数强行 complete partition。

典型边界：

```text
mouse  前三个 occurrence 明显是动物；waiyan g4 occurrence 无法安全判断 mouse=老鼠/鼠标
kind   noun/adjective 两义都有强证据，但 Beijing/Waiyan 部分 occurrence 归属不足
right  directions occurrence 清晰，其他 occurrence 正确/方向边界不足
sound  noun/linking-verb 都可能成立，但部分 occurrence 缺少绑定证据
```

无新 source evidence 时，这 10 个默认保持 blocker，不重复推理扫描。

---

## 7. NEXT TASK — ACTIONABLE SEMANTIC RECHECK

从当前 generated `review_bundle.csv` 重新筛 `actionable-semantic`，不要把已有 `*-audited-defer` 当待执行项。

规则：

```text
1. 优先 current source evidence 已经能绑定单一 elementary learning unit 的 surface。
2. canonical-missing / canonical-blocked / context-insufficient 且已有 audited-defer 的不重复处理。
3. dictionary gloss 多义但 source evidence 单义时，允许 keep 窄义 TargetSense。
4. 任何 form reuse 继续要求 canonical reviewed + same lexical sense；multipart canonical 不默认等价于单一 ready canonical。
5. 每批执行 transient inbox + fast workflow + core/batch recheck + independent sample/high-risk/diff recheck。
6. 若 actionable-semantic 已无实质可释放集合，则将 blocker checkpoint 视为 evidence-quality boundary，不以 blocker=0 为目标。
7. 暂不启用 waiyan_start3；所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
```

---

## 8. Completion Recheck contract

每批必须验证：

```text
Source occurrence closure
Explicit reviewed OccurrenceKeys
Split subsets disjoint + complete
Partial split remains blocker
Completed split leaves review_queue
TargetSense non-empty
Canonical reuse ready
Changed source evidence requeues
Review Bundle closes over blockers
Policy proposals derived-only / AutoApply=no
Transient inbox removed
Diff scope only intended third-party/docs layers
Klose Master/Learner/Publish/Anki untouched
```

CI success 不能单独作为结果正确；必须 independent sample + high-risk boundary + diff recheck。

---

## 9. Frozen long-term rules

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
