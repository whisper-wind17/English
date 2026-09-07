# NEXT — Klose Learning

Last updated: 2026-09-07

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

## 4. Current Stage-A checkpoint — OBJECT BOUNDARY BATCH 1 CLOSED

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 2062
Vocabulary preview        = 1592
Review/blocker surfaces   = 260
Evidence-changed surfaces = 0
pending                   = 0

keep-identity     = 1583
reuse-identity    =   83
held              =  213
split-required    =   47
route-expression  =  102
source-only       =   34
```

Source reconciliation lane remains closed at `0`.

### Object-boundary batch 1

25 个 blocker 一次处理：

```text
19 route-expression
├─ could not / did not / do not / does not
├─ he is / here is / i am / is not / it is / she is
├─ should not / there are / there is / they are
└─ was not / were not / what is / where is / will not

6 keep-identity
├─ Parents' Day → 家长日
├─ pick up      → 捡起；拾起
├─ put on       → 穿上；戴上
├─ to go        → 外带；打包带走
├─ turn around  → 转身；掉头
└─ turn back    → 返回；往回走
```

结果：

```text
blockers       285 → 260
preview        1586 → 1592
object-boundary 39 → 14
```

多词项没有机械统一路由：稳定 lexical chunk 仍可属于 Vocabulary；开放句型、语法 presentation frame、交际框架才 route-expression。

---

## 5. Latest batch validation

```text
GitHub Actions run                         = 34138413698   SUCCESS
decision commit                            = 5fc29c00134afea4d65f7c2e06045c85c2504ef2
bot-generated data commit                  = fcbabb95bed5fb758faeb1ab600e4fa551fca1ab
batch decisions                            = 25 = 19 route-expression + 6 keep
Vocabulary Preview TargetSense complete    = 1592 / 1592
Third-party core Completion Recheck         = PASS
Audit-batch Completion Recheck              = PASS
Decision-only fast path                     = PASS
Source adapters reparsed                    = NO
Review Bundle closure                       = 260 / 260 PASS
Source-reconciliation lane                  = 0
Policy proposals remaining                  = 0
Explicit reviewed OccurrenceKeys            = PASS
Changed source evidence requeues decision   = PASS
Canonical blocker bypass                    = NO
Transient decision inbox                    = removed
Klose Master/Learner/Publish/Anki touched   = NO
Stable ThirdPartyID minted                  = NO
Final Klose diff executed                   = NO
```

Independent diff recheck：本批前 `5393084...` → bot `fcbabb95...` 仅变化 third-party audit/review/staging 六个文件：

```text
review_bundle.csv
identity_decisions.csv
staging/README.md
review_queue.csv
surface_candidates.csv
unified_vocabulary_preview.csv
```

无 Source Adapter 重解析、无 Klose Master/Learner/Publish/Anki、无 tool/code 修改。

---

## 6. Throughput architecture v2 — CURRENT

当前 260 blockers 分类：

```text
abbreviation-policy       = 14
form-policy               = 81
functional-polysemy       = 18
multiword-object-boundary = 14
semantic-cross-source     = 56
semantic-easy             = 28
semantic-hard             =  2
split-resolution          = 47
```

当前 execution lanes：

```text
source-reconciliation-needed  = 0
actionable-semantic           = 0
semantic-review               = 2   # ever/player; audited-defer exceptions
policy-executable             = 10  # proposal engine outputs 0
policy-review                 = 85
object-boundary               = 14
deferred-high-ambiguity       = 102
split-resolution              = 47
```

Actionability bands：

```text
80–100 =   2
65–79  =  10
45–64  =  47
0–44   = 201
```

`policy-executable = 10` 仍全部被 proposal guard 拦截；`decision_proposals.csv` 当前为空，不能机械 reuse。

`ever/player` 已人工 defer；无新 evidence 不重复处理。`deferred-high-ambiguity` 默认不扫描。

---

## 7. Remaining object-boundary set

当前剩余 14：

```text
in one hour
all right
get through
go out
has got
keep on
out of
see the world
street sweeper
take away
take down
take off
all over
a lot
```

其中多项已有明确“证据不足/多义”审计结论。第二批应一次性做 residual pass：能明确对象边界才 release/route；其余保留 held 并标成 audited-defer，避免后续重复扫描。

---

## 8. NEXT TASK — CLOSE OBJECT BOUNDARY, THEN POLICY REVIEW

**当前不要自动启用 `waiyan_start3`。**

```text
1. 一次处理剩余 object-boundary = 14；这是该 lane 的 residual batch。
2. 对已有 source evidence 仍不足的项保留 held；不要为了清零 blocker 强行 release。
3. residual pass 后不再反复扫描 audited-defer object-boundary；无新 evidence 不重审。
4. 然后切换到 policy-review = 85，按 frozen form/-ing/abbreviation policy 高吞吐批量处理。
5. policy-executable = 10 当前 proposal = 0，不直接机械处理。
6. deferred-high-ambiguity = 102 默认不扫描。
7. split-resolution = 47 等待 occurrence-partitioned multiple provisional Stage-A identity 架构，不把多义词压成单一 TargetSense。
8. 每个 batch：1 decision_updates + 1 fast workflow + core/batch/independent recheck；闭环后立即更新 NEXT.md。
9. blocker 数量下降不是质量目标。
10. blocker quality 稳定后向用户展示结构；用户确认后才考虑启用 waiyan_start3。
11. 所有计划第三方小学来源完成前不执行 Stage-B Klose diff，不 mint Stable ThirdPartyID。
```

---

## 9. Completion Recheck contract

每批必须验证：

```text
Source adapter occurrence closure
Decision schema / canonical reuse correctness
Explicit reviewed OccurrenceKeys JSON arrays
Changed source evidence automatically requeues
Stale SourceMatchKey excluded from preview provenance
review_queue remains pure derived blocker view
Review Bundle closes exactly over current blockers
Policy proposals remain derived-only / AutoApply=no
Vocabulary Preview TargetSense all non-empty
batch intended decisions exactly persisted
known semantic/morphology/policy blockers preserved unless explicitly changed
transient decision inbox removed
Git diff scope contains only intended third-party layers
Klose Master/Learner/Publish/Anki untouched
```

CI/script success 不能单独作为“结果正确”；必须再做 independent sample + high-risk boundary + diff recheck。

---

## 10. Frozen long-term rules

- Stable NoteID / ExpressionID 不因教材顺序、来源增加或 Presentation 修改而变化；
- Source Occurrence 与 Vocabulary / Expression Identity 分离；
- Source Grade、LearnerLevel、Learning Admission 分离；
- Vocabulary 与 Expressions 使用独立 Identity / Review / Release / Note Type；
- 第三方教材 provenance 只用于回溯，不作为学习优先级；
- MatchKey / morphology / format alias 只做 candidate matching；
- 同 surface 不同 target sense 必须允许 split；
- generated publish 文件禁止手工维护；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。
