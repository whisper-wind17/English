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

## 3. Current checkpoint — PRODUCTION SPLIT BATCH 2 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1675
Review/blocker surfaces   = 168
Evidence-changed surfaces = 0
Multipart resolved        = 32
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
```

Production split batch 2：8 Source MatchKeys / 16 subgroup decisions。

```text
may / like / play / drop / fall / feel / drink / light
```

Mixed-object partition 已验证：

```text
May(month)       -> Vocabulary keep / may#month
may(modal)       -> Expressions route
like(preference) -> Vocabulary keep / like#preference
like(weather)    -> Expressions route
```

其余 6 个 surface 生成两条 Vocabulary provisional identities。

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

实现：

```text
build_third_party_corpus.py
check_third_party_corpus.py
recheck_third_party_audit_batch.py
```

---

## 5. Latest validation

```text
production batch 1 decision commit  = e17b138d2957e7ab01c5bb1ab0af8180efc9941d
production batch 1 workflow         = 34167059586 SUCCESS
production batch 1 bot data commit  = 7ce39252b0531ebd37d603eec55be68511ce64a1
production batch 2 decision commit  = 4edffce6b845a78e5c8f94848549da86a3badcf7
production batch 2 workflow         = 34167269958 SUCCESS
production batch 2 bot data commit  = d94cc6d4cdaddc0fd34ee974472cf4577acb0410
```

Batch 2 independent recheck：

```text
Decision-only fast path                    PASS
Source adapters reparsed                   NO
Core Completion Recheck                    PASS
Split-aware batch Completion Recheck       PASS
Partition disjoint + complete              PASS
Mixed Vocabulary/Expression partition      PASS
May modal leakage to Vocabulary Preview    NO
Like weather leakage to Vocabulary Preview NO
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

## 6. NEXT TASK — RESIDUAL SPLIT-RESOLUTION

当前 generated `review_bundle.csv` 中剩余 split-resolution 已收敛为 15 个：

```text
too / chinese / exercise / french / kind / letter / little / live /
look / mouse / plant / present / right / sound / taste
```

规则：

```text
1. 不再强求 20–25/batch；只处理 occurrence partition 能完整闭合的 residual surface。
2. 历史 split rationale 只是 evidence，不是事实；若 current occurrence evidence 只支持一个 learning unit，可以改为单一 keep/reuse，而不是强行拆义。
3. evidence 只能明确部分 occurrence 时保持 blocker，不允许为了降低 blocker 数猜测剩余 occurrence。
4. mixed Vocabulary/Expression/source-only subgroup 可以使用，但整个 partition 必须 complete + resolved。
5. residual split lane 收敛后转 actionable-semantic；已 audited-defer / protected blocker 无新 evidence 不重复扫。
6. 每批仍执行 transient inbox + fast workflow + core/batch recheck + independent sample/high-risk/diff recheck。
7. 暂不启用 waiyan_start3；所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
```

当前优先重新核实较可能闭合的 residual：

```text
mouse / too / sound / letter / present / right
```

`chinese / exercise / french / kind / little / live / look / plant / taste` 若无法覆盖全部 occurrences，继续 held/split-required。

---

## 7. Completion Recheck contract

每批必须验证：

```text
Source occurrence closure
Explicit reviewed OccurrenceKeys
Split subsets disjoint + complete
Partial split remains blocker
Completed split leaves review_queue
TargetSense non-empty
Multipart reuse canonical ready
Changed source evidence requeues
Review Bundle closes over blockers
Policy proposals derived-only / AutoApply=no
Transient inbox removed
Diff scope only intended third-party/docs layers
Klose Master/Learner/Publish/Anki untouched
```

CI success 不能单独作为结果正确；必须 independent sample + high-risk boundary + diff recheck。

---

## 8. Frozen long-term rules

- Stable NoteID / ExpressionID 不因来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release；
- provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- generated publish 文件禁止手工维护；
- Anki 保存 FSRS / Review History，GitHub 不重建学习历史。
