#!/usr/bin/env python3
"""One-time hardening migration for the long-lived Klose vocabulary architecture."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Patch anchor not found: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"Patch anchor is not unique: {label}")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, next_name: str, replacement: str) -> str:
    pattern = rf"def {re.escape(name)}\(.*?(?=\ndef {re.escape(next_name)}\()"
    new_text, count = re.subn(pattern, replacement.rstrip() + "\n\n", text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Could not replace function {name}")
    return new_text


def build_source_identity_map() -> None:
    registry_path = MASTER / "note_registry.csv"
    target = MASTER / "source_identity_map.csv"
    with registry_path.open("r", encoding="utf-8-sig", newline="") as f:
        registry = list(csv.DictReader(f))
    rows = []
    seen = set()
    for row in registry:
        origin = row["PrimaryOriginKey"].strip()
        if "|" not in origin:
            raise SystemExit(f"Invalid PrimaryOriginKey: {origin}")
        source_id, source_item_key = origin.split("|", 1)
        key = (source_id, source_item_key)
        if key in seen:
            raise SystemExit(f"Duplicate source identity key: {key}")
        seen.add(key)
        rows.append({
            "SourceID": source_id,
            "SourceItemKey": source_item_key,
            "NoteID": row["NoteID"].strip(),
            "Decision": "baseline-confirmed",
            "Status": "confirmed",
        })
    if len(rows) != 802:
        raise SystemExit(f"Expected 802 baseline identity mappings, got {len(rows)}")
    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["SourceID", "SourceItemKey", "NoteID", "Decision", "Status"])
        w.writeheader(); w.writerows(rows)


def patch_profile() -> None:
    path = BASE / "config" / "profile.json"
    data = json.loads(read(path))
    initial = data.pop("initial_release_date", "2026-09-04")
    scopes = data.get("released_scopes", [])
    if not isinstance(scopes, list):
        raise SystemExit("released_scopes must be a list")
    for scope in scopes:
        if not isinstance(scope, dict):
            raise SystemExit("released_scopes entries must be objects")
        scope.setdefault("released_at", initial)
        scope.setdefault("reason", "initial-grade4-scope")
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def patch_builder() -> None:
    path = ROOT / "tools" / "build_klose_vocabulary.py"
    text = read(path)
    text = replace_once(
        text,
        'RELEASE_REGISTRY = MASTER_DIR / "release_registry.csv"\n',
        'RELEASE_REGISTRY = MASTER_DIR / "release_registry.csv"\nSOURCE_IDENTITY_MAP = MASTER_DIR / "source_identity_map.csv"\n',
        "builder identity map constant",
    )

    replacement_registry = r'''def load_registry() -> list[dict[str, str]]:
    """Load committed identity state. Never bootstrap it from current Master."""
    if not REGISTRY.exists():
        raise SystemExit("Persistent note_registry.csv is missing; refusing to rebuild identity history")
    registry = read_csv(REGISTRY)
    if not registry:
        raise SystemExit("note_registry.csv is empty")
    seen_ids: set[str] = set()
    seen_origins: set[str] = set()
    for row in registry:
        nid = row["NoteID"].strip()
        org = row["PrimaryOriginKey"].strip()
        if nid in seen_ids:
            raise SystemExit(f"Duplicate NoteID in registry: {nid}")
        if not org or org in seen_origins:
            raise SystemExit(f"Invalid/duplicate PrimaryOriginKey in registry: {org}")
        note_num(nid)
        seen_ids.add(nid)
        seen_origins.add(org)
    registry.sort(key=lambda r: note_num(r["NoteID"]))
    return registry


def source_item_key(word: str) -> str:
    """Stable source-adapter item key for the current rj_start1 baseline."""
    return match_key(word)


def load_source_identity_map(
    source_rows: list[dict[str, str]], registry: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    """Load committed SourceItem -> NoteID decisions; never re-resolve silently."""
    if not SOURCE_IDENTITY_MAP.exists():
        raise SystemExit("Persistent source_identity_map.csv is missing")
    rows = read_csv(SOURCE_IDENTITY_MAP)
    registry_ids = {r["NoteID"].strip() for r in registry}
    current: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("Status", "").strip() != "confirmed":
            continue
        nid = row.get("NoteID", "").strip()
        if nid not in registry_ids:
            raise SystemExit(f"Source identity map references unknown NoteID: {nid}")
        if row.get("SourceID", "").strip() != SOURCE_ID:
            continue
        key = row.get("SourceItemKey", "").strip()
        if not key or key in current:
            raise SystemExit(f"Invalid/duplicate {SOURCE_ID} SourceItemKey: {key!r}")
        current[key] = row

    expected = {source_item_key(r["Word"]) for r in source_rows}
    actual = set(current)
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise SystemExit(
            "Source identity coverage mismatch; explicit identity resolution required. "
            f"missing={missing[:20]} extra={extra[:20]}"
        )
    return rows, current'''
    text = replace_function(text, "load_or_bootstrap_registry", "source_grade_membership", replacement_registry)

    replacement_release = r'''def load_or_extend_releases(
    config: dict[str, object],
    identity_by_key: dict[str, dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], bool]:
    if not RELEASE_REGISTRY.exists():
        raise SystemExit("Persistent release_registry.csv is missing")
    releases = read_csv(RELEASE_REGISTRY)
    released = {r["NoteID"] for r in releases}

    scopes_raw = config.get("released_scopes", [])
    scopes: list[tuple[set[int], str, str]] = []
    for scope in scopes_raw if isinstance(scopes_raw, list) else []:
        if not isinstance(scope, dict) or scope.get("source_id") != SOURCE_ID:
            continue
        grades_raw = scope.get("grades", [])
        if not isinstance(grades_raw, list):
            raise SystemExit("release scope grades must be a list")
        grades = {int(x) for x in grades_raw}
        released_at = str(scope.get("released_at", "")).strip()
        reason = str(scope.get("reason", "")).strip() or f"scope:{SOURCE_ID}:grades={','.join(map(str, sorted(grades)))}"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", released_at):
            raise SystemExit(f"release scope requires ISO released_at: {scope}")
        scopes.append((grades, released_at, reason))

    grade_membership = source_grade_membership(source_rows)
    changed = False
    for item_key, grades in grade_membership.items():
        matches = [(date, reason) for allowed, date, reason in scopes if grades & allowed]
        if not matches:
            continue
        nid = identity_by_key[item_key]["NoteID"].strip()
        if nid in released:
            continue
        release_date, reason = min(matches, key=lambda x: x[0])
        releases.append({"NoteID": nid, "ReleasedAt": release_date, "ReleaseReason": reason})
        released.add(nid)
        changed = True

    releases.sort(key=lambda r: note_num(r["NoteID"]))
    if changed:
        write_csv(RELEASE_REGISTRY, RELEASE_FIELDS, releases)
    return releases, changed'''
    text = replace_function(text, "load_or_extend_releases", "trivial_grade4_reason", replacement_release)

    text = replace_once(
        text,
        '    for required in (CONFIG, SOURCE_MASTER, SOURCE_OCCURRENCES):\n',
        '    for required in (CONFIG, SOURCE_MASTER, SOURCE_OCCURRENCES, REGISTRY, RELEASE_REGISTRY, SOURCE_IDENTITY_MAP):\n',
        "builder required state",
    )
    text = replace_once(
        text,
        '    registry, registry_changed = load_or_bootstrap_registry(source_rows)\n    registry_by_origin = {r["PrimaryOriginKey"]: r for r in registry}\n    releases, releases_changed = load_or_extend_releases(config, registry, source_rows)\n',
        '    registry = load_registry()\n    registry_by_id = {r["NoteID"]: r for r in registry}\n    identity_map_rows, identity_by_key = load_source_identity_map(source_rows, registry)\n    releases, releases_changed = load_or_extend_releases(config, identity_by_key, source_rows)\n',
        "builder registry calls",
    )
    text = replace_once(
        text,
        '        org = origin_key(src["Word"])\n        reg = registry_by_origin[org]\n        nid = reg["NoteID"]\n',
        '        item_key = source_item_key(src["Word"])\n        nid = identity_by_key[item_key]["NoteID"].strip()\n        reg = registry_by_id[nid]\n',
        "builder master resolution",
    )
    text = replace_once(
        text,
        '        org = origin_key(occ["Word"])\n        if org not in registry_by_origin:\n            raise SystemExit(f"Occurrence without registry identity: {occ[\'Word\']}")\n        nid = registry_by_origin[org]["NoteID"]\n',
        '        item_key = source_item_key(occ["Word"])\n        if item_key not in identity_by_key:\n            raise SystemExit(f"Occurrence without committed source identity: {occ[\'Word\']}")\n        nid = identity_by_key[item_key]["NoteID"].strip()\n',
        "builder occurrence resolution",
    )
    text = text.replace('        {"Metric": "registry_changed", "Value": str(registry_changed).lower()},\n', '        {"Metric": "source_identity_map_rows", "Value": len(identity_map_rows)},\n        {"Metric": "registry_changed", "Value": "false"},\n')
    write(path, text)


def patch_persistent_check() -> None:
    path = ROOT / "tools" / "check_klose_persistent_state.py"
    text = read(path)
    text = replace_once(text, 'RELEASES = BASE / "release_registry.csv"\n', 'RELEASES = BASE / "release_registry.csv"\nSOURCE_MAP = BASE / "source_identity_map.csv"\n', "checker map constant")
    text = replace_once(text, '    missing = [p for p in (REGISTRY, RELEASES) if not p.exists()]\n', '    missing = [p for p in (REGISTRY, RELEASES, SOURCE_MAP) if not p.exists()]\n', "checker missing state")
    anchor = '    registry_ids = set(ids)\n    release_ids: set[str] = set()\n'
    insert = '''    registry_ids = set(ids)\n\n    source_map = read_csv(SOURCE_MAP)\n    map_keys: set[tuple[str, str]] = set()\n    mapped_ids: set[str] = set()\n    for row in source_map:\n        source_id = row.get("SourceID", "").strip()\n        item_key = row.get("SourceItemKey", "").strip()\n        nid = row.get("NoteID", "").strip()\n        status = row.get("Status", "").strip()\n        key = (source_id, item_key)\n        if not source_id or not item_key or key in map_keys:\n            raise SystemExit(f"Invalid/duplicate SourceIdentity key: {key}")\n        if nid not in registry_ids:\n            raise SystemExit(f"Source identity references unknown NoteID: {nid}")\n        if status != "confirmed":\n            raise SystemExit(f"Unconfirmed persistent SourceIdentity row: {key}")\n        map_keys.add(key)\n        mapped_ids.add(nid)\n    if not source_map:\n        raise SystemExit("source_identity_map.csv is empty")\n\n    release_ids: set[str] = set()\n'''
    text = replace_once(text, anchor, insert, "checker map validation")
    text = replace_once(
        text,
        '    print(f"Persistent state OK: registry={len(registry_ids)}, released={len(release_ids)}")\n',
        '    print(f"Persistent state OK: registry={len(registry_ids)}, source_map={len(source_map)}, released={len(release_ids)}")\n',
        "checker print",
    )
    write(path, text)


def patch_docs() -> None:
    readme = BASE / "README.md"
    text = read(readme)
    text = text.replace('│   ├── release_registry.csv       # 已释放学习集合\n', '│   ├── source_identity_map.csv    # SourceItem → NoteID 持久映射\n│   ├── release_registry.csv       # 已释放学习集合及实际释放日期\n')
    text = text.replace('以下两个文件不能视为普通缓存：', '以下三个文件不能视为普通缓存：')
    text = text.replace('master/note_registry.csv\nmaster/release_registry.csv', 'master/note_registry.csv\nmaster/source_identity_map.csv\nmaster/release_registry.csv')
    text = text.replace('python tools/build_klose_vocabulary.py\n', 'python tools/check_klose_persistent_state.py\npython tools/build_klose_vocabulary.py\n', 1)
    write(readme, text)

    agents = ROOT / "AGENTS.md"
    text = read(agents)
    text = text.replace('Registry/Release Registry 缺失时必须失败', 'Registry/Source Identity Map/Release Registry 缺失时必须失败')
    text = text.replace('master/                    # NoteID registry / release registry / master / occurrences', 'master/                    # NoteID registry / source identity map / release registry / master / occurrences')
    text = text.replace('- Persistent Registry / Release Registry 存在且内部一致；', '- Persistent Registry / Source Identity Map / Release Registry 存在且内部一致；')
    text = text.replace('3. 与 Registry 做 sense-aware candidate matching；\n4. 明确已有 unit → 原 NoteID + 扩展 provenance；', '3. 与 Registry 做 sense-aware candidate matching；\n4. 将确认后的 `SourceItemKey → NoteID` 决策写入 committed `source_identity_map.csv`；\n5. 明确已有 unit → 原 NoteID + 扩展 provenance；')
    text = text.replace('5. 明确新 unit → 追加新 NoteID，旧 ID 不重排；\n6. 模糊项 → review；\n7. 生成当前 Learner Layer；\n8. 根据 release config 决定新 Note 是否进入 `study.csv`；\n9. 重建并跑 CI。', '6. 明确新 unit → 追加新 NoteID，旧 ID 不重排；\n7. 模糊项 → review；\n8. 生成当前 Learner Layer；\n9. 根据带 `released_at` 的 release scope 决定新 Note 是否进入 `study.csv`；\n10. 重建并跑 CI。')
    write(agents, text)

    doc = ROOT / "docs" / "KLOSE_VOCABULARY_SYSTEM.md"
    text = read(doc)
    marker = '### 3.2 Source Occurrence / Provenance\n'
    section = '''### 3.2 Source Identity Map（持久化）\n\n跨来源接入时，candidate matching 的确认结果必须持久化：\n\n```text\nSourceID\nSourceItemKey\nNoteID\nDecision\nStatus\n```\n\n`source_identity_map.csv` 与 `note_registry.csv` 一样属于长期状态，不是每次构建重新推导的缓存。新教材接入时可以重新计算候选，但一旦确认某个 source learning unit 对应某个 NoteID，后续构建必须复用该映射；若语义发生冲突，进入 identity migration/review，而不是静默改映射。\n\n### 3.3 Source Occurrence / Provenance\n'''
    if marker in text:
        text = text.replace(marker, section, 1)
        text = text.replace('### 3.3 Vocabulary Fact / Master', '### 3.4 Vocabulary Fact / Master', 1)
        text = text.replace('### 3.4 Learner Presentation', '### 3.5 Learner Presentation', 1)
    text = text.replace('`release_registry.csv` 记录已释放 Note。', '`release_registry.csv` 记录已释放 Note；每个 release scope 必须显式带 `released_at`，因此 Grade 5/新来源在未来释放时不会被错误记成初始基线日期。')
    write(doc, text)


def patch_workflow() -> None:
    path = ROOT / ".github" / "workflows" / "build-klose-vocabulary.yml"
    text = read(path)
    text = replace_once(text, "      - 'anki/klose/master/note_registry.csv'\n", "      - 'anki/klose/master/note_registry.csv'\n      - 'anki/klose/master/source_identity_map.csv'\n", "workflow source map trigger")
    write(path, text)


def main() -> None:
    build_source_identity_map()
    patch_profile()
    patch_builder()
    patch_persistent_check()
    patch_docs()
    patch_workflow()
    print("Klose architecture v2 hardening applied")


if __name__ == "__main__":
    main()
