# NEXT — Klose Learning

Last updated: 2026-09-07

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前第三方 Vocabulary corpus 任务继续读取：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ anki/klose/third_party_vocabulary/config/source_adapters.csv
→ anki/klose/third_party_vocabulary/review/identity_decisions.csv
→ anki/klose/third_party_vocabulary/staging/review_queue.csv
```

涉及 Klose 实际教材 reconciliation 时再读取：

```text
docs/SOURCE_RECONCILIATION.md
```

Expressions 任务读取：

```text
docs/EXPRESSIONS_SYSTEM.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Vocabulary operational baseline

Grade-4 Vocabulary 已闭环并正常学习：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

完整 Klose Stable Vocabulary Identity Registry：

```text
note_registry.csv + note_registry_extensions.csv
= 901 identities
```

GitHub 管 Source / Identity / Learner / Release；Anki 是 FSRS / Review History / Due / Interval / Card State 真源。

---

## 2. Expressions operational baseline

三、四年级 Expressions 已完成首次正式闭环：

```text
Stable Expressions = 66
Grade-4 priority    = 37
Grade-3-only        = 29
LearningOrder       = 000001..000066
approved            = 66
admitted            = 66
release-ready       = 66
```

Anki：

```text
Deck              = Klose-English::Expressions
Note Type         = Klose Expression
Cards             = 66
New/day           = 2
FSRS              = ON
Desired retention = 90%
AnkiWeb Sync       = completed
```

当前处于 real-learning pilot。不要因 repo 重建改变已经进入 Learning / Review 的 Card 调度状态。

---

## 3. Current repo task — Third-party Multi-Edition Vocabulary Corpus

长期目标已冻结：

> 把北京版、人教版、沪教版及其他第三方小学教材词汇汇总成一个统一、sense-aware 去重的第三方词源。教材来源、最早年级、覆盖教材数、出现次数、年级分布不参与学习决策。所有第三方来源处理完成后，再与 Klose Full Stable Identity Registry 做一次最终去重，剩余 learning units 全部作为 Klose 当前教材之外的新词学习。

两阶段流程：

```text
Stage A
所有第三方 Source Occurrences
→ 第三方内部 sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B（所有计划第三方来源完成后才执行）
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
```

Stage A 不因 Klose 当前已有某词而删除第三方 learning unit。

---

## 4. Simplified Stage-A architecture — FROZEN

原多层 `audit → apply → recheck` edition-specific 流水线已完成收敛。长期 active model 只有：

```text
Source Adapter occurrences
+ config/source_adapters.csv
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ staging/occurrences.csv
→ staging/surface_candidates.csv
→ staging/review_queue.csv
→ staging/unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

职责：

```text
Source Adapter = 只解析 Source Fact
CandidateSignals = 只提供匹配证据
identity_decisions.csv = 唯一内容决策真源
review_queue.csv = 纯派生 unresolved/blocker view
unified_vocabulary_preview.csv = reviewed Vocabulary preview
```

`identity_decisions.csv` Action：

```text
keep-identity
reuse-identity
split-required
held
route-expression
source-only
pending
```

Content decision 是 data；Python 只负责通用生成和校验。不要恢复旧的 exact / morphology / semantic / multiword / routing 专项 pipeline。

---

## 5. Enabled Source Adapters

配置真源：

```text
anki/klose/third_party_vocabulary/config/source_adapters.csv
```

当前：

```text
beijing_start1
  Source books       = 12
  Source occurrences = 808
  MatchKeys          = 734

renjiao_start1
  Source books       = 12
  Source occurrences = 908
  MatchKeys          = 802
```

Renjiao adapter 物理职责已经收敛为：

```text
Raw 12 XLSX
→ source_reference/renjiao_start1_staging/README.md
→ source_reference/renjiao_start1_staging/occurrences.csv
```

它不再比较北京版，不再生成 exact/morph/new/semantic 队列。

人教版“三年级起点”未来作为独立 adapter，不能混入 `renjiao_start1`。

---

## 6. Current Stage-A baseline

北京 + 人教一年级起点：

```text
Enabled adapters        = 2
Source occurrences      = 1716
Normalized surfaces     = 1144
Durable decisions       = 1144
Vocabulary preview      = 851
Review/blocker surfaces = 254

keep-identity     = 849
reuse-identity    = 13
held              = 50
pending           = 192
split-required    = 12
route-expression  = 3
source-only       = 25
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master modified      = no
Klose Learner modified     = no
Klose Publish modified     = no
Anki modified              = no
```

---

## 7. Simplification Completion Recheck — PASS

2026-09-07 已完成清理后的最终独立 Completion Recheck，GitHub Actions run `34044221086` 全部成功。

除数据闭合外，checker 现在还把“最简物理架构”本身作为 executable invariant：

```text
third_party_vocabulary/staging/
  README.md
  occurrences.csv
  surface_candidates.csv
  review_queue.csv
  unified_vocabulary_preview.csv

third_party_vocabulary/review/
  identity_decisions.csv

source_reference/renjiao_start1_staging/
  README.md
  occurrences.csv
```

同时显式检查旧 multi-pass third-party 工具不得重新出现。

本次 Recheck 结果：

```text
Simplified physical layout                    = yes
Legacy multi-pass tools absent                = yes
Source occurrence closure                     = yes
Known semantic blockers preserved             = yes
Known morphology decisions preserved          = yes
Unreviewed Beijing multiword carry-forward blocked = yes
Klose publishing state untouched              = yes
Generated Stage-A data drift                  = no
```

持续保护的代表性边界：

```text
May(月份) / may(情态动词)
like=喜欢 / weather-like construction
square=正方形 / square=广场
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
study=学习 / study=书房

danced → dance
gloves → glove
cartoons → cartoon
scissors / crossroads 保留 lexicalized learning unit
slept / swam / were / won 保持 irregular-form blocker
```

此前迁移误差也已锁定：`a few / get well / how many / ice cream / make use of / pencil case / sweet potato / take part in / the U.K. / the U.S.A. / the United States of America` 未经过 object routing，不得因北京 seed 身份自动进入 Vocabulary Identity。

---

## 8. NEXT TASK — resolve the single unified review queue

唯一内容工作入口：

```text
anki/klose/third_party_vocabulary/staging/review_queue.csv
```

当前 254 个 surface 只按最终 learning-unit 决策处理，不再按旧 pipeline 分类执行。

每条只能写回：

```text
anki/klose/third_party_vocabulary/review/identity_decisions.csv
```

目标 Action：

```text
keep-identity       # 独立 Vocabulary learning unit
reuse-identity      # canonicalize / form / alias reuse
route-expression    # Expression 对象
source-only         # 仅保留 Source Fact
split-required      # 真实同形异义，需要 occurrence-level split
held                # 证据或 identity policy 仍不足
```

工作规则：

```text
1. 能从当前 source evidence 高置信 resolve 的直接 resolve；
2. 缺真实教材上下文的义项继续 held，不为了 pending=0 猜测；
3. 所有内容判断只落 identity_decisions.csv；
4. rebuild；
5. independent Completion Recheck；
6. corpus 足够稳定前不 mint Stable ThirdPartyID；
7. 所有计划第三方来源完成前不执行 Stage-B Klose diff。
```

完成当前两 adapter 的统一 queue 后，再接入下一个第三方 Source Adapter。

---

## 9. Deferred

```text
Grade 1–3 Klose actual-source Vocabulary reconciliation
Grade 5/6 actual-source reconciliation
99 held legacy Vocabulary Notes 的 British/American IPA 补齐（对应 admission 前）
Expressions one-month real-learning evaluation
```

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
