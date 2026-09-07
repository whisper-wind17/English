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

## 3. Current checkpoint — FIVE-ADAPTER QUALITY BOUNDARY

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

累计演进：

```text
policy/object passes      blockers 256 → 200 / preview 1594 → 1615
split smoke               200 → 197 / preview 1615 → 1621
production split batch 1  197 → 176 / preview 1621 → 1661
production split batch 2  176 → 168 / preview 1661 → 1675
residual split batch 3    168 → 163 / preview 1675 → 1682
scoped reuse smoke        163 → 160 / preview 1682 → 1682
scoped reuse batch        160 → 156 / preview 1682 → 1682
```

当前 review bundle：

```text
deferred-high-ambiguity = 110
object-boundary         = 10
policy-executable       = 3
policy-review           = 23
split-resolution        = 10
actionable-semantic     = 0
semantic-review         = 0
```

这 156 个 blocker 是当前 evidence/policy boundary，不是“漏审 156 个”；Blocker=0 不是质量目标。

---

## 4. Raw source evidence ceiling — VERIFIED

2026-09-08 对 5 个 enabled adapter 的 **48 册原始 XLSX** 做了只读结构审计，直接检查 workbook XML，而不是从 adapter 输出推测：

```text
beijing_start1   12/12 books
renjiao_start1   12/12 books
renjiao_start3    8/8  books
hujiao_start3     8/8  books
waiyan_start1    12/12 books
```

全部结果一致：

```text
Sheets/book       = 1
Max non-empty col = 4
Columns            = A 单词 | B 英音 | C 美音 | D 释义
Rows with E+ data  = 0
Unit/Module/Lesson structural metadata = 0
```

审计中命中的 `lesson / homework / study / PE` 等只是普通 vocabulary rows，不是结构标记。

结论：当前歧义不是 Source Adapter 丢失 Unit 字段；**raw source 本身就是 flat vocabulary list**。因此：

```text
- 不扩 adapter schema 去虚构 Unit/Module；
- 不从固定 row window 推导伪 Unit；
- ±8 neighborhood 只能作为弱 contextual evidence；
- 无更强 source 时，evidence-bound blocker 保持 held/split-required；
- 要继续降低这些 blocker，只能引入更强教材证据或新的 source adapter evidence。
```

一次性 raw-XLSX audit workflow 已删除，没有长期 CI/数据文件残留。

---

## 5. Occurrence-partitioned split — FROZEN

```text
one MatchKey
+ multiple reviewed decision rows
+ disjoint non-empty OccurrenceKeys subsets
+ complete current-occurrence cover
→ multiple provisional Stage-A learning identities
```

硬门禁：union(partitions)=all current occurrences；任一 subgroup unresolved 则整个 MatchKey 仍 blocker；新增 evidence 改变 cover 必须 requeue；multipart keep key=`<MatchKey>#<variant>`；TargetSense 非空；Stage-A provisional key != Stable ThirdPartyID。

Residual split：

```text
too / french / kind / little / live / look / mouse / plant / right / sound
```

这些至少有一个 current occurrence 无法用当前 flat source evidence 安全归属；无新 evidence 不重复强拆。

---

## 6. Scoped multipart canonical reuse — FROZEN

已完成显式 subgroup reuse 能力：form/alias 只能指向已存在、complete + reviewed 的 `<base>#<variant>`；alias 绑定全部 current OccurrenceKeys，不得 mint 新 subgroup，不得覆盖 canonical Display/TargetSense，Preview 只合并 provenance + occurrence count。

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

独立抽查：

```text
fall#verb    = fall|fell / 4 occurrences
cook#verb    = cook|cooking / 4
drink#verb   = drink|drank|drinking / 9
play#general = play|playing / 7
```

剩余 `broken / watches / felt` 有真实 lexical/form ambiguity，不做 scoped reuse。

---

## 7. Scheduler + latest validation

Stable semantic defer 已从 active semantic lanes 排除；`actionable-semantic=0 / semantic-review=0`，无 evidence 变化不重复审计。

```text
scheduler fix commit               = 5ae44d54fb775b39706a9dbcb46d8f27f68cc4de
scoped reuse architecture commit   = 195adb3bcc6ee363cd930ab72b32440e1188727e
scoped reuse smoke workflow        = 34168194013 SUCCESS
scoped reuse smoke bot commit      = b67e5fdd9957e92b14e4be823a8557d8d5ae0329
scoped reuse batch workflow        = 34168312268 SUCCESS
scoped reuse batch bot commit      = 8f93eea74f419dd8187abb5f747672a57ad49709
raw XLSX structure audit run       = 34168623201 SUCCESS
```

Completion Recheck：

```text
Decision-only fast path                    PASS
Source occurrence closure                  PASS
Core / split-aware batch recheck           PASS
Scoped canonical integrity                 PASS
Preview TargetSense                        1682 / 1682
Explicit reviewed OccurrenceKeys           PASS
Changed evidence requeue                   PASS
Stable defer excluded from active lanes    PASS
Transient inbox removed                    PASS
Klose Master/Learner/Publish/Anki touched  NO
Stable ThirdPartyID minted                 NO
Final Klose diff executed                  NO
```

`policy-executable=3` 仍受 grammar-special / lexicalization-risk 保护；proposal engine 不机械 AutoApply。

---

## 8. NEXT TASK — USER GATE BEFORE `waiyan_start3`

Five-adapter Stage-A quality boundary 已形成，当前不要继续为了降低 blocker 数重复扫描 156 个 evidence/policy-bound rows。

**下一 planned adapter 是 `waiyan_start3`，但不得自动启用。必须在用户看到上述 checkpoint 后明确确认。**

用户确认启用后：

```text
1. Enabled=yes 接入 waiyan_start3。
2. 完整 source parse + validation；不能走 decision-only fast path。
3. 用新增 occurrence evidence 对全部 durable decisions 做 exact OccurrenceKeys revalidation。
4. evidence-changed MatchKey 必须自动 requeue，不静默继承旧结论。
5. rebuild review_queue / review_bundle / Preview。
6. 独立核对 source closure、blocker delta、multipart partition、scoped reuse 与高风险 surface。
7. 更新 NEXT.md。
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
