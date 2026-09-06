# Renjiao Start1 — Third-party Source Adapter

Active output:

```text
occurrences.csv
```

The adapter only captures source facts. Cross-source comparison, morphology,
semantic resolution, Vocabulary/Expression routing, and corpus identity logic
are handled centrally by `tools/build_third_party_corpus.py`.

```text
Source books       = 12
Source occurrences = 908
Distinct MatchKeys = 802
```

Other older CSVs in this directory are legacy migration/audit history and are
not inputs to the active simplified Stage-A pipeline.
