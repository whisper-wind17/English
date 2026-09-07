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

## 3. Current checkpoint — PRODUCTION SPLIT BATCH 1 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1661
Review/blocker surfaces   = 176
Evidence-changed surfaces = 0
Multipart resolved        = 24
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
```

Production split batch 1：21 Source MatchKeys / 42 subgroup decisions。

```text
break / save / square / water / left / saw / orange / film / match / miss /
past / point / thin / watch / chicken / duck / fish / fly / hot / cook / cold
```

其中高风险 canonical reuse：

```text
left(past) -> leave
saw(past)  -> see
```

均通过 canonical-ready + provenance 检查；不会 mint 重复 provisional identity。

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
Stage-A provisional key != Stable ThirdPartyID
```

实现：

```text
build_third_party_corpus.py             split build/materialization
check_third_party_corpus.py             core independent partition guards
recheck_third_party_audit_batch.py      split-aware batch Completion Recheck
```

---

## 5. Latest validation

```text
split build commit                  = 59020c3d2fb73692ccb6e80c6330b68a2e2aa273
split core-check commit             = e4320d30c2de6ab0bc13c7d802400aa222c026ca
split batch-check commit            = cb5662f0962ba6a951f8ba4216a76acb229127e7
smoke data commit                   = c9ea1f96cb98e0ebf46ab15391dc16f1e2a7a543
production batch 1 decision commit  = e17b138d2957e7ab01c5bb1ab0af8180efc9941d
production batch 1 workflow         = 34167059586 SUCCESS
production batch 1 bot data commit  = 7ce39252b0531ebd37d603eec55be68511ce64a1
```

Validation：

```text
Decision-only fast path                    PASS
Source adapters reparsed                   NO
Core Completion Recheck                    PASS
Split-aware batch Completion Recheck       PASS
Partition disjoint + complete              PASS
Partial split remains blocker              PASS
Preview TargetSense/provenance/count       PASS
Canonical blocker bypass                   NO
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

## 6. NEXT TASK — CONTINUE SPLIT-RESOLUTION PRODUCTION

继续从当前 generated `review_bundle.csv` 读取剩余 `split-resolution`；不要沿用历史候选列表。

规则：

```text
1. 每批目标 20–25 Source MatchKeys；证据不足时宁可少，不凑数。
2. occurrence neighborhood 可明确 partition 才处理。
3. 同 lexical unit 的 inflected/form subgroup 优先 reuse reviewed canonical。
4. 真正不同 target sense 使用 <MatchKey>#<variant> keep。
5. functional/grammar subgroup 如对象边界不明确，不为了释放 blocker 强行 route。
6. 已 audited-defer / protected blocker 无新 evidence 不重复扫。
7. 每批执行 transient inbox + fast workflow + core/batch recheck + independent sample/high-risk/diff recheck。
8. split-resolution 明显收敛后再回 actionable-semantic；不要在低 actionability form 上消耗吞吐。
9. blocker quality 稳定后，经用户确认才考虑启用 waiyan_start3。
10. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff。
```

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
