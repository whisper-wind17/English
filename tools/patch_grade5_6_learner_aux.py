#!/usr/bin/env python3
"""One-shot patch: remove explicitly later auxiliary vocabulary from G5-6 examples."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "learner"
FILES = [BASE / "grade5_6_content_batch_a.csv", BASE / "grade5_6_content_batch_b.csv", BASE / "grade5_6_content_batch_c.csv"]
CHECKER = ROOT / "tools" / "check_grade5_6_new_learner_content.py"
REPL = {
"KV000906": ("This robot is here.", "这个机器人在这里。"),
"KV000915": ("This is our school project.", "这是我们的学校项目。"),
"KV000924": ("They laugh.", "他们笑了。"),
"KV000928": ("The lesson is at eight.", "这节课在八点。"),
"KV000947": ("I have a little water.", "我有一点水。"),
"KV000957": ("This is a good way.", "这是一个好方法。"),
"KV000959": ("Nature is all around us.", "大自然就在我们周围。"),
"KV000981": ("It is 8 a.m.", "现在是上午八点。"),
"KV000986": ("This is a letter.", "这是一封信。"),
"KV001005": ("We act it out.", "我们把它表演出来。"),
"KV001017": ("This is my diary.", "这是我的日记。"),
"KV001019": ("What is that noise?", "那是什么声音？"),
"KV001037": ("This is bamboo.", "这是竹子。"),
"KV001054": ("It is dry now.", "现在它干了。"),
"KV001057": ("It is inspiring.", "它很鼓舞人心。"),
"KV001065": ("This is the Red Army.", "这是红军。"),
"KV001079": ("I will do it later.", "我稍后会做。"),
"KV001089": ("We discuss it.", "我们讨论它。"),
"KV001114": ("There is a cloud.", "有一朵云。"),
"KV001139": ("What type is it?", "它是什么类型？"),
"KV001143": ("The clock runs.", "这个钟在运转。"),
"KV001170": ("We camp here.", "我们在这里野营。"),
"KV001172": ("We fish here.", "我们在这里钓鱼。"),
"KV001176": ("The hat is off my head.", "帽子从我头上掉下来了。"),
"KV001186": ("I like cycling.", "我喜欢骑自行车。"),
"KV001189": ("Look it up.", "查一下它。"),
"KV001192": ("This is a cheetah.", "这是一只猎豹。"),
}

def read(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def write(path, rows):
    fields=list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)

def main():
    seen=set()
    for path in FILES:
        rows=read(path)
        for row in rows:
            nid=row["NoteID"].strip()
            if nid in REPL:
                row["ExampleSentence"],row["ExampleTranslation"]=REPL[nid]
                seen.add(nid)
        write(path,rows)
    if seen != set(REPL):
        raise SystemExit(f"Patch coverage mismatch missing={sorted(set(REPL)-seen)}")
    text=CHECKER.read_text(encoding="utf-8")
    old='    "KV001143": {"runs", "fan"},'
    new='    "KV001143": {"runs"},'
    if old not in text:
        raise SystemExit("Expected run-operate cue not found")
    CHECKER.write_text(text.replace(old,new),encoding="utf-8")
    print(f"Patched Grade 5-6 learner auxiliary vocabulary: {len(seen)} examples")
if __name__ == "__main__": main()
