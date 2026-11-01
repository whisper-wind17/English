#!/usr/bin/env python3
"""Minimal stdlib XLSX reader used by the NCE1 source adapter."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XLSX = ROOT / "8.新概念英语" / "新概念英语第一册（新版）.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "")
    if not letters:
        return 0
    value = 0
    for ch in letters.group(0):
        value = value * 26 + ord(ch) - 64
    return value - 1


def read_first_sheet(path: Path = DEFAULT_XLSX) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iterfind(".//m:t", NS)))

        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            names = sorted(n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
            if not names:
                raise ValueError(f"No worksheet XML in {path}")
            sheet_name = names[0]

        root = ET.fromstring(zf.read(sheet_name))
        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            values: dict[int, str] = {}
            max_col = -1
            for cell in row.findall("m:c", NS):
                idx = _col_index(cell.get("r", ""))
                max_col = max(max_col, idx)
                typ = cell.get("t", "")
                if typ == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                else:
                    node = cell.find("m:v", NS)
                    raw = "" if node is None else (node.text or "")
                    if typ == "s" and raw:
                        value = shared[int(raw)]
                    else:
                        value = raw
                values[idx] = value.strip()
            if max_col >= 0:
                rows.append([values.get(i, "") for i in range(max_col + 1)])
        return rows


def normalize(value: str) -> str:
    return re.sub(r"\\s+", " ", (value or "").strip()).casefold()


def read_xlsx_lexicon(path: Path = DEFAULT_XLSX) -> dict[str, list[dict[str, str]]]:
    rows = read_first_sheet(path)
    if not rows:
        raise ValueError("NCE1 XLSX is empty")
    header = rows[0]
    required = ["单词", "英音", "美音", "释义"]
    if header[:4] != required:
        raise ValueError(f"Unexpected NCE1 XLSX header: {header}")
    out: dict[str, list[dict[str, str]]] = {}
    for values in rows[1:]:
        values = values + [""] * (4 - len(values))
        word, british, american, definition = values[:4]
        key = normalize(word)
        if not key:
            continue
        out.setdefault(key, []).append({
            "Word": word,
            "British": british.strip("[] "),
            "American": american.strip("[] "),
            "DefinitionRaw": definition,
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    rows = read_first_sheet(args.path)
    print(json.dumps({"rows": len(rows), "sample": rows[: args.limit]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
