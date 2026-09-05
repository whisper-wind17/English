# 四年级上：Klose 实际教材 vs 当前 rj_start1 数据

状态：**BLOCKED FOR SOURCE RECONCILIATION**

本文件记录 2026-09-05 发现的教材版本冲突。完成 reconciliation 前，不把当前第三方 `rj_start1::4年级上` 继续当作 Klose 手中教材的准确 Source Fact。

## 1. Klose 实际教材基准

Core Vocabulary：

```text
rj_start1-grade4-upper-klose-actual.csv
6 Units
110 occurrence rows
109 unique surface entries
```

Useful Expressions：

```text
rj_start1-grade4-upper-klose-expressions.csv
41 source-expression rows
```

Pattern Candidates：

```text
rj_start1-grade4-upper-pattern-candidates.csv
```

这些文件来自 Klose 手中实际《四年级上》教材照片，优先作为当前 reconciliation 的实物证据。

## 2. 已确认的版本冲突

当前 repo 第三方 `人教版一年级起点四年级上.xlsx` 的主题从 `running / basketball / roller skating / jumping rope / ...` 开始，并包含交通、文具、安全等主题；Klose 实际四上教材的 6 个 Unit 则是职业/家务、人物特征、社区场所、职业、天气、衣物与季节。

因此不是少量漏词，而是 **教材词表版本不一致**。

按 exact surface + 当前 `SourceBook=4年级上` 做第一轮交叉检查，Klose 实际 110 条 occurrence 中只有 17 条 occurrence 直接命中当前四上 SourceWord；因为 `cook` 在实际教材出现两次，所以是 16 个 unique surface：

```text
job
doctor
farmer
nurse
cook
people
basketball
always
park
shop
police officer
film
fun
their
swim
snow
```

这只代表“当前四上 source 中 exact surface 命中”，不代表其 target sense 已经正确，也不代表未命中的词不在 Master 其他年级中。

## 3. Master 中大量词已存在，但 provenance 错位

实际四上中的不少词已经在当前 Master 里出现，只是当前第三方来源把它们放在其他年级。例如：

```text
PE          -> 当前来源在 3年级下
hair        -> 3年级上
Chinese     -> 3年级下
playground  -> 3年级下
library     -> 3年级下
weather     -> 2年级下
sunny       -> 2年级下
hot         -> 2年级下
cold        -> 2年级下
windy       -> 2年级下
cloudy      -> 2年级下
rainy       -> 2年级下
snowy       -> 2年级下
sweater     -> 3年级上
wear        -> 3年级上
coat        -> 3年级上
```

这些通常不是新 Note，而是需要新增/修正 Klose 实际教材 provenance。

## 4. 不能做字符串级自动合并的项目

以下类型必须进入 identity/sense reconciliation：

```text
office worker   vs worker
factory worker  vs worker
bus stop        vs stop
driver          vs bus driver / taxi driver
delivery worker vs worker
football        vs play football
sport           vs play sports
fly             vs fly a kite
kite            vs fly a kite
snowman         vs make a snowman
sock            vs socks
glove           vs gloves
leaf            vs maple leaves
child           vs children
read            vs read books / reading
play            vs play with / play football / ...
```

MatchKey/包含关系只能产生 candidate，不能自动认定同一 learning unit。

## 5. 已确认的 identity blocker：cook

Klose 实际教材明确给出两个 target sense：

```text
Unit 1 cook = 烹饪；煮       # verb
Unit 4 cook = 厨师           # noun
```

当前 released `KV000424` 却把 MeaningPrimary 合并成：

```text
厨师；做饭
```

且例句是 noun sense。

这违反本项目“一 Note = 一个明确 learning unit / target sense”的规则。正确迁移方向应是：

```text
保留 KV000424 -> cook (noun: 厨师)
新增 NoteID   -> cook (verb: 烹饪；煮)
```

因为 Klose 尚未开始正式 Review，目前是修复 identity 的低风险窗口，但仍必须按显式 migration 处理，不能重编号既有 NoteID。

## 6. 对当前 Anki Baseline 的影响

当前 AnkiWeb 已有：

```text
518 Cards
343 Suspended
175 Unsuspended
```

但其中 `stage::grade4-new` 是基于版本不匹配的第三方四年级来源生成的。因此在重新 staging 前：

> **不要让 Klose 开始正式学习。**

一旦开始产生真实 Review History，后续清理错误 source scope 会更复杂。

现阶段保护原则：

```text
不删除/重编号已有 NoteID
不手改 publish CSV
不让错误的 175 active cards 开始形成 FSRS history
先完成实际四上 reconciliation
再从上游重建正确的 released/stage 集合
最后重新导入同一 Note Type
```

## 7. Useful Expressions 的处理

教材原句 100% 保存为 Source Fact；不会机械地一条原句对应一张 Anki Card。

Expression 与 Vocabulary 分开：

```text
Vocabulary  -> word / phrase / target sense
Expression  -> communicative pattern / reusable structure
```

已抽取的 pattern candidate 例如：

```text
What's [person]'s job?
There is / There are ...
What's the weather like in [place]?
Whose [noun] is this?
Can I [verb phrase]?
Which [category] do you like?
```

未来若发布 Expressions，建议使用独立 Note Type / 学习目标；当前先不制卡。

## 8. 下一步完成条件

四年级上只有满足以下条件才算 reconciliation 完成：

```text
[ ] 110 条 Core Vocabulary occurrence 全部得到 identity 决策
[ ] 现有 exact Note -> 复用 NoteID + 增加实际教材 provenance
[ ] phrase/morphology 候选逐条做 sense-aware 决策
[ ] 真正新 learning unit -> append 新 NoteID
[ ] cook noun/verb 完成显式 split migration
[ ] LearnerLevel 仍固定为 4
[ ] 新增/变化的 Meaning / Example / Translation 重新 review
[ ] 当前 175 active cards 重新 staging
[ ] release gate 通过
[ ] 再生成并导入 anki-import.csv
```

在这些条件完成前，不开始 Grade 5/6 release，也不让 Klose 在当前 175 张 active cards 上产生正式学习历史。
