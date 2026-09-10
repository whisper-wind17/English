#!/usr/bin/env python3
"""One-shot patch for Vocabulary current-curriculum release/review semantics.

This file is intentionally removed by its workflow after applying the patch.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "tools" / "check_klose_release_ready.py"
SYNC = ROOT / "tools" / "sync_klose_learner_review_registry.py"
APPROVE = ROOT / "tools" / "approve_klose_learner_review.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"Patch anchor not found: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"Patch anchor not unique: {label} count={text.count(old)}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, new_block: str, label: str) -> str:
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"Patch start not found: {label}")
    j = text.find(end, i)
    if j < 0:
        raise SystemExit(f"Patch end not found: {label}")
    return text[:i] + new_block.rstrip() + "\n\n" + text[j:]


def patch_release() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'SOURCE_IDENTITY_EXTENSIONS = BASE / "master" / "source_identity_extensions.csv"\n',
        'SOURCE_IDENTITY_EXTENSIONS = BASE / "master" / "source_identity_extensions.csv"\nG56_SCOPE = BASE / "learner" / "grade5_6_learning_scope.json"\n',
        "release G56 scope path",
    )
    text = replace_once(
        text,
        'CURRENT_LEARNING_TAG = "learning::klose::grade4"\nCURRENT_STAGE = "stage::grade4-current"\nHELD_STAGE = "stage::library"\nGRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\\d+)-o(\\d+)\\|")\nSEMESTER_RANK = {"upper": 0, "lower": 1}\n',
        'GRADE4_LEARNING_TAG = "learning::klose::grade4"\nGRADE4_STAGE = "stage::grade4-current"\nG56_LEARNING_TAG = "learning::klose::grade5-6"\nG56_STAGE = "stage::grade5-6-current"\nHELD_STAGE = "stage::library"\nGRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\\d+)-o(\\d+)\\|")\nG56_KEY_RE = re.compile(r"^grade([56])-(upper|lower)-u(\\d+)-o(\\d+)\\|")\nSEMESTER_RANK = {"upper": 0, "lower": 1}\n',
        "release stage constants",
    )

    curriculum_fn = r'''def current_curriculum_ordered_note_ids() -> tuple[list[str], dict[str, tuple[str, str]]]:
    """Independently derive current curriculum order and expected stage/tag.

    Grade-4 current source remains first. Accepted Grade-5/6 source follows in
    textbook order. A Stable Note recurring in multiple books appears once at its
    earliest accepted occurrence. If a Note is already in Grade-4 current, the
    Grade-4 stage/tag wins even when it recurs in Grade 5/6.
    """
    scope = json.loads(G56_SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        raise SystemExit("Release blocked: Grade 5-6 current learning scope is not accepted")
    accepted_books = {k for k, v in scope.get("Books", {}).items() if v.get("Accepted") is True}
    if accepted_books != {"5上", "5下", "6上", "6下"}:
        raise SystemExit(f"Release blocked: Grade 5-6 current scope is incomplete: {sorted(accepted_books)}")

    first_coord: dict[str, tuple[int, int, int, int, int]] = {}
    expected_state: dict[str, tuple[str, str]] = {}
    seen_coordinates: set[tuple[int, int, int, int]] = set()
    for row in read_csv(SOURCE_IDENTITY_EXTENSIONS):
        if row.get("Status", "").strip() != "confirmed":
            continue
        key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        if not nid:
            raise SystemExit("Release blocked: confirmed source identity has blank NoteID")

        m4 = GRADE4_KEY_RE.match(key)
        if (
            m4 is not None
            and row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
        ):
            semester, unit_text, order_text = m4.groups()
            coordinate = (4, SEMESTER_RANK[semester], int(unit_text), int(order_text))
            if coordinate in seen_coordinates:
                raise SystemExit(f"Release blocked: duplicate current curriculum coordinate: {coordinate}")
            seen_coordinates.add(coordinate)
            full_coord = (*coordinate, int(nid[2:]))
            first_coord[nid] = min(first_coord.get(nid, full_coord), full_coord)
            expected_state[nid] = (GRADE4_STAGE, GRADE4_LEARNING_TAG)
            continue

        m56 = G56_KEY_RE.match(key)
        if m56 is None:
            continue
        grade_text, semester, unit_text, order_text = m56.groups()
        book = grade_text + ("上" if semester == "upper" else "下")
        if book not in accepted_books:
            continue
        coordinate = (int(grade_text), SEMESTER_RANK[semester], int(unit_text), int(order_text))
        if coordinate in seen_coordinates:
            raise SystemExit(f"Release blocked: duplicate current curriculum coordinate: {coordinate}")
        seen_coordinates.add(coordinate)
        full_coord = (*coordinate, int(nid[2:]))
        first_coord[nid] = min(first_coord.get(nid, full_coord), full_coord)
        expected_state.setdefault(nid, (G56_STAGE, G56_LEARNING_TAG))

    if not first_coord:
        raise SystemExit("Release blocked: current curriculum identity set is empty")
    ordered = [nid for nid, _ in sorted(first_coord.items(), key=lambda item: item[1])]
    return ordered, expected_state'''
    text = replace_between(
        text,
        "def actual_grade4_ordered_note_ids()",
        "def load_and_validate_admission(",
        curriculum_fn,
        "release curriculum function",
    )

    admission_fn = r'''def load_and_validate_admission(
    learner_profile: str,
    learner_level: str,
    released_ids: set[str],
) -> dict[str, dict[str, str]]:
    rows = [
        r for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == learner_profile
        and r.get("LearnerLevel", "").strip() == learner_level
    ]
    if not rows:
        raise SystemExit("Release blocked: explicit learning admission is empty")

    expected_ordered, expected_state = current_curriculum_ordered_note_ids()
    expected_allowed = set(expected_ordered)
    expected_universe = released_ids | expected_allowed

    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        nid = row.get("NoteID", "").strip()
        status = row.get("Status", "").strip()
        stage = row.get("Stage", "").strip()
        tag = row.get("LearningTag", "").strip()
        learning_order = row.get("LearningOrder", "").strip()
        if not nid or nid in by_id:
            raise SystemExit(f"Release blocked: invalid/duplicate learning admission NoteID: {nid!r}")
        if status not in {"allowed", "held"}:
            raise SystemExit(f"Release blocked: invalid learning admission status: {nid}={status!r}")
        if status == "allowed":
            expected = expected_state.get(nid)
            if expected is None:
                raise SystemExit(f"Release blocked: allowed Note is outside current curriculum: {nid}")
            expected_stage, expected_tag = expected
            if stage != expected_stage or tag != expected_tag:
                raise SystemExit(
                    "Release blocked: current learning Note has wrong stage/tag: "
                    f"{nid} stage={stage!r}->{expected_stage!r} tag={tag!r}->{expected_tag!r}"
                )
            if not is_valid_learning_order(learning_order):
                raise SystemExit(
                    f"Release blocked: allowed Note has invalid six-digit LearningOrder: {nid}={learning_order!r}"
                )
        else:
            if nid in expected_allowed:
                raise SystemExit(f"Release blocked: current curriculum Note cannot be held: {nid}")
            if stage != HELD_STAGE or tag:
                raise SystemExit(
                    f"Release blocked: held Note has wrong stage/tag: {nid} stage={stage!r} tag={tag!r}"
                )
            if learning_order:
                raise SystemExit(f"Release blocked: held Note must have blank LearningOrder: {nid}={learning_order!r}")
        by_id[nid] = row

    ids = set(by_id)
    missing = sorted(expected_universe - ids)
    extra = sorted(ids - expected_universe)
    if missing or extra:
        raise SystemExit(
            "Release blocked: explicit learning admission must cover released library union current curriculum; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    allowed = {nid for nid, row in by_id.items() if row.get("Status", "").strip() == "allowed"}
    if allowed != expected_allowed:
        missing = sorted(expected_allowed - allowed)
        extra = sorted(allowed - expected_allowed)
        raise SystemExit(
            "Release blocked: allowed learning set does not equal current curriculum identity set; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    try:
        expected_order = {
            nid: format_learning_order(index)
            for index, nid in enumerate(expected_ordered, start=1)
        }
    except ValueError as exc:
        raise SystemExit(f"Release blocked: {exc}") from exc
    bad_order = [
        f"{nid}:{by_id[nid].get('LearningOrder', '')}->{expected}"
        for nid, expected in expected_order.items()
        if by_id[nid].get("LearningOrder", "").strip() != expected
    ]
    if bad_order:
        raise SystemExit(
            "Release blocked: LearningOrder does not match current textbook curriculum order; "
            f"count={len(bad_order)} examples={bad_order[:10]}"
        )
    return by_id'''
    text = replace_between(
        text,
        "def load_and_validate_admission(",
        "def main() -> None:",
        admission_fn,
        "release admission function",
    )
    text = replace_once(
        text,
        "        SOURCE_IDENTITY_EXTENSIONS, STUDY, ANKI_IMPORT, *REPORTS,\n",
        "        SOURCE_IDENTITY_EXTENSIONS, G56_SCOPE, STUDY, ANKI_IMPORT, *REPORTS,\n",
        "release required inputs",
    )
    RELEASE.write_text(text, encoding="utf-8")


def patch_sync() -> None:
    text = SYNC.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'REGISTRY = BASE / "learner" / "presentation_review_registry.csv"\n',
        'REGISTRY = BASE / "learner" / "presentation_review_registry.csv"\nADMISSION = BASE / "learner" / "learning_admission.csv"\n',
        "sync admission path",
    )
    new_main = r'''def main() -> None:
    learner = read_csv(LEARNER)
    master = read_csv(MASTER)
    master_by_id = {r["NoteID"]: r for r in master}
    released = {r["NoteID"] for r in master if r.get("Released") == "yes"}
    learner_by_id = {r["NoteID"]: r for r in learner}
    if released - set(learner_by_id):
        raise SystemExit("Released notes are missing learner presentations")
    if not ADMISSION.exists():
        raise SystemExit("Learning admission is required before review-registry sync")

    review_keys: set[tuple[str, str, str]] = set()
    for nid in released:
        cur = learner_by_id[nid]
        review_keys.add((cur["LearnerProfile"], cur["LearnerLevel"], nid))

    allowed_count = 0
    for row in read_csv(ADMISSION):
        if row.get("Status", "").strip() != "allowed":
            continue
        allowed_count += 1
        nid = row.get("NoteID", "").strip()
        profile = row.get("LearnerProfile", "").strip()
        level = row.get("LearnerLevel", "").strip()
        if nid not in master_by_id or nid not in learner_by_id:
            raise SystemExit(f"Allowed learning admission lacks Master/Learner row: {nid}")
        cur = learner_by_id[nid]
        if cur.get("LearnerProfile", "").strip() != profile or cur.get("LearnerLevel", "").strip() != level:
            raise SystemExit(f"Allowed admission profile/level mismatch for {nid}")
        review_keys.add((profile, level, nid))

    existing = read_csv(REGISTRY) if REGISTRY.exists() else []
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in existing:
        key = (row["LearnerProfile"], row["LearnerLevel"], row["NoteID"])
        if key in by_key:
            raise SystemExit(f"Duplicate learner review registry key: {key}")
        if row.get("ReviewStatus", "") not in VALID_STATUSES:
            raise SystemExit(f"Invalid ReviewStatus in learner review registry: {row}")
        by_key[key] = row

    added = 0
    invalidated = 0
    missing_fingerprint_invalidated = 0
    for profile, level, nid in sorted(review_keys, key=lambda k: (k[0], int(k[1]), k[2])):
        cur = learner_by_id[nid]
        current_fp = fingerprint(master_by_id[nid], cur)
        key = (profile, level, nid)
        if key not in by_key:
            row = {
                "LearnerProfile": profile,
                "LearnerLevel": level,
                "NoteID": nid,
                "ContentFingerprint": current_fp,
                "ReviewStatus": "pending",
                "ReviewedAt": "",
                "ReviewerType": "",
                "ReviewNote": "awaiting explicit learner-level review before release",
            }
            existing.append(row)
            by_key[key] = row
            added += 1
            continue

        row = by_key[key]
        old_fp = row.get("ContentFingerprint", "").strip()
        if not old_fp:
            row["ContentFingerprint"] = current_fp
            row["ReviewStatus"] = "pending"
            row["ReviewedAt"] = ""
            row["ReviewerType"] = ""
            row["ReviewNote"] = "missing fingerprint is unreviewed; explicit approval required"
            missing_fingerprint_invalidated += 1
        elif old_fp != current_fp:
            row["ContentFingerprint"] = current_fp
            row["ReviewStatus"] = "pending"
            row["ReviewedAt"] = ""
            row["ReviewerType"] = ""
            row["ReviewNote"] = "release-visible content changed after previous review; explicit re-review required"
            invalidated += 1

    existing.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, FIELDS, existing)

    required_rows = [by_key[k] for k in review_keys]
    model_reviewed = sum(r["ReviewStatus"] == "model-reviewed" for r in required_rows)
    human_reviewed = sum(r["ReviewStatus"] == "human-reviewed" for r in required_rows)
    pending = sum(r["ReviewStatus"] == "pending" for r in required_rows)

    stats = read_csv(STATS)
    upsert_metric(stats, "learner_review_registry_current", len(required_rows))
    upsert_metric(stats, "learner_model_reviewed_current", model_reviewed)
    upsert_metric(stats, "learner_human_reviewed_current", human_reviewed)
    upsert_metric(stats, "learner_review_pending_current", pending)
    write_csv(STATS, ["Metric", "Value"], stats)
    print(
        "Learner review registry: "
        f"required={len(required_rows)}, released={len(released)}, admitted_allowed={allowed_count}, "
        f"model={model_reviewed}, human={human_reviewed}, pending={pending}, added={added}, "
        f"invalidated={invalidated}, missing_fingerprint_invalidated={missing_fingerprint_invalidated}"
    )'''
    text = replace_between(text, "def main() -> None:", 'if __name__ == "__main__":', new_main, "sync main")
    SYNC.write_text(text, encoding="utf-8")


def patch_approve() -> None:
    text = APPROVE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'REGISTRY = BASE / "learner" / "presentation_review_registry.csv"\n',
        'REGISTRY = BASE / "learner" / "presentation_review_registry.csv"\nADMISSION = BASE / "learner" / "learning_admission.csv"\n',
        "approve admission path",
    )
    new_main = r'''def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch-id", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--expected-count", type=int, required=True)
    p.add_argument("--reviewer-type", choices=["model", "human"], required=True)
    p.add_argument("--review-note", required=True)
    p.add_argument("--confirm-all-current", action="store_true")
    p.add_argument(
        "--pending-only",
        action="store_true",
        help="Approve only currently pending rows in the released-or-admitted review scope.",
    )
    args = p.parse_args()
    if not args.confirm_all_current:
        raise SystemExit("Refusing approval without --confirm-all-current")
    if not args.batch_id.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("batch-id may contain only letters, digits, '-' and '_'")

    for path in (MASTER, LEARNER, REGISTRY, ADMISSION, STATS, *REPORTS):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")
    for report in REPORTS:
        rows = read_csv(report)
        if rows:
            raise SystemExit(f"Cannot approve while review report is non-empty: {report.relative_to(ROOT)} ({len(rows)} rows)")

    approval_path = APPROVAL_DIR / f"{args.batch_id}.csv"
    if approval_path.exists():
        raise SystemExit(f"Approval batch already exists and is immutable: {approval_path.relative_to(ROOT)}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    registry_rows = read_csv(REGISTRY)
    master_by_id = {r["NoteID"]: r for r in master_rows}
    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    registry_by_key = {
        (r["LearnerProfile"], r["LearnerLevel"], r["NoteID"]): r for r in registry_rows
    }

    released_ids = {
        r["NoteID"] for r in master_rows
        if r.get("Released") == "yes"
        and r["NoteID"] in learner_by_id
        and learner_by_id[r["NoteID"]].get("LearnerProfile") == args.profile
        and learner_by_id[r["NoteID"]].get("LearnerLevel") == str(args.level)
    }
    allowed_ids = {
        r.get("NoteID", "").strip()
        for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == args.profile
        and r.get("LearnerLevel", "").strip() == str(args.level)
        and r.get("Status", "").strip() == "allowed"
    }
    required_ids = sorted(released_ids | allowed_ids)
    if not required_ids:
        raise SystemExit("No released-or-admitted learner presentations found for approval")

    for nid in required_ids:
        if nid not in master_by_id or nid not in learner_by_id:
            raise SystemExit(f"Review scope references missing Master/Learner row: {nid}")
        key = (args.profile, str(args.level), nid)
        if key not in registry_by_key:
            raise SystemExit(f"Missing registry row: {key}")
        row = registry_by_key[key]
        current_fp = fingerprint(master_by_id[nid], learner_by_id[nid])
        if row.get("ContentFingerprint", "") != current_fp:
            raise SystemExit(f"Registry fingerprint does not match current content: {nid}")

    selected_ids = required_ids
    if args.pending_only:
        selected_ids = [
            nid for nid in required_ids
            if registry_by_key[(args.profile, str(args.level), nid)].get("ReviewStatus") == "pending"
        ]
    if len(selected_ids) != args.expected_count:
        raise SystemExit(
            f"Expected {args.expected_count} selected review rows, found {len(selected_ids)} "
            f"(required_scope={len(required_ids)}, pending_only={args.pending_only})"
        )
    if not selected_ids:
        raise SystemExit("Refusing to create an empty approval batch")

    reviewed_at = date.today().isoformat()
    status = "human-reviewed" if args.reviewer_type == "human" else "model-reviewed"
    approval_rows: list[dict[str, str]] = []
    for nid in selected_ids:
        key = (args.profile, str(args.level), nid)
        row = registry_by_key[key]
        current_fp = fingerprint(master_by_id[nid], learner_by_id[nid])
        row["ReviewStatus"] = status
        row["ReviewedAt"] = reviewed_at
        row["ReviewerType"] = args.reviewer_type
        row["ReviewNote"] = args.review_note
        approval_rows.append({
            "BatchID": args.batch_id,
            "LearnerProfile": args.profile,
            "LearnerLevel": str(args.level),
            "NoteID": nid,
            "ContentFingerprint": current_fp,
            "ReviewStatus": status,
            "ReviewedAt": reviewed_at,
            "ReviewerType": args.reviewer_type,
            "ReviewNote": args.review_note,
        })

    registry_rows.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, REGISTRY_FIELDS, registry_rows)
    write_csv(approval_path, APPROVAL_FIELDS, approval_rows)

    stats = read_csv(STATS)
    required_rows = [registry_by_key[(args.profile, str(args.level), nid)] for nid in required_ids]
    model_count = sum(r["ReviewStatus"] == "model-reviewed" for r in required_rows)
    human_count = sum(r["ReviewStatus"] == "human-reviewed" for r in required_rows)
    pending_count = sum(r["ReviewStatus"] == "pending" for r in required_rows)
    upsert_metric(stats, "learner_review_registry_current", len(required_rows))
    upsert_metric(stats, "learner_model_reviewed_current", model_count)
    upsert_metric(stats, "learner_human_reviewed_current", human_count)
    upsert_metric(stats, "learner_review_pending_current", pending_count)
    write_csv(STATS, ["Metric", "Value"], stats)

    print(
        f"Approved learner review batch {args.batch_id}: selected={len(selected_ids)}, "
        f"required_scope={len(required_ids)}, status={status}, pending={pending_count}, "
        f"manifest={approval_path.relative_to(ROOT)}"
    )'''
    text = replace_between(text, "def main() -> None:", 'if __name__ == "__main__":', new_main, "approve main")
    APPROVE.write_text(text, encoding="utf-8")


def main() -> None:
    patch_release()
    patch_sync()
    patch_approve()
    print("Patched Vocabulary release/review gate semantics")


if __name__ == "__main__":
    main()
