#!/usr/bin/env python3
"""One-time migration: remove examples that use explicitly later-listed vocabulary."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURATION = ROOT / "anki" / "人教版一年级起点" / "curation"

# Word -> (ExampleSentence, ExampleTranslation)
FIXES = {
    "can": ("I can do it.", "我能做到。"),
    "sorry": ("I am sorry.", "我很抱歉。"),
    "wow": ("Wow it is big!", "哇，它真大！"),
    "hand": ("This is my hand.", "这是我的手。"),
    "tongue": ("My tongue hurts.", "我的舌头疼。"),
    "morning": ("It is morning.", "现在是早晨。"),
    "afternoon": ("It is afternoon.", "现在是下午。"),
    "summary": ("This is the summary.", "这是总结。"),
    "cola": ("I don't like cola.", "我不喜欢可乐。"),
    "soon": ("My birthday is soon.", "我的生日快到了。"),
    "March": ("March is in spring.", "三月在春季。"),
    "June": ("June is in summer.", "六月在夏季。"),
    "September": ("September is in autumn.", "九月在秋季。"),
    "tomorrow": ("Tomorrow is Monday.", "明天是星期一。"),
    "uncle": ("My uncle is tall.", "我叔叔个子很高。"),
    "walking the dog": ("I am walking the dog.", "我正在遛狗。"),
    "play with": ("I play with my dog.", "我和我的狗一起玩。"),
    "study": ("This is my study.", "这是我的书房。"),
    "for rent": ("This room is for rent.", "这个房间出租。"),
    "always": ("I always get up at seven.", "我总是七点起床。"),
    "so": ("It is rainy so I am at home.", "下雨了，所以我在家。"),
    "day": ("Today is a sunny day.", "今天是晴朗的一天。"),
    "by ship": ("We go by ship.", "我们乘船去。"),
    "by taxi": ("We go by taxi.", "我们乘出租车去。"),
    "by subway": ("We go by subway.", "我们乘地铁去。"),
    "by plane": ("We go by plane.", "我们乘飞机去。"),
    "pen": ("This is my pen.", "这是我的钢笔。"),
    "Excuse me": ("Excuse me where is the gate?", "请问大门在哪里？"),
    "phone": ("I have a phone.", "我有一部电话。"),
    "farmer": ("The farmer is a worker.", "农民是一名劳动者。"),
    "people": ("Many people are here.", "许多人在这里。"),
    "send": ("I send a card.", "我寄一张卡片。"),
    "before": ("I get up before seven.", "我七点前起床。"),
    "Big Ben": ("Big Ben is in the UK.", "大本钟在英国。"),
    "has": ("The panda has black ears.", "熊猫有黑色的耳朵。"),
    "elephant": ("The elephant is big.", "大象很大。"),
    "panda": ("The panda is black.", "熊猫是黑色的。"),
    "into": ("The cat jumped into the water.", "猫跳进了水里。"),
    "silk": ("This dress is made of silk.", "这条连衣裙是丝绸做的。"),
}


def main() -> None:
    found: set[str] = set()
    changed_files = 0
    for path in sorted(CURATION.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)

        changed = False
        for row in rows:
            word = row.get("Word", "")
            if word not in FIXES:
                continue
            found.add(word)
            sentence, translation = FIXES[word]
            if row.get("ExampleSentence") != sentence or row.get("ExampleTranslation") != translation:
                row["ExampleSentence"] = sentence
                row["ExampleTranslation"] = translation
                changed = True

        if changed:
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            changed_files += 1

    missing = set(FIXES) - found
    if missing:
        raise SystemExit("Fix targets not found: " + ", ".join(sorted(missing)))
    print(f"Example migration targets: {len(found)}; changed files: {changed_files}")


if __name__ == "__main__":
    main()
