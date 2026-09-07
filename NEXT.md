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

动态进度/当前计数只以本 `NEXT.md` 为准；旧 checkpoint 只作历史记录。不要仅凭聊天历史推测当前状态。

---

## 1. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Note Type          = Klose Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 identities

Expressions Stable = 66
Grade-4 priority   = 37
Grade-3-only       = 29
Expressions New/day = 2
FSRS               = ON / 90%
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

---

## 2. Current task — Third-party Multi-Edition Vocabulary Corpus

```text
Stage A
Third-party Source Occurrences
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 禁止因 Klose 当前已有某词而删除第三方 learning unit；当前未进入 Stage B。

`identity_decisions.csv` 是唯一内容决策真源；`review_queue.csv`、`review_bundle.csv`、`decision_proposals.csv` 都是 generated/derived views。Reviewed decision 必须显式绑定当前 JSON `OccurrenceKeys`；evidence 变化必须自动 requeue。

---

## 3. Enabled Source Adapters

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

`waiyan_start3` Source Inventory 已完成，但 **尚未启用**。

---

## 4. Current Stage-A checkpoint — SPLIT ARCHITECTURE SMOKE CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1621
Review/blocker surfaces   = 197
Evidence-changed surfaces = 0
Multipart resolved        = 3
pending                   = 0
```

此前 active pass：

```text
object-boundary original 39 → 29 released/routed + 10 audited-defer
policy batch 1            30 → blockers 256 → 226 / preview 1594 → 1600
policy batch 2            30 → blockers 226 → 207 / preview 1600 → 1615
policy batch 3            28 → blockers 207 → 200 / preview 1615 → 1615
```

### Occurrence-partitioned split architecture

Stage A 已支持：

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
完整释放前 union = all current occurrences
任一 subgroup unresolved → whole MatchKey remains blocker
new source evidence changes cover → requeue
multipart keep uses <MatchKey>#<variant> Stage-A key
multipart TargetSense non-empty
multipart reuse cannot bypass canonical blocker
no Stable ThirdPartyID
```

实现已覆盖：

```text
tools/build_third_party_corpus.py
  → partition completeness/disjointness
  → multipart-reviewed state
  → multiple provisional Preview rows

tools/check_third_party_corpus.py
  → independent partition/provenance/TargetSense/canonical guards

tools/recheck_third_party_audit_batch.py
  → explicit OccurrenceKeys batch verification
  → MatchKey-group-aware multipart verification
```

### Frozen smoke baseline

```text
dish  → dish#plate / dish#food
cut   → cut#verb / cut#injury
dream → dream#aspiration / dream#sleep
```

结果：

```text
blockers   200 → 197
Preview    1615 → 1621
multipart resolved = 3
```

独立确认：3 个 Source MatchKey 均已退出 `review_queue.csv`；6 条 provisional Preview row 均存在、TargetSense 与 subgroup occurrence count 正确；transient inbox 已删除；smoke diff 未触碰 Klose Master/Learner/Publish/Anki。

---

## 5. Latest architecture/smoke validation

```text
build split support commit                    = 59020c3d2fb73692ccb6e80c6330b68a2e2aa273
build zero-multipart regression workflow      = 34166461616   SUCCESS
core checker split support commit             = e4320d30c2de6ab0bc13c7d802400aa222c026ca
core checker regression workflow              = 34166538226   SUCCESS
batch checker split support commit            = cb5662f0962ba6a951f8ba4216a76acb229127e7
batch checker regression workflow             = 34166649909   SUCCESS
smoke decision commit                         = 1997961573164243885042ee83ea86d22acb116d
smoke workflow                                = 34166687405   SUCCESS
smoke bot-generated data commit               = c9ea1f96cb98e0ebf46ab15391dc16f1e2a7a543
Third-party core Completion Recheck           = PASS
Audit-batch Completion Recheck                = PASS
Decision-only fast path                       = PASS
Source adapters reparsed                      = NO
Split partition disjoint/complete             = PASS
Partial split remains blocker                 = PASS
Multipart Preview provenance/count            = PASS
Explicit reviewed OccurrenceKeys              = PASS
Changed source evidence requeues decision     = PASS
Canonical blocker bypass                      = NO
Transient decision inbox                      = removed
Independent diff-scope recheck                = PASS
Klose Master/Learner/Publish/Anki touched     = NO
Stable ThirdPartyID minted                    = NO
Final Klose diff executed                     = NO
```

Protected invariants remain：

```text
were / sweets / pleased / lost = held
slept -> sleep reuse
swam  -> swim reuse
won   -> win reuse
```

---

## 6. NEXT TASK — PRODUCTION SPLIT BATCH

**当前不要自动启用 `waiyan_start3`。**

下一步直接用正式 split mechanism 批处理当前 `split-resolution` lane：

```text
1. 每批 20–25 Source MatchKeys；只选择 occurrence partition 明确的 surface，不为凑数强行归类。
2. 每个 surface 的 decision rows 必须 complete cover current OccurrenceKeys，且 subsets disjoint。
3. 同一 lexical unit 的词形可使用 multipart reuse 指向 reviewed canonical；不得重复 mint provisional identity。
4. 真正不同 target sense 才使用 <MatchKey>#<variant> multipart keep。
5. 如某 subgroup 实际属于 Expression/source-only，可使用 route-expression/source-only；只有全 partition resolved 后 surface 才退出 review。
6. 第一批优先处理 source neighborhood 已明确分开的高置信 surface，例如：
   break / save / square / water / left / saw / orange / film / match / miss /
   past / point / thin / watch / chicken / duck / fish / fly / hot / cook / cold
7. 暂跳过 occurrence 归属仍有疑点的 mouse / like / light / kind / letter / live / look 等。
8. 每批仍执行 fast workflow + core/batch recheck + independent sample/high-risk/diff recheck。
9. blocker quality 稳定后，经用户确认才考虑启用 waiyan_start3。
10. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
```

---

## 7. Completion Recheck contract

每批必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Split occurrence groups disjoint + complete
Partial split remains blocker
Completed split leaves review_queue
Each provisional learning unit has non-empty TargetSense
Multipart reuse canonical ready
Stale SourceMatchKey excluded from preview provenance
review_queue remains pure derived blocker view
Review Bundle closes exactly over current blockers
Policy proposals remain derived-only / AutoApply=no
batch intended decisions exactly persisted
known semantic/morphology/policy blockers preserved unless explicitly changed
transient decision inbox removed
Git diff scope contains only intended third-party layers/tools/docs
Klose Master/Learner/Publish/Anki untouched
```

CI/script success 不能单独作为“结果正确”；必须再做 independent sample + high-risk boundary + diff recheck。

---

## 8. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 occurrence-partitioned split；
- Stage-A `<MatchKey>#<variant>` 不是 Stable ThirdPartyID；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
