#!/usr/bin/env python3
"""Explicitly revalidate unchanged Grade-4 baseline reviews under fingerprint v2.

The 518-note baseline was already fully model-reviewed. Fingerprint v2 widened the
bound fields, so prior approval cannot be silently inherited. This one-time tool
compares current release-visible content with the exact baseline-approved Git
snapshot. Byte-identical Notes are explicitly revalidated; changed/new Notes stay
pending and are emitted as a compact review packet for real model review.
"""
from __future__ import annotations

import csv
import hashlib
import io
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
BASELINE_COMMIT = "fe5612ee7999f8714f31f184d7b8520f01378744"
BASELINE_MANIFEST = BASE / "learner" / "review_approvals" / "grade4-baseline-v1.csv"
OUT_MANIFEST = BASE / "learner" / "review_approvals" / "grade4-baseline-v2-revalidated.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
RELEASE_EXT = BASE / "master" / "release_registry_extensions.csv"
NOTE_EXT = BASE / "master" / "note_registry_extensions.csv"
STATS = BASE / "master" / "build_stats.csv"
PACKET = BASE / "review" / "grade4-v2-pending.csv"

MASTER_FIELDS = ["CanonicalWord", "SenseLabel", "Word", "British", "American", "MeaningPrimary"]
LEARNER_FIELDS = ["ExampleSentence", "ExampleTranslation", "LearnerProfile", "LearnerLevel"]
REGISTRY_FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "ContentFingerprint",
    "ReviewStatus", "ReviewedAt", "ReviewerType", "ReviewNote",
]
APPROVAL_FIELDS = [
    "BatchID", "LearnerProfile", "LearnerLevel", "NoteID", "ContentFingerprint",
    "ReviewStatus", "ReviewedAt", "ReviewerType", "ReviewNote",
]
PACKET_FIELDS = [
    "Category", "LearningStatus", "NoteID", "CanonicalWord", "SenseLabel", "Word",
    "British", "American", "MeaningPrimary", "ExampleSentence", "ExampleTranslation", "SourceBooks",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git_csv(commit: str, relpath: str) -> list[dict[str, str]]:
    raw = subprocess.check_output(["git", "show", f"{commit}:{relpath}"], cwd=ROOT)
    text = raw.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def fingerprint(master: dict[str, str], learner: dict[str, str]) -> str:
    payload = "\x1f".join([
        "klose-presentation-v2",
        master.get("CanonicalWord", "").strip(),
        master.get("SenseLabel", "").strip(),
        master.get("Word", "").strip(),
        master.get("British", "").strip(),
        master.get("American", "").strip(),
        master.get("MeaningPrimary", "").strip(),
        learner.get("ExampleSentence", "").strip(),
        learner.get("ExampleTranslation", "").strip(),
        learner.get("LearnerProfile", "").strip(),
        learner.get("LearnerLevel", "").strip(),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def same_content(cur_m: dict[str, str], old_m: dict[str, str], cur_l: dict[str, str], old_l: dict[str, str]) -> bool:
    return all(cur_m.get(f, "").strip() == old_m.get(f, "").strip() for f in MASTER_FIELDS) and all(
        cur_l.get(f, "").strip() == old_l.get(f, "").strip() for f in LEARNER_FIELDS
    )


def upsert_metric(rows: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in rows:
        if row.get("Metric") == metric:
            row["Value"] = str(value)
            return
    rows.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    required = (BASELINE_MANIFEST, MASTER, LEARNER, REGISTRY, ADMISSION, RELEASE_EXT, NOTE_EXT, STATS)
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing v2 revalidation input: {path.relative_to(ROOT)}")

    baseline_ids = {r["NoteID"].strip() for r in read_csv(BASELINE_MANIFEST)}
    if len(baseline_ids) != 518:
        raise SystemExit(f"Expected 518 baseline-approved Notes, found {len(baseline_ids)}")

    old_master = {r["NoteID"].strip(): r for r in git_csv(BASELINE_COMMIT, "anki/klose/master/vocabulary_master.csv")}
    old_learner = {r["NoteID"].strip(): r for r in git_csv(BASELINE_COMMIT, "anki/klose/learner/current.csv")}
    cur_master = {r["NoteID"].strip(): r for r in read_csv(MASTER)}
    cur_learner = {r["NoteID"].strip(): r for r in read_csv(LEARNER)}
    registry_rows = read_csv(REGISTRY)
    registry = {(r["LearnerProfile"], r["LearnerLevel"], r["NoteID"]): r for r in registry_rows}
    admission = {r["NoteID"].strip(): r for r in read_csv(ADMISSION)}
    release_ext = {r["NoteID"].strip() for r in read_csv(RELEASE_EXT)}
    new_ids = {r["NoteID"].strip() for r in read_csv(NOTE_EXT)}

    eligible: list[str] = []
    for nid in sorted(baseline_ids):
        if nid not in cur_master or nid not in cur_learner or nid not in old_master or nid not in old_learner:
            continue
        if cur_master[nid].get("Released") != "yes":
            continue
        if same_content(cur_master[nid], old_master[nid], cur_learner[nid], old_learner[nid]):
            eligible.append(nid)

    reviewed_at = date.today().isoformat()
    note = f"Explicit fingerprint-v2 revalidation: release-visible content unchanged from fully model-reviewed baseline commit {BASELINE_COMMIT}"
    batch_id = "grade4-baseline-v2-revalidated"

    if not OUT_MANIFEST.exists():
        manifest_rows: list[dict[str, str]] = []
        for nid in eligible:
            fp = fingerprint(cur_master[nid], cur_learner[nid])
            manifest_rows.append({
                "BatchID": batch_id,
                "LearnerProfile": "klose",
                "LearnerLevel": "4",
                "NoteID": nid,
                "ContentFingerprint": fp,
                "ReviewStatus": "model-reviewed",
                "ReviewedAt": reviewed_at,
                "ReviewerType": "model",
                "ReviewNote": note,
            })
        write_csv(OUT_MANIFEST, APPROVAL_FIELDS, manifest_rows)
    manifest = {r["NoteID"].strip(): r for r in read_csv(OUT_MANIFEST)}

    revalidated = 0
    for nid in eligible:
        key = ("klose", "4", nid)
        row = registry.get(key)
        approved = manifest.get(nid)
        if row is None or approved is None:
            raise SystemExit(f"Missing current registry/approval row for revalidated Note: {nid}")
        current_fp = fingerprint(cur_master[nid], cur_learner[nid])
        if approved.get("ContentFingerprint", "") != current_fp:
            raise SystemExit(f"Immutable v2 revalidation manifest is stale for {nid}")
        if row.get("ContentFingerprint", "") != current_fp:
            raise SystemExit(f"Current review registry fingerprint mismatch for {nid}")
        row["ReviewStatus"] = "model-reviewed"
        row["ReviewedAt"] = approved["ReviewedAt"]
        row["ReviewerType"] = "model"
        row["ReviewNote"] = approved["ReviewNote"]
        revalidated += 1

    current_ids = sorted(
        nid for nid, m in cur_master.items()
        if m.get("Released") == "yes" and nid in cur_learner
        and cur_learner[nid].get("LearnerProfile") == "klose"
        and cur_learner[nid].get("LearnerLevel") == "4"
    )
    pending_ids = [nid for nid in current_ids if registry[("klose", "4", nid)].get("ReviewStatus") == "pending"]

    packet: list[dict[str, str]] = []
    for nid in pending_ids:
        if nid in new_ids:
            category = "actual-grade4-new-identity"
        elif nid in release_ext:
            category = "actual-grade4-new-release-existing-identity"
        elif nid in baseline_ids:
            category = "baseline-changed-since-v1"
        else:
            category = "other-current-pending"
        m = cur_master[nid]
        l = cur_learner[nid]
        packet.append({
            "Category": category,
            "LearningStatus": admission.get(nid, {}).get("Status", ""),
            "NoteID": nid,
            "CanonicalWord": m.get("CanonicalWord", ""),
            "SenseLabel": m.get("SenseLabel", ""),
            "Word": m.get("Word", ""),
            "British": m.get("British", ""),
            "American": m.get("American", ""),
            "MeaningPrimary": m.get("MeaningPrimary", ""),
            "ExampleSentence": l.get("ExampleSentence", ""),
            "ExampleTranslation": l.get("ExampleTranslation", ""),
            "SourceBooks": m.get("SourceBooks", ""),
        })

    registry_rows.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, REGISTRY_FIELDS, registry_rows)
    write_csv(PACKET, PACKET_FIELDS, packet)

    current_rows = [registry[("klose", "4", nid)] for nid in current_ids]
    model_count = sum(r["ReviewStatus"] == "model-reviewed" for r in current_rows)
    human_count = sum(r["ReviewStatus"] == "human-reviewed" for r in current_rows)
    pending_count = sum(r["ReviewStatus"] == "pending" for r in current_rows)
    stats = read_csv(STATS)
    upsert_metric(stats, "learner_review_registry_current", len(current_rows))
    upsert_metric(stats, "learner_model_reviewed_current", model_count)
    upsert_metric(stats, "learner_human_reviewed_current", human_count)
    upsert_metric(stats, "learner_review_pending_current", pending_count)
    upsert_metric(stats, "learner_baseline_v2_revalidated", revalidated)
    write_csv(STATS, ["Metric", "Value"], stats)

    categories: dict[str, int] = {}
    for row in packet:
        categories[row["Category"]] = categories.get(row["Category"], 0) + 1
    print(
        f"Baseline v2 revalidation: baseline=518 revalidated={revalidated} "
        f"current={len(current_ids)} pending={pending_count} categories={categories}"
    )


if __name__ == "__main__":
    main()
