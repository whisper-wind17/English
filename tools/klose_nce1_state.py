"""Validate explicit, fingerprint-bound NCE1 identity decisions (never approve)."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from klose_current_policy import unit_fingerprint
BASE = Path(__file__).resolve().parents[1] / "anki/klose"
SOURCE_ID = "new_concept_english_1"
EDITION = "2022-smart-isbn-9787521336702"

def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def source_fingerprint(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def reviewed_state(*, require_allocated=True):
    source = read(BASE / "source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv")
    sources = {f"nce1-o{int(r['CurriculumOrder']):04d}|{r['Entry'].casefold()}": r for r in source}
    registry = {r["NoteID"]: r for name in ("note_registry.csv", "note_registry_extensions.csv") for r in read(BASE / "master" / name)}
    new_rows = read(BASE / "nce1/learner/batch_001_new_notes.csv")
    decisions = read(BASE / "nce1/identity_decisions/batch_001.csv")
    manifest = json.loads((BASE / "nce1/batch_001.json").read_text())
    if manifest.get("Status") != "identity-reviewed" or manifest.get("SourceID") != SOURCE_ID or manifest.get("SourceEdition") != EDITION:
        raise SystemExit("NCE1 reviewed batch identity/status is invalid")
    if len(new_rows) != len({r["NoteID"] for r in new_rows}):
        raise SystemExit("Duplicate NCE1 new identities")
    proposed = {r["NoteID"]: r for r in new_rows}
    for nid, row in proposed.items():
        if row.get("CreatedSource") != SOURCE_ID or row.get("Status") != "active" or row.get("LearnerProfile") != "klose" or row.get("LearnerLevel") != "4":
            raise SystemExit(f"NCE1 new identity/profile drift: {nid}")
        if require_allocated and nid not in registry:
            raise SystemExit(f"NCE1 identity not allocated: {nid}")
        if nid in registry:
            for field in ("CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey", "CreatedSource", "CreatedSourceBook", "Status"):
                if row.get(field) != registry[nid].get(field):
                    raise SystemExit(f"NCE1 allocated identity conflict: {nid}:{field}")
    effective = dict(registry)
    if not require_allocated:
        effective.update(proposed)
    mapped = {}; new_targets = set(); reused = set()
    for row in decisions:
        key, nid = row["SourceItemKey"], row["NoteID"]
        if key in mapped or key not in sources or nid not in effective:
            raise SystemExit(f"NCE1 decision key/target invalid: {key}")
        src = sources[key]; target = effective[nid]
        if row.get("ReviewerType") not in {"model", "human"} or not row.get("ReviewedAt") or not row.get("Reason"):
            raise SystemExit(f"NCE1 decision lacks explicit review evidence: {key}")
        if row.get("SourceFingerprint") != source_fingerprint(src) or row.get("IdentityFingerprint") != unit_fingerprint(target):
            raise SystemExit(f"NCE1 source/identity fingerprint mismatch: {key}")
        if any(row.get(k) != src.get(k) for k in ("CurriculumOrder", "Entry", "PartOfSpeech")) or row.get("SourceMeaning") != src.get("Meaning") or row.get("TargetSense") != target.get("SenseLabel"):
            raise SystemExit(f"NCE1 reviewed meaning/coordinate drift: {key}")
        if not src.get("Meaning") or src.get("SourceStatus") != "verified-actual":
            raise SystemExit(f"This NCE1 batch only authorizes photo-backed target senses: {key}")
        if row["Decision"] in {"new-learning-unit", "new-distinct-sense"}:
            if nid not in proposed: raise SystemExit(f"NCE1 new decision lacks new-note input: {key}")
            new_targets.add(nid)
        elif row["Decision"] in {"reuse-existing", "reuse-spelling-variant"}:
            if nid in proposed: raise SystemExit(f"NCE1 reuse points to new identity: {key}")
            reused.add(nid)
        else:
            raise SystemExit(f"NCE1 unsupported decision: {key}")
        mapped[key] = row
    scope = manifest["Scope"]
    orders = sorted(int(r["CurriculumOrder"]) for r in decisions)
    if orders != list(range(scope["FirstCurriculumOrder"], scope["LastCurriculumOrder"] + 1)):
        raise SystemExit("NCE1 reviewed batch coverage is not closed")
    if len(decisions) != scope["SourceOccurrences"] or len(new_targets) != scope["NewStableNotes"] or len(reused) != scope["ReusedStableNotes"] or new_targets != set(proposed):
        raise SystemExit("NCE1 frozen batch counts/sets drift")
    if require_allocated:
        mappings = [r for r in read(BASE / "master/source_identity_extensions.csv") if r.get("SourceID") == SOURCE_ID]
        actual = {}
        for row in mappings:
            key = row.get("SourceItemKey")
            if key in actual or key not in mapped or row.get("SourceEdition") != EDITION or row.get("Status") != "confirmed" or row.get("NoteID") != mapped[key]["NoteID"] or row.get("Decision") != mapped[key]["Decision"]:
                raise SystemExit(f"Unreviewed/drifted NCE1 source mapping: {key}")
            actual[key] = row
        if set(actual) != set(mapped): raise SystemExit("NCE1 source mapping coverage incomplete")
    return source, mapped, proposed

def validated_mapping_tuples():
    _, decisions, _ = reviewed_state()
    return {(SOURCE_ID, EDITION, k, r["NoteID"]) for k, r in decisions.items()}

if __name__ == "__main__":
    sources, decisions, new = reviewed_state()
    print(f"NCE1 reviewed identity gate PASS: reviewed={len(decisions)} new={len(new)} remaining={len(sources)-len(decisions)}")
