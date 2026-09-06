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

已启用四个小学 Source Adapter：

```text
beijing_start1   = 12 books / 808 occurrences / 734 MatchKeys
renjiao_start1   = 12 books / 908 occurrences / 802 MatchKeys
renjiao_start3   =  8 books / 851 occurrences / 818 MatchKeys
hujiao_start3    =  8 books / 1111 occurrences / 1067 MatchKeys
```

`hujiao_start3` 只纳入沪教版三年级起点 3–6 年级上下册；同目录 7–9 年级牛津英语不属于当前小学 adapter。Hujiao parser/checker 已冻结真实源基线 `1111 / 1067`。

三-adapter 闭合时：

```text
Source occurrences        = 2567
Normalized surfaces       = 1443
Durable decisions         = 1443
Vocabulary preview        = 1223
pending                   = 0
evidence-changed          = 0
true blockers             = 125
```

启用 Hujiao 后，generic builder 自动识别：

```text
722 previously reviewed surfaces with changed evidence
345 completely new surfaces
= 1067 pending
```

说明 evidence-aware decision binding 正常工作，旧 surface 没有静默继承 decision。

截至 GitHub Actions run `34067517554`，Hujiao A–D 已完成多批统一审校并逐批通过 independent Completion Recheck：

```text
Enabled adapters          = 4
Source occurrences        = 3678
Normalized surfaces       = 1788
Durable decisions         = 1510
Vocabulary preview        = 759
Review/blocker surfaces   = 949
Evidence-changed surfaces = 570

Generated current surface state:
keep-identity     = 731
reuse-identity    = 49
held              = 96
pending           = 848
split-required    = 5
route-expression  = 26
source-only       = 33
```

从 Hujiao 初始状态的收敛：

```text
pending            1067 → 848
evidence-changed    722 → 570
review/blocker     1134 → 949
Vocabulary preview  582 → 759
```

已明确保护的新增边界包括：

```text
can        = modal / container → held
call       = 电话/呼叫/称呼 → held
capital    = 首都 / 大写字母 → held
chicken    = 鸡 / 鸡肉 → split-required
Chinese    = 汉语 / 中国人 / 中国的 → split-required
class      = 班级 / 课 → held
clean      = adjective / verb → held
clear      = 清楚 / 晴朗等 → held
cloth      = 布料 → independent identity
clothes    = 衣服 → independent identity
cold       = 寒冷 / 感冒 → split-required
cook       = 烹饪 / 厨师 → split-required
colour     = 颜色 / 涂颜色 → held
country    = 国家 / 乡下 → held
cross / cut / dear / diamond → source context insufficient, held
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master / Learner / Publish / Anki modified = no
```

下一步继续按唯一 `review_queue.csv` 从 D 后段 / E / F 往后审校；真实 held/split blocker 不为了清零而猜测。每批必须 rebuild + independent Completion Recheck，并串行写入唯一决策真源。
