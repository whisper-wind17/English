#!/usr/bin/env python3
"""Synchronize the current third-party vocabulary Stage A progress into NEXT.md."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NEXT = ROOT / "NEXT.md"

SECTION = r'''## 9. Third-party Multi-Edition Vocabulary Corpus — two-stage design + current progress

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
Renjiao morphology candidates  = 6
Renjiao new-surface candidates = 403
Cross-source context reviews   = 392
Semantic-risk queue            = 287
```

当前工程状态：

```text
Renjiao Stage A Valid          = yes
Combined Stage A build         = yes
Cross-source context audit     = yes
Stable ThirdPartyID minted     = no
Final Klose diff executed      = no
Klose Master/Release/Publish/Anki changed = no
```

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
1. 对 392 个北京/人教 exact-surface overlap 做 context-aware sense review；
2. 处理 6 个 morphology candidates；
3. 对人教 403 个 new-surface candidates 做 within-source homograph / sense split 检查；
4. 只有 Identity Resolution 足够稳定后，才开始 mint stable ThirdPartyID；
5. 然后再接入下一个教材 adapter，仍只执行 Stage A。
```
'''


def main() -> None:
    text = NEXT.read_text(encoding="utf-8")
    pattern = re.compile(
        r"## 9\. Third-party Multi-Edition Vocabulary Corpus.*?(?=\n---\n\n## 10\. Frozen long-term rules)",
        flags=re.S,
    )
    if not pattern.search(text):
        raise SystemExit("Cannot locate Third-party section in NEXT.md")
    updated = pattern.sub(SECTION.rstrip(), text)
    if updated != text:
        NEXT.write_text(updated, encoding="utf-8")
        print("NEXT third-party status updated = yes")
    else:
        print("NEXT third-party status updated = no-change")


if __name__ == "__main__":
    main()
