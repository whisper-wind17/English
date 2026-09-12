# 最小学习反馈

当前没有实际学习观察记录；`feedback/pilot.json` 的状态是 `awaiting-observation`。设备导入、发布成功和准入数量都不能证明已经学会。

从首个实际记录的学习周开始，建议每周人工记录一次，首轮观察窗口为 30 天。没有测量的项目留空，不填推算成绩。

| 文件 | 记录什么 | 如何使用 |
| --- | --- | --- |
| observations.csv | 日期区间、Deck、日均复习分钟、积压卡数、Again 比例、困难 ID、迁移尝试与成功数、观察、来源 | 真实负担与表现；比例使用 0..1 |
| learning_support.csv | 支撑词 Token、supported / needs-support、实际日期与证据 | 支撑词不是目标词本身；需要帮助的词出现在 allowed 例句时进入发布 blocker |
| decisions.csv | 决策 ID、日期、证据位置、修改对象、决定和 proposed / applied / verified | 每次调整能追溯到观察，下一周核对效果 |
| pilot.json | 实际开始日期、最后观察日期和试点状态 | 首次真实记录后才填写开始日期 |

以上文件位于 [feedback](../anki/klose/feedback/)。不从 Source Grade、allowed 或已导入推断掌握程度。未知支撑词进入 `review/example_support_review.csv` 供抽查；实际困难进入 `review/future_vocab_review.csv` 并阻止发布。修正例句、补充学习后更新有证据的支持状态，或暂缓该卡的新卡准入，才能关闭问题。

每周用几个已学目标换一个新场景，请 Klose 口头说一句或写一句，记录尝试次数、能否独立完成和困难 ID。Vocabulary 看目标义项及读音是否正确；Expressions 看是否完成交际功能、结构与时态是否合适，允许正确的等效表达，不要求逐字复述 Target。

如果复习时间超过家庭可接受范围、积压持续增加或 Again 偏高，先记录原因，再讨论降低每日新增、简化例句或暂缓新卡。不要仅凭一个比例自动修改 FSRS 参数或重置旧卡。没有家庭时间预算和实际数据时，不预设“已经适龄”或“负担合理”。

后续记录要形成“观察 → 决策 → 上游修正或设备设置 → 下一周复核”。repo 只保存必要汇总和相关学习 ID，不需要复制完整 Anki 学习历史。
