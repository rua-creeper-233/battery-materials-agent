# 本地问答小模型数据集

这里是给个人电脑使用的、可审阅的电池材料计算问答数据层。它不是把论文全文塞进模型：生成器只读取 `data/papers.json`、`data/answer_guidance.json`、`data/answer_regression.json` 和 `data/search_training.json` 的结构化字段，不读取 PDF 或 `fulltext_chunks.jsonl`，因此不会把受版权保护的正文复制进训练集。

## 生成与检查

在仓库根目录运行：

```powershell
python training/generate_dataset.py
python -c "import json, pathlib; [json.loads(x) for p in pathlib.Path('training').glob('*.jsonl') for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]; print('JSONL OK')"
```

脚本是幂等的，使用来源论文分组的 SHA-256 做固定切分：同一篇论文的所有样本只会进入训练或评估一侧，避免“同论文不同问题”的泄漏；多论文工具题按共享论文组成连通分组，没有论文来源的通用工具题按自身 ID 稳定切分。当前生成 285 条样本，其中训练 238 条、盲评 47 条。每条记录都有 `messages`、`provenance`、来源论文 ID、DOI/URL（若有）、任务类别、难度、是否要求引用和 `split`。要求引用的样本会把短的结构化证据包放入用户消息，并在回答中使用 `[P1]` 等来源编号；`eval.jsonl` 是保留的盲评集合，不应拿来训练。`manifest.json` 记录数量和来源。

四类训练文件分别是：事实问答 `qa_factual.jsonl`、复现/工作流 `qa_workflow.jsonl`、证据不足时的拒答与边界判断 `qa_refusal.jsonl`、检索—核验工具轨迹 `tool_traces.jsonl`。回答内容只来自结构化字段；没有页码时不会虚构页码。

## 怎样真正做一个“只用于问答”的本地模型

推荐先做 RAG，再考虑微调。用一个本地向量库保存论文标题、摘要、人工证据和允许使用的笔记；用户问题先检索，再把检索片段交给小模型回答，并强制返回 DOI/来源。这样更新论文只需更新索引，不必重新训练，也更适合本项目的版权和可追溯要求。`tool_traces.jsonl` 可用于测试检索—核验流程，不应被误解为真实工具执行日志。

若已有 8–12 GB 显存，可在脱敏后的 `qa_*.jsonl` 上尝试 1B–3B 指令模型的 LoRA/QLoRA；16–24 GB 显存更适合 3B–7B 的 4-bit QLoRA。使用 Hugging Face Transformers、PEFT、TRL、bitsandbytes 或同类工具时，先固定模型许可证、版本和随机种子。训练集只教“如何回答、何时引用、何时拒答”，不要把事实库当作永久知识；事实更新仍走 RAG。没有合适显卡时，可只运行 RAG 或用 CPU 做小规模评估，不要把本机训练能力和模型质量混为一谈。

## 最小评估清单

1. 只用训练文件拟合，`eval.jsonl` 完全隔离。
2. 检查 DOI 是否被正确引用、未知问题是否拒答、DFT/MD/力场边界是否保持。
3. 记录 exact match/关键词命中、引用准确率、拒答准确率和人工抽样结果；不能只看训练 loss。
4. 对每次数据或提示词改动保存 manifest、模型版本、评估结果和错误样例。

## 隐私与安全

所有生成步骤默认本地执行。不要把 Zotero 数据库、机构登录信息、API 密钥、私人 PDF 或未授权全文上传到训练平台或 GitHub。发布数据集前只保留公开 DOI、出版社 URL、人工撰写的短摘要和可公开的证据链接；如果要把自己的阅读笔记加入 RAG，先确认版权和机构政策。
