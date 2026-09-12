# Klose 数据区

当前状态见根目录 [NEXT](../../NEXT.md)，统一入口见 [README](../../README.md)。

| 区域 | 职责 |
| --- | --- |
| config | 学习者与范围配置 |
| master | 持久身份、来源、发布记录；派生 Master |
| learner | 例句和题面输入、当前呈现、准入、review 与不可变凭据 |
| source_reference | 实际教材证据和来源核对输入 |
| expressions | 独立的表达身份、呈现、准入、review 与发布 |
| publish | 确定性产物；正式导入只用 anki-import.csv |
| review | blocker 和待检查报告，未知支撑词为 advisory |
| releases | 当前清单、冻结历史与设备凭据 |
| feedback | 真实学习观察和后续决策 |
| anki | 原地更新使用的 Note/Card 契约与模板 |

Source Grade、LearnerLevel、准入和掌握程度互不替代。稳定 ID 和来源事实持久保存；publish 禁止手工改写。Vocabulary 正面显示 Word 和必要的 PromptHint；Expressions 正面通过场景触发主动表达。

运行 `python tools/klose_pipeline.py all` 完整生成与校验。内容变化必须显式审校；详见 [变更流程](../../docs/CHANGE_WORKFLOW.md)。
