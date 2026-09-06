# Third-party Vocabulary — Simplified Stage A

Active pipeline:

```text
standardized source occurrences
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ surface_candidates.csv
→ review_queue.csv
→ unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

Current facts:

```text
Source occurrences       = 1716
Normalized surfaces      = 1144
Reviewed identity preview = 851
Review/blocker surfaces  = 254
```

Candidate signals (exact / morphology / format / multiword / punctuation) are
only evidence. They do not create extra processing stages and never equal
Identity truth.

`identity_decisions.csv` is the single durable content-decision truth for this
third-party corpus. Legacy audit/resolution CSVs remain only as migration/audit
history and are no longer part of the active long-term pipeline.

Stable ThirdPartyID is not minted yet. Final Klose diff is not executed in Stage A.
