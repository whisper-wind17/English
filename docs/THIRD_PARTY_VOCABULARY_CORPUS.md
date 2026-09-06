# Third-party Multi-Edition Vocabulary Corpus

本文定义 Klose 的统一第三方教材 Vocabulary corpus。目标很简单：把多个第三方小学英语教材词表汇总、按 **learning unit / target sense** 去重，形成一个独立的统一第三方词源；等计划中的第三方来源全部处理完成后，再与 Klose Full Stable Vocabulary Identity 做一次最终差集。

## 1. 两阶段流程

```text
Stage A — 第三方内部

多个第三方教材 Raw Vocabulary
→ 各 Source Adapter 只解析 Source Occurrence
→ 通用 candidate matching
→ sense-aware Identity Resolution
→ Third-party Unified Vocabulary

Stage B — 所有第三方来源完成后

Third-party Unified Vocabulary
→ vs Klose Full Stable Identity Registry
→ Third-party New Vocabulary Pool
→ 后续全部作为 Klose 当前教材之外的新词学习
```

Stage A 不因为 Klose 当前已有某词而删除第三方 learning unit；Stage B 只执行一次最终 Klose diff。

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

以下信息不参与学习排序、LearnerLevel、Anki Presentation 或是否学习：

```text
来自哪个教材版本
最早出现年级
多少套教材包含
跨教材/跨册出现次数
主要分布年级
```

SourceID / Book / Grade / Row 等来源信息仍保留在 Source Occurrence 层，仅用于追溯、重建和 source reconciliation。

## 3. Identity 原则

去重单位不是字符串，而是一个明确 learning unit / target sense。

同 surface、同义项：

```text
apple = 苹果
→ 一个 Identity
```

同 surface、不同义项：

```text
bank = 银行
bank = 河岸

square = 正方形
square = 广场

cook = 烹饪；煮
cook = 厨师
```

必须保留多个 Identity。

Morphology、format alias、multiword、punctuation、substring 等都只能产生 candidate signal，不能自动等同 Identity：

```text
sock / socks
child / children
How old ...? / how old
fly / fly a kite
```

Vocabulary / Expression / source-only chunk 也必须分开，不能因为原始 XLSX 把它们都放在“单词”列里就全部 mint Vocabulary Identity。

## 4. 最简长期实现

不要为每一种风险建立一条独立处理流水线。长期 active model 只有四个核心数据对象：

```text
1. Source Adapter occurrences
2. config/source_adapters.csv
3. review/identity_decisions.csv
4. generated Stage-A views
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

核心工具：

```text
tools/build_third_party_corpus.py
→ 通用生成器

tools/check_third_party_corpus.py
→ 独立 Completion Recheck
```

每个 Source Adapter 只负责：

```text
Raw source
→ standardized occurrences.csv
```

它不负责跨教材比较，不负责 morphology/sense 决策，也不负责 Klose diff。

## 5. `identity_decisions.csv` 是唯一内容决策真源

候选信号可以很多，但内容决策只有一套。

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

`Action` 当前统一为：

```text
keep-identity       # 保留为独立 Vocabulary learning unit
reuse-identity      # 归到 canonical learning unit
split-required      # 同 surface 需要拆义项/按 occurrence 拆分
held                # 当前证据或 identity policy 不足
route-expression    # 进入 Expression 路由，不生成 Vocabulary Identity
source-only         # 只保留 Source Fact
pending             # 尚未审校
```

例如：

```text
danced
→ reuse-identity
→ CanonicalMatchKey=dance

scissors
→ keep-identity

won
→ held
→ irregular-form policy

French
→ split-required
```

新的教材接入后，如果出现没有 decision 的新 surface，builder 自动把它放入 `review_queue.csv`；不需要为新教材再创建一套 `audit_xxx.py → apply_xxx.py → recheck_xxx.py`。

## 6. Generated views

`surface_candidates.csv`：

- 每个 normalized surface 一行；
- 展示来源聚合、CandidateSignals、候选 MatchKey 和当前 Decision；
- candidate signal 只是证据。

`review_queue.csv`：

- 纯派生 view；
- 只包含 `pending / held / split-required` 等需要继续处理的 surface；
- 不作为第二套决策真源。

`unified_vocabulary_preview.csv`：

- 只包含当前已经 reviewed 的 `keep-identity / reuse-identity` Vocabulary candidate；
- 目前仍是 preview；
- 还没有 mint Stable ThirdPartyID。

## 7. 新教材的标准接入方式

以后增加沪教版、人教三年级起点或其他版本，只做：

```text
1. 新增 Source Adapter，输出标准 occurrences.csv
2. 在 config/source_adapters.csv 增加一行并 Enabled=yes
3. 运行 build_third_party_corpus.py
4. 新 surface / 新冲突自动进入统一 review_queue.csv
5. 只修改 identity_decisions.csv 完成审校
6. rebuild
7. check_third_party_corpus.py 做独立 Completion Recheck
```

不复制现有 builder/checker，不建立 edition-specific semantic pipeline。

## 8. Stage B：最终 Klose diff

只有当计划中的第三方教材都完成 Stage A 后才执行：

```text
Third-party Unified Vocabulary
vs
note_registry.csv + note_registry_extensions.csv
```

规则仍然是 sense-aware：

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

## 9. Source Truth 边界

第三方统一 corpus 即使充分清洗，仍是第三方数据：

```text
Klose 手中实际教材
> 可确认同 Edition 的官方材料
> Third-party Multi-Edition Vocabulary Corpus
```

与 Klose 实际教材发生冲突时，继续按 `docs/SOURCE_RECONCILIATION.md` 处理。

## 10. 当前基线

已启用：

```text
beijing_start1   808 occurrences
renjiao_start1   908 occurrences
```

联合 Stage A：

```text
Source occurrences      = 1716
Normalized surfaces     = 1144
Durable decisions       = 1144
Vocabulary preview      = 851
Review/blocker surfaces = 254

keep-identity    = 849
reuse-identity   = 13
held             = 50
pending          = 192
split-required   = 12
route-expression = 3
source-only      = 25
```

已在 Completion Recheck 中持续保护的代表性边界：

```text
May(月份) / may(情态动词)
like=喜欢 / weather-like construction
square=正方形 / square=广场
left=左边 / left=leave过去式
cook=动词 / cook=名词
cold=寒冷 / cold=感冒
study=学习 / study=书房

danced → dance
cartoons → cartoon
gloves → glove
scissors 保留独立 learning unit
crossroads 保留独立 learning unit
slept / swam / were / won 保持 irregular-form blocker
```

当前仍然：

```text
Stable ThirdPartyID minted = no
Final Klose diff executed  = no
Klose Master / Learner / Publish / Anki modified = no
```

下一步内容工作只针对统一 `review_queue.csv`，不再恢复旧 multi-pass 专项流水线。