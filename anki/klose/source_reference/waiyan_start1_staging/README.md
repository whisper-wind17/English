# Waiyan Start1 — Third-party Source Adapter

Scope:

```text
外研版一年级起点 1-6 年级上下册 = 12 primary-school books
```

The start-from-grade-3 primary family and middle/high-school XLSX files in the
same raw directory are explicitly excluded.

Expected source schema:

```text
A 单词 | B 英音 | C 美音 | D 释义
```

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 12
Source occurrences = 1170
Distinct MatchKeys = 1071
```

No cross-source identity state and no Klose final-diff state are stored here.
