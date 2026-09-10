#!/usr/bin/env python3
"""Attach current Source provenance state to Grade 5–6 reconciliation status.

The semantic CandidateFingerprint remains unchanged. This adds a separate provenance
fingerprint and allocation blocker so provenance corrections do not force false
semantic re-review while stale source binding remains machine-detectable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from grade5_6_source_state import source_provenance_state

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "anki" / "klose" / "review" / "grade5_6_reconciliation"
TARGETS = {
    "vocabulary": DIR / "vocabulary_status.json",
    "expression": DIR / "expression_status.json",
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        raise SystemExit("Usage: sync_grade5_6_reconciliation_provenance.py vocabulary|expression")
    lane = sys.argv[1]
    path = TARGETS[lane]
    if not path.exists():
        raise SystemExit(f"Missing reconciliation status: {path.relative_to(ROOT)}")
    status = json.loads(path.read_text(encoding="utf-8"))
    prov = source_provenance_state()
    status.update({
        "SourceIdentityPending": prov["SourceIdentityPending"],
        "SourceProvenanceFingerprint": prov["SourceProvenanceFingerprint"],
        "SourceProvenanceRows": prov["SourceProvenanceRows"],
        "SourceProvenanceBlockers": prov["SourceProvenanceBlockers"],
        "SourceProvenanceResolutionState": prov["ResolutionState"],
        "CanonicalSourceID": prov["CanonicalSourceID"],
        "StableIDAllocationAllowed": prov["StableIDAllocationAllowed"],
    })
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Synced {lane} provenance: pending={prov['SourceIdentityPending']}, "
        f"fingerprint={prov['SourceProvenanceFingerprint']}, "
        f"blockers={len(prov['SourceProvenanceBlockers'])}, allocation={prov['StableIDAllocationAllowed']}"
    )


if __name__ == "__main__":
    main()
