# New Concept English 1 — Klose source reference

Klose 实际教材：外研社《新概念英语 1：英语初阶（智慧版）》，ISBN 9787521336702。

正式 source-reference 输入：

- `vocabulary-smart-2022.csv`：906 条按课程顺序排列的 occurrence。
- `source_provenance.json`：教材版本、证据、旧新版基线及已知智慧版差异。
- `vocabulary.csv`：Lesson 1–17 的历史实物照片转录，保留作核验证据。

证据分层：

1. Lesson 1–17：Klose 实物教材照片，`verified-actual`。
2. Lesson 19–144：1997 新版顺序基线 + 外研社“智慧版保留原书全部内容”声明 + 抽样核验，`baseline-reconciled`。
3. 已知差异显式记录，不把 1997 基线静默冒充为 2022 智慧版逐页实物事实。

本目录只保存 Source Fact / reconciliation input；Stable NoteID、Learner Presentation、Admission 和 Anki 发布仍走正式 pipeline。
