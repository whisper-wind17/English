# Guangzhou Start3 — Third-party Source Adapter

Scope:

```text
广州版三年级起点 3-6 年级上下册 = 8 primary-school books
```

Source schema is anchored by the `单词` and `释义` header columns. `英音` / `美音`
are preserved when present.

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 8
Source occurrences = 1268
Distinct MatchKeys = 1212
Blank definitions  = 1
```

No cross-source identity state and no Klose final-diff state are stored here.
