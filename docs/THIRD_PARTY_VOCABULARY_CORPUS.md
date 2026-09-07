# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的统一第三方教材 Vocabulary corpus。目标是把多个第三方小学英语教材词表汇总、按 **learning unit / target sense** 去重，形成一个独立统一词源；等计划中的第三方来源全部处理完成后，再与 Klose Full Stable Vocabulary Identity 做一次最终差集。

## 1. 两阶段流程

```text
Stage A — 第三方内部
多个第三方教材 Raw Vocabulary
→ 各 Source Adapter 只解析 Source Occurrence
→ 通用 candidate matching
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B — 所有计划第三方来源完成后
Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
→ 后续全部作为 Klose 当前教材之外的新词学习
```

Stage A 不因为 Klose 当前已有某词而删除第三方 learning unit；Stage B 才执行最终 Klose diff。

## 2. 产品上真正重要的内容

统一第三方词源只关心 learning unit 本身：

```text
CanonicalWord
TargetSense
BritishIPA
AmericanIPA
Meaning
IdentityStatus
```

教材版本、最早年级、覆盖教材数、出现次数、年级分布不参与学习排序、LearnerLevel、Anki Presentation 或是否学习。`SourceID / Book / Grade / Row / SourceOccurrenceKey` 保留在 Source Occurrence 层，仅用于追溯、重建和 source reconciliation。

## 3. Identity 原则

去重单位不是字符串，而是明确的 learning unit / target sense。

```text
apple = 苹果
→ 一个 Identity

bank = 银行
bank = 河岸
→ 两个 Identity

square = 正方形
square = 广场
→ 两个 Identity
```

Morphology、format alias、multiword、punctuation、substring 等都只能产生 candidate signal，不能自动等同 Identity。Vocabulary / Expression / source-only chunk 必须分开，不能因为原始 XLSX 都放在“单词”列里就全部 mint Vocabulary Identity。

## 4. 最简长期实现 — FROZEN

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

物理路径：

```text
anki/klose/third_party_vocabulary/
├── config/source_adapters.csv
├── review/identity_decisions.csv
└── staging/
    ├── occurrences.csv
    ├── surface_candidates.csv
    ├── review_queue.csv
    └── unified_vocabulary_preview.csv
```

每个 Source Adapter 只做 `Raw source → standardized occurrences.csv`；不负责跨教材比较、morphology/sense 决策、对象路由或 Klose diff。不要恢复 edition-specific `audit → apply → recheck` 多层流水线。

## 5. `identity_decisions.csv` 是唯一内容决策真源

核心字段：

```text
DecisionKey
MatchKey
OccurrenceKeys
Action
CanonicalMatchKey
ObjectType
TargetSense
Status
Confidence
DecisionBasis
Rationale
```

`Action`：

```text
keep-identity       # 独立 Vocabulary learning unit
reuse-identity      # canonicalize / alias / form reuse
split-required      # 同 surface 需要 occurrence-level 拆义
held                # 证据或 identity/form policy 不足
route-expression    # Expression 对象
source-only         # 只保留 Source Fact
pending             # 尚未审校 / evidence 已变化需重审
```

内容审校使用 transient inbox：

```text
review/decision_updates.csv
→ tools/apply_third_party_identity_decision_updates.py
→ identity_decisions.csv
→ inbox 删除
```

成功 workflow 后 `review/` 必须重新只剩 `identity_decisions.csv`。

## 6. Evidence-aware decision binding

一个 surface 已经 reviewed，不代表未来新增教材出现同一字符串时可以自动沿用旧判断。durable decision 的 `OccurrenceKeys` 必须记录审校时实际覆盖的 SourceOccurrenceKey 集合，并持久化为无歧义 JSON array。

```text
当前 MatchKey occurrence set == reviewed occurrence set
→ decision 有效

新增/变化 Source Occurrence 导致集合不同
→ DecisionAction=pending
→ CandidateSignals += decision-evidence-changed
→ 自动回到 review_queue.csv
→ stale SourceMatchKey 不得进入 preview provenance
```

历史 wildcard / legacy serialization 已完成一次性迁移；当前 durable decisions 不允许长期 wildcard。

## 7. Generated views

- `surface_candidates.csv`：每个 normalized surface 一行，展示来源聚合、CandidateSignals 和派生 decision；signal 只是证据。
- `review_queue.csv`：纯派生 view，只包含 `pending / held / split-required` 等需处理 surface，不是第二套决策真源。
- `unified_vocabulary_preview.csv`：只包含 evidence 完整、已 reviewed 的 `keep-identity / reuse-identity` Vocabulary candidates；尚未 mint Stable ThirdPartyID。

## 8. 新教材标准接入方式

```text
1. 新增 Source Adapter，只输出 occurrences.csv
2. source_adapters.csv 增加 Enabled=yes
3. generic builder 合并
4. 全新 surface 自动 pending
5. 已审 surface 若新增 occurrence evidence，也自动 pending
6. 所有内容判断只写 identity_decisions.csv
7. rebuild
8. check_third_party_corpus.py 独立 Completion Recheck
```

不复制 builder/checker，不建立 edition-specific semantic pipeline。

## 9. Stage B：最终 Klose diff

只有计划中的第三方教材都完成 Stage A 后才执行：

```text
Third-party Unified Vocabulary
vs
note_registry.csv + note_registry_extensions.csv
```

同一 learning unit 已在 Klose → `existing-in-klose`；Klose 没有该 target sense → `third-party-new`。

Stage B 之前禁止：

```text
- 因 Klose 已存在而删除第三方 Identity
- 把 Klose NoteID 当第三方 corpus Identity
- 把 Stage-A staging 自动写入 Klose Master / Learner / Release / Publish / Anki
```

## 10. Source Truth 边界

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

冲突按 `docs/SOURCE_RECONCILIATION.md` 处理。

## 11. 当前基线 — 2026-09-07

当前已启用五个小学 Source Adapter：

```text
beijing_start1   = 12 books /  808 occurrences /  734 MatchKeys
renjiao_start1   = 12 books /  908 occurrences /  802 MatchKeys
renjiao_start3   =  8 books /  851 occurrences /  818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
waiyan_start1    = 12 books / 1170 occurrences / 1071 MatchKeys
```

边界：

- `hujiao_start3` 只纳入沪教版三年级起点 3–6 年级上下册；同目录 7–9 年级牛津英语不属于当前小学 adapter；真实源基线 `1111 / 1067` 已冻结。
- `waiyan_start1` 只纳入外研版一年级起点 1–6 年级上下册；外研三年级起点与初高中资料均明确排除；真实源基线 `1170 / 1071` 已冻结。
- 外研版三年级起点 3–6 年级上下册已完成 Source Inventory，确认是独立完整 8-book family，但尚未启用。

四-adapter 阶段曾达到 review closure：

```text
Enabled adapters          = 4
Source occurrences        = 3678
Normalized surfaces       = 1788
Durable decisions         = 1788
Vocabulary preview        = 1441
Review/blocker surfaces   = 219
Evidence-changed surfaces = 0
pending                   = 0
```

启用 `waiyan_start1` 后，generic builder 正确执行 evidence-aware requeue。最新可信 rebuild 为 GitHub Actions run `34074078620`，generated data commit `2bedfeb249ce2acef975b920f2420f3b931b310b`：

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Durable decisions         = 1788
Vocabulary preview        = 799
Review/blocker surfaces   = 1169
Evidence-changed surfaces = 797
pending                   = 1071

Generated current surface actions:
keep-identity     = 765
reuse-identity    = 50
held              = 92
pending           = 1071
split-required    = 6
route-expression  = 45
source-only       = 33
```

集合严格闭合：

```text
4848 - 3678 = 1170
= Waiyan source occurrences

2062 - 1788 = 274
= completely new normalized surfaces

797 evidence-changed existing surfaces
+ 274 completely new surfaces
= 1071 pending
= Waiyan distinct MatchKeys
```

这证明旧 decision 没有被新教材静默继承。`identity_decisions.csv` 仍保留原 1788 条 durable decisions，但只有当其 `OccurrenceKeys` 与五-adapter current occurrence set 完全一致时，generated current state 才继续 reviewed。

典型行为：

```text
apple / afraid
→ 旧 surface + Waiyan 新 occurrence
→ decision-evidence-changed
→ current pending

study
→ durable decision 仍为 held（学习/研究等 semantic collision）
→ Waiyan 新 occurrence 改变 evidence set
→ current pending，等待五-adapter revalidation

saw
→ durable decision 仍为 split-required（see过去式 / 锯子）
→ Waiyan 新 occurrence 改变 evidence set
→ current pending

stronger
→ evidence 未变化
→ reuse-identity → strong 继续 reviewed

swing
→ evidence 未变化
→ keep-identity / 秋千 继续 reviewed
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master / Learner / Publish / Anki modified = no
```

下一步只处理唯一 `review_queue.csv` 中的 1071 个 pending surface：先审 known semantic collisions / morphology-form edge cases，再按字母区间批量 revalidate 稳定项。所有判断继续写入 `identity_decisions.csv`，每批都执行 rebuild + independent Completion Recheck。当前 1071 pending 闭合后，再考虑启用已盘点完成的 `waiyan_start3`；所有计划第三方小学来源完成前仍不进入 Stage B。
