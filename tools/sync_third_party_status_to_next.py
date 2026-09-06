#!/usr/bin/env python3
"""Synchronize the current third-party vocabulary Stage A progress into NEXT.md."""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXT = ROOT / "NEXT.md"
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
RESOLUTION = STAGING / "cross_source_identity_resolution.csv"
MORPH = BASE / "third_party_vocabulary" / "review" / "renjiao_start1_morphology_resolution.csv"
NEW_SURFACE = BASE / "source_reference" / "renjiao_start1_staging" / "new_surface_candidates.csv"
RISK = STAGING / "cross_source_semantic_risk_queue.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    resolution = read_csv(RESOLUTION)
    morph = read_csv(MORPH)
    new_surface = read_csv(NEW_SURFACE)
    risk = read_csv(RISK)

    statuses = Counter(r["ResolutionStatus"] for r in resolution)
    decisions = Counter(r["ProposedDecision"] for r in resolution)
    morph_held = sum(r["ProposedDecision"].startswith("held-") for r in morph)
    morph_resolved = len(morph) - morph_held

    section = f'''## 9. Third-party Multi-Edition Vocabulary Corpus — two-stage design + current progress

2026-09-06 用户确认长期目标：北京版只是第一个 seed，后续把人教版、沪教版及其他第三方小学教材词表持续累加到同一个统一第三方 corpus，按 learning unit / target sense 做 sense-aware 去重。

长期设计：

```text
docs/THIRD_PARTY_VOCABULARY_CORPUS.md
```

两阶段流程冻结为：

```text
Stage A — 第三方内部

多个第三方教材 Raw Vocabulary
→ Source Adapters
→ 与 Third-party Unified Vocabulary 做 sense-aware 去重
→ 完整 Third-party Unified Vocabulary

Stage B — 所有第三方来源完成后

完整 Third-party Unified Vocabulary
→ 与 Klose Full Stable Identity Registry 做一次最终 sense-aware diff
→ Third-party New Vocabulary Pool
→ 后续全部作为 Klose 当前教材之外的新词学习
```

当前已接入两个独立 Source Adapter：

```text
Adapter #1  beijing_start1
Source books             = 12
Source occurrences       = 808
Distinct MatchKeys       = 734

Adapter #2  renjiao_start1
Source books             = 12
Source occurrences       = 908
Distinct MatchKeys       = 802
```

人教版目录同时存在“一年级起点”和“三年级起点”；当前只接入 `renjiao_start1`。三年级起点未来作为独立 adapter，不能静默混入一年级起点。

北京 + 人教一年级起点当前联合 Stage A 工作区：

```text
anki/klose/third_party_vocabulary/staging/

Total source occurrences       = 1716
Distinct normalized MatchKeys  = 1144
Cross-source exact overlaps    = 392
Single-source surfaces         = 752
Renjiao morphology candidates  = {len(morph)}
Renjiao new-surface candidates = {len(new_surface)}
Cross-source context reviews   = {len(resolution)}
Semantic-risk queue            = {len(risk)}
```

Cross-source exact-overlap 第一轮 Identity Resolution：

```text
rule-reviewed reuse             = {statuses.get('rule-reviewed', 0)}
model-reviewed rows             = {statuses.get('model-reviewed', 0)}
pending semantic review         = {statuses.get('pending', 0)}

reuse-learning-unit             = {decisions.get('reuse-learning-unit', 0)}
partial-overlap-split-required  = {decisions.get('partial-overlap-split-required', 0)}
do-not-merge                    = {decisions.get('do-not-merge', 0)}
held / policy-context blocker   = {sum(v for k, v in decisions.items() if k.startswith('held-'))}

morphology resolved             = {morph_resolved}
morphology held                 = {morph_held}
```

当前已显式保护的 semantic collision 包括：

```text
May(月份) vs may(情态动词)
like=喜欢 vs weather ... like ...
square=正方形 vs square=广场
left=左边 vs left=leave过去式
cook=烹饪/煮 vs cook=厨师
cold=寒冷 vs cold=感冒
study=学习 vs study=书房
```

当前工程状态：

```text
Renjiao Stage A Valid          = yes
Combined Stage A build         = yes
Cross-source context audit     = yes
First-pass Identity Resolution = yes
Completion Recheck             = pass
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
Klose Master/Release/Publish/Anki changed = no
```

这里的 `rule-reviewed`、`model-reviewed`、`pending` 必须保持区分；第一轮 Resolution 不等于全部 392 个 overlap 已经 source-confirmed。只有明确无风险信号或已有显式语义判断的行才向前推进，其余继续 pending。

重要约束继续有效：

- 北京版只有 seed 身份，没有语义优先级；
- 第二个及后续教材在 Stage A **只和第三方 Unified Vocabulary 去重**，不因 Klose 当前已有同词而删除第三方 Identity；
- 在所有计划中的第三方来源处理完成前，不生成最终 `existing-in-klose / third-party-new` 结论；
- 早期与 Klose 的比较可以保留为 diagnostic / candidate evidence，但不能作为第三方 corpus 删除依据；
- 去重单位是 `learning unit / target sense`，不是字符串；
- 同 surface 不同义项必须允许多个第三方 Identity；
- morphology / phrase / punctuation 只产生 candidate，不自动 merge；
- 教材版本、最早年级、覆盖教材数、出现次数、年级分布都不作为学习决策维度；
- provenance 只在 raw / Source Occurrence 层保留用于回溯，不进入正常学习界面；
- 第三方统一 corpus 永远低于 Klose 实际教材 Source Truth 优先级。

当前下一步：

```text
1. 继续处理剩余 {statuses.get('pending', 0)} 个 cross-source semantic-risk pending rows；
2. 对人教 {len(new_surface)} 个 new-surface candidates 做 within-source homograph / sense-split audit；
3. 复核两类 blocker 后，再判断是否已经足够稳定到可以 mint 第一版 Stable ThirdPartyID；
4. 在此之前不执行 Klose Stage-B final diff；
5. 每个阶段完成后必须执行独立 Completion Recheck。
```
'''

    text = NEXT.read_text(encoding="utf-8")
    pattern = re.compile(
        r"## 9\. Third-party Multi-Edition Vocabulary Corpus.*?(?=\n---\n\n## 10\. Frozen long-term rules)",
        flags=re.S,
    )
    if not pattern.search(text):
        raise SystemExit("Cannot locate Third-party section in NEXT.md")
    updated = pattern.sub(section.rstrip(), text)
    if updated != text:
        NEXT.write_text(updated, encoding="utf-8")
        print("NEXT third-party status updated = yes")
    else:
        print("NEXT third-party status updated = no-change")


if __name__ == "__main__":
    main()
