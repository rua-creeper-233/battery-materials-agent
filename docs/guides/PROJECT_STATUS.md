# 当前项目状态

统计日期：2026-10-14。由 `update_project_status.py` 根据实际库、索引与数据集生成。

| 项目 | 实际数量 |
|---|---:|
| 公开精选论文（唯一 DOI） | 176 |
| 2023 年及以后论文 | 92 |
| 已有 WOS UT | 16 |
| QLoRA 训练样本 | 793 |
| QLoRA 验证样本 | 78 |
| QLoRA 测试样本 | 127 |

当前新增的是可追溯问答数据，本版本没有自动重新训练模型。训练/验证/测试按论文来源分组隔离；验证集用于开发选择，测试集留到方案固定后评估。样本来自元数据与人工简述，不能据其数量判断真实科研问答准确率。

公开站点保留书目、DOI、教学资料与数据集统计；本机正文覆盖、索引状态和私有条目键仅保存在本机，不代表公开网页全文可访问率。

- [AI 实施指南](AI_BATTERY_APPLICATIONS.md)
- [未来研究方向](BATTERY_COMPUTATION_FUTURE_DIRECTIONS.md)
- JSON 统计：`data/project_status.json`；训练来源与文件 SHA-256：`finetune/data/manifest.json`。
