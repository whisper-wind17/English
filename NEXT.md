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

## 3. Current checkpoint — HIGH-THROUGHPUT POLICY PASS CLOSED

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
```

### 本轮吞吐定义修正

此前把“净释放数”误当成“review throughput”，导致只挑容易释放的少量 surface，退化成低吞吐逐项处理。现已修正：

```text
Original policy-review lane = 23 surfaces
Reviewed end-to-end         = 23 / 23
Released                    = 3
Audited-defer               = 20
policy-review after pass    = 0
```

这两个指标必须分开：

```text
Review throughput = 一批实际完成审查/归类多少 surface
Net blocker release = 最终有多少 surface 能安全离开 blocker
```

高吞吐要求前者按 20–30/batch 执行；后者服从 evidence quality，不为数字强行 release。

本轮 release：

```text
a        → keep-identity / 一个；一（用于辅音音素前）
mice     → keep-identity / 老鼠（mouse 的复数）
sometime → keep-identity / 在某一时候；改天
```

`sweets` 原拟 release，但 core checker 正确拦截 `Protected form-policy blocker lost: sweets`。未削弱 checker；最终保持 audited-defer。该失败 run 没有持久化错误 decision。

---

## 4. Review-lane normalization — FROZEN

发现 scheduler 只会把 semantic `audited-defer` 移出 active lane，而 form-policy / abbreviation-policy / object-boundary 的已审核 defer 会反复重新出现，造成重复扫描和假低吞吐。

已加入 derived-only normalizer：

```text
tools/normalize_third_party_review_lanes.py
```

规则：

```text
held + DecisionBasis contains audited-defer
→ ReviewLane = deferred-high-ambiguity
→ RecommendedBatchSize = 0
→ no identity decision change
→ source evidence changed 后仍按原机制 requeue
```

最终 normalized review bundle：

```text
deferred-high-ambiguity = 140
policy-executable       = 3
split-resolution        = 10
policy-review           = 0
object-boundary         = 0
actionable-semantic     = 0
semantic-review         = 0
Total blockers          = 153
```

因此 140 个 deferred 不是“未审”；没有新 evidence 时禁止重复扫描。

`policy-executable=3`：

```text
were / pleased / lost
```

proposal engine 仍输出 0：1 个 grammar-special + 2 个 multi-POS/lexicalization-risk。按 frozen policy 不机械 AutoApply，也不为降低 blocker 强行处理。

---

## 5. Raw source evidence ceiling — VERIFIED

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

## 6. Occurrence-partitioned split + scoped reuse — FROZEN

Occurrence split：

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint non-empty OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional Stage-A learning identities
```

Residual split：

```text
too / french / kind / little / live / look / mouse / plant / right / sound
```

这些至少有一个 current occurrence 无法用当前 flat source evidence 安全归属；无新 evidence 不重复强拆。

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

## 7. Latest validation

Lane normalization infrastructure：

```text
workflow integration commit = 4c1adaf7737d30e06e2abcf5d437a67f9430d99f
normalization workflow       = 34169519390 SUCCESS
```

Full policy batch：

```text
corrected decision commit    = 9b87c3be682b2bc6961d44b95c8320d671f85543
workflow                     = 34169727538 SUCCESS
bot data commit              = f08de4716ae51e38d7961fe040e93183dd96dec6
batch decisions              = 14
  keep-identity              = 3
  held/audited-defer         = 11
```

Final historical-marker normalization：

```text
PS decision commit           = df80f2c156e43cdf600be8af8af32536f35e6349
workflow                     = 34169781528 SUCCESS
bot data commit              = b15d92fc5853f894f3547641a46b6d6220b80140
```

Completion Recheck：

```text
Decision-only fast path                    PASS
Source adapters reparsed in decision runs  NO
Source occurrence closure                  PASS
Core Completion Recheck                    PASS
Audit-batch Completion Recheck             PASS
Preview TargetSense                        1685 / 1685
Explicit reviewed OccurrenceKeys           PASS
Changed evidence requeue                   PASS
Audited defer absent from active lanes     PASS
policy-review                              0
object-boundary                            0
Transient inbox removed                    PASS
Klose Master/Learner/Publish/Anki touched  NO
Stable ThirdPartyID minted                 NO
Final Klose diff executed                  NO
```

Independent samples：

```text
a        Preview reviewed / 4 occurrences
mice     Preview reviewed / 2 occurrences
sometime Preview reviewed / 1 occurrence
sweets   remains blocker / audited-defer
broken   remains blocker / audited-defer
felt     remains blocker / audited-defer
```

Diff-scope recheck from pre-normalization five-adapter checkpoint through `b15d92f` only touched workflow + third-party review/audit/staging + lane-normalizer tool；未触碰 Klose Master/Learner/Publish/Anki。

---

## 8. NEXT TASK — USER GATE BEFORE `waiyan_start3`

Five-adapter Stage-A 的可执行 review lanes 已按高吞吐方式清空；当前剩余：

```text
140 = reviewed evidence/policy defers
  3 = policy-executable but proposal guard blocks AutoApply
 10 = residual split requiring stronger occurrence evidence
```

下一 planned evidence expansion 是 `waiyan_start3`，但不得自动启用。用户确认后：

```text
1. Enabled=yes 接入 waiyan_start3。
2. 完整 source parse + validation；不能走 decision-only fast path。
3. 对 durable decisions 做 exact OccurrenceKeys revalidation。
4. evidence-changed MatchKey 自动 requeue，不静默继承旧结论。
5. rebuild review_queue / review_bundle / Preview。
6. 新 active lanes 继续按 frozen batch-size 高吞吐处理，不退回逐项 review。
7. 独立核对 source closure、blocker delta、multipart partition、scoped reuse、高风险 surface。
8. 更新 NEXT.md。
```

仍禁止：Stage-B Klose diff、Stable ThirdPartyID minting、修改 Klose Master/Learner/Publish/Anki、为了 blocker=0 强行解释 evidence-bound rows。

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
