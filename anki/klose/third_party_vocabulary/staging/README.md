# Third-party Vocabulary — Simplified Stage A

Active data flow:

```text
config/source_adapters.csv
+ standardized adapter occurrences
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ surface_candidates.csv
→ review_queue.csv
→ unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

```text
Enabled adapters          = 5
Source occurrences        = 4848
Normalized surfaces       = 2062
Vocabulary preview        = 1586
Review/blocker surfaces   = 285
Evidence-changed surfaces = 0
```

Each durable decision is bound to the exact Source Occurrences it reviewed via an
unambiguous JSON array in `OccurrenceKeys`. Additional source evidence automatically
re-queues that MatchKey. Candidate signals are evidence only. Canonical blockers cannot
be bypassed by reuse aliases, and canonical learner-facing TargetSense always comes from
the reviewed canonical surface when it exists. Stable ThirdPartyID is not minted and
Stage-B Klose diff is not executed here.
