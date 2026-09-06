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

教材版本、最早年级、覆盖教材数、出现次数、年级分布不参与学习排序、LearnerLevel、Anki Presentation 或是否学习。`SourceID / Book / Grade / Row / SourceOccurrenceKey` 仍保留在 Source Occurrence 层，只用于追溯、重建和 source reconciliation。

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

Morphology、format alias、multiword、punctuation、substring 等都只能产生 candidate signal，不能自动等同 Identity：

```text
sock / socks
child / children
How old ...? / how old
fly / fly a kite
```

Vocabulary / Expression / source-only chunk 也必须分开，不能因为原始 XLSX 把它们都放在“单词”列里就全部 mint Vocabulary Identity。

## 4. 最简长期实现 — FROZEN

长期 active model 只有：

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
├── config/
│   └── source_adapters.csv
├── review/
│   └── identity_decisions.csv
└── staging/
    ├── occurrences.csv
    ├── surface_candidates.csv
    ├── review_queue.csv
    └── unified_vocabulary_preview.csv
```

每个 Source Adapter 只做：

```text
Raw source
→ standardized occurrences.csv
```

它不负责跨教材比较、morphology/sense 决策、对象路由或 Klose diff。不要恢复 edition-specific `audit → apply → recheck` 多层流水线。

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

内容审校可使用 transient inbox：

```text
review/decision_updates.csv
→ tools/apply_third_party_identity_decision_updates.py
→ merge 到 identity_decisions.csv
→ inbox 删除
```

成功 workflow 结束后，`review/` 必须重新只剩 `identity_decisions.csv`。

## 6. Evidence-aware decision binding

一个 surface 已经 reviewed，不代表未来新增教材出现同一字符串时可以自动沿用旧判断。

因此 durable decision 的 `OccurrenceKeys` 必须记录**审校时实际覆盖的 SourceOccurrenceKey 集合**，持久化格式为无歧义 JSON array，例如：

```text
["beijing_start1|g3-upper|r010|bank","renjiao_start1|g4-upper|r022|bank"]
```

规则：

```text
当前 MatchKey occurrence set == decision reviewed occurrence set
→ decision 仍有效

新增/变化 Source Occurrence 导致集合不同
→ DecisionAction=pending
→ CandidateSignals += decision-evidence-changed
→ 自动回到统一 review_queue.csv
→ stale SourceMatchKey 不得进入 preview provenance
```

这样可以防止：

```text
旧教材：bank = 银行（已 reviewed）
新教材：bank = 河岸
```

被静默沿用为“银行”。

历史 `OccurrenceKeys=*` / 旧的歧义 pipe serialization 已完成一次性迁移；当前 durable decisions 全部使用 JSON array，不再允许 wildcard 状态长期存在。

## 7. Generated views

`surface_candidates.csv`：每个 normalized surface 一行，展示来源聚合、CandidateSignals、候选 MatchKey 和当前派生 Decision 状态；candidate signal 只是证据。

`review_queue.csv`：纯派生 view，只包含 `pending / held / split-required` 等仍需处理的 surface，不是第二套决策真源。

`unified_vocabulary_preview.csv`：只包含当前 evidence 完整且已经 reviewed 的 `keep-identity / reuse-identity` Vocabulary candidates；仍是 preview，尚未 mint Stable ThirdPartyID。

## 8. 新教材标准接入方式

```text
1. 新增 Source Adapter，只输出标准 occurrences.csv
2. 在 config/source_adapters.csv 增加 Enabled=yes
3. generic builder 合并
4. 全新 surface 自动 pending
5. 已审 surface 若新增 occurrence evidence，也自动 pending
6. 所有内容判断只写 identity_decisions.csv
7. rebuild
8. check_third_party_corpus.py 独立 Completion Recheck
```

不复制现有 builder/checker，不建立 edition-specific semantic pipeline。

## 9. Stage B：最终 Klose diff

只有计划中的第三方教材都完成 Stage A 后才执行：

```text
Third-party Unified Vocabulary
vs
note_registry.csv + note_registry_extensions.csv
```

仍然 sense-aware：

```text
同一 learning unit 已在 Klose
→ existing-in-klose

Klose 没有该 target sense
→ third-party-new
```

`third-party-new` 的产品含义是：**Klose 当前实际教材之外、后续计划学习的新 Vocabulary**。

Stage B 之前禁止：

```text
- 因 Klose 已存在而删除第三方 Identity
- 把 Klose NoteID 当第三方 corpus Identity
- 把 Stage-A staging 自动写入 Klose Master / Learner / Release / Publish / Anki
```

## 10. Source Truth 边界

第三方统一 corpus 即使充分清洗，仍是第三方数据：

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

冲突继续按 `docs/SOURCE_RECONCILIATION.md` 处理。

## 11. 当前基线 — 2026-09-07

已启用：

```text
beijing_start1
  books       = 12
  occurrences = 808
  MatchKeys   = 734

renjiao_start1
  books       = 12
  occurrences = 908
  MatchKeys   = 802

renjiao_start3
  books       = 8
  occurrences = 851
  MatchKeys   = 818
```

联合 Stage A：

```text
Enabled adapters          = 3
Source occurrences        = 2567
Normalized surfaces       = 1443
Durable decisions         = 1271
Vocabulary preview        = 857
Review/blocker surfaces   = 526
Evidence-changed surfaces = 290

Generated current surface state:
keep-identity     = 839
reuse-identity    = 35
held              = 62
pending           = 462
split-required    = 2
route-expression  = 16
source-only       = 27
```

`renjiao_start3` 刚接入时：

```text
299 completely new surfaces
519 reviewed surfaces with changed evidence
= 818 pending
```

已经完成 7 批统一审校：

```text
resolved/reclassified pending surfaces = 356
pending                            818 → 462
new-surface pending                299 → 172
evidence-changed pending           519 → 290
Vocabulary preview                 553 → 857
review/blocker                     848 → 526
```

代表性安全边界继续保留：

```text
May(月份) / may(情态动词)
like=喜欢 / similarity construction
square=正方形 / square=广场
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
hot=温度 / hot=辣或食物语义
orange=水果 / orange=颜色
kind=种类 / kind=友好的
live=居住 / live=活着
mouse=动物 / mouse=电脑鼠标

glasses=眼镜 保留独立 lexical identity，不因 glass morphology 合并
our / ours 保留不同语法 learning unit
Mrs / Mr 不因字符串 morphology 信号合并
laughed → laugh
licked → lick
longer → long
older → old
noodles → noodle
parents → parent
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master / Learner / Publish / Anki modified = no
```

下一步继续只处理统一 `review_queue.csv`；对真实 held/split blocker 不为了清零而猜测。