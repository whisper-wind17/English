# Klose Learning

为 Klose 长期维护英语 Vocabulary 与 Expressions：准确回忆词义和读音，在新场景中主动表达，并让复习负担可持续。稳定卡片身份与 Anki 学习历史优先于扩充词量。

| 要做的事 | 入口 |
| --- | --- |
| 查看当前进度和下一步 | [NEXT.md](NEXT.md) |
| 查看当前发布数量、校验值、审核分布 | [发布清单](anki/klose/releases/current.json) |
| 更新 Anki | [当前导入 SOP](docs/ANKI_CURRENT_RELEASE_IMPORT.md) |
| 修改数据或代码 | [变更流程](docs/CHANGE_WORKFLOW.md)、[AGENTS.md](AGENTS.md) |
| 记录学习负担与真实效果 | [学习反馈](docs/LEARNING_FEEDBACK.md) |
| 查看本次整改前后对比 | [整改记录](docs/MAINTENANCE_20260912.md) |

从仓库根目录执行（Python 3.12，标准库；保留完整 Git 历史）：

```bash
python tools/klose_pipeline.py build
python -m unittest discover -s tests -v
python tools/klose_pipeline.py all
```

`build` 可以产生待审状态；只有 `all` 成功才可使用正式发布文件。内容变更需要显式审校，CI 不授予内容批准，也不操作 Anki Collection。

Vocabulary 正式包：[anki-import.csv](anki/klose/publish/anki-import.csv)。Expressions 正式包：[anki-import.csv](anki/klose/expressions/publish/anki-import.csv)。导入前按 SOP 核对同一份发布清单。

原始英语词库资源仍保留在原目录。上游项目介绍、作者归属和许可声明见 [原词库说明](docs/archive/UPSTREAM_WORD_LIBRARY.md)；本次入口调整不改变这些资源的授权条件。
