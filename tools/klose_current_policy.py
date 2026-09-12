"""Explicit current admission decisions, independent of historical source intake."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "anki/klose"
DECISIONS = BASE / "learner/admission_decisions.csv"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def unit_fingerprint(row):
    fields = ("NoteID", "CanonicalWord", "SenseLabel", "Status")
    return hashlib.sha256(json.dumps({f: row.get(f, "").strip() for f in fields}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def admission_decisions():
    profile = json.loads((BASE / "config/profile.json").read_text())
    identities = {r["NoteID"]: r for name in ("note_registry.csv", "note_registry_extensions.csv") for r in read_csv(BASE / "master" / name)}
    result = {}
    for row in read_csv(DECISIONS):
        nid = row.get("NoteID", "").strip()
        if row.get("LearnerProfile") != profile["learner_profile"] or row.get("LearnerLevel") != str(profile["learner_level"]):
            raise SystemExit(f"Admission decision profile/level mismatch: {nid}")
        if nid in result or nid not in identities or identities[nid].get("Status") != "active":
            raise SystemExit(f"Invalid/duplicate admission decision: {nid}")
        if row.get("Status") not in {"allowed", "held"} or row.get("ReviewerType") not in {"model", "human"}:
            raise SystemExit(f"Invalid admission decision status/reviewer: {nid}")
        if not row.get("Reason", "").strip() or not row.get("ReviewedAt", "").strip():
            raise SystemExit(f"Admission decision missing evidence: {nid}")
        if row.get("IdentityFingerprint") != unit_fingerprint(identities[nid]):
            raise SystemExit(f"Stale admission decision identity: {nid}")
        target = row.get("PreferredNoteID", "").strip()
        if target:
            if target == nid or target not in identities or identities[target].get("Status") != "active":
                raise SystemExit(f"Invalid preferred learning identity: {nid}->{target}")
            if row.get("PreferredIdentityFingerprint") != unit_fingerprint(identities[target]):
                raise SystemExit(f"Stale preferred learning identity: {nid}->{target}")
            if row["Status"] != "held":
                raise SystemExit(f"A duplicate hold must be held: {nid}")
        result[nid] = row
    return result


def apply_decisions(ordered, states):
    decisions = admission_decisions()
    if set(decisions) - set(ordered):
        raise SystemExit(f"Admission decision outside curriculum: {sorted(set(decisions) - set(ordered))[:10]}")
    allowed = [nid for nid in ordered if decisions.get(nid, {}).get("Status", "allowed") == "allowed"]
    for nid, row in decisions.items():
        target = row.get("PreferredNoteID", "")
        if target and target not in allowed:
            raise SystemExit(f"Duplicate hold lost its admitted survivor: {nid}->{target}")
    return allowed, {nid: states[nid] for nid in allowed}
