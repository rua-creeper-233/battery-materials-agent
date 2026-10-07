# Battery Evidence Lab · 电池材料计算科研助手

面向 DFT、VASP、NEB、AIMD、分子动力学与机器学习原子势的证据检索、学习和工作流助手。论文提供可追踪事实，本地模型组织回答，工具层读取证据并生成可审阅的研究流程。

公开入口：[Battery Evidence Lab](https://rua-creeper-233.github.io/battery-materials-agent/)。

## 当前状态

<!-- CURRENT_STATUS_START -->
统计日期 **2026-10-08**：**176 篇唯一 DOI**；本机已有校验正文 **128 篇**、页码文本块 **6858 个**；WOS UT **16 条**。

QLoRA 数据：**793 训练 / 78 验证 / 127 测试**。已通过 5 步 GPU 流程验证，未做正式训练或准确率评估；数量与哈希详见 [当前状态](guides/PROJECT_STATUS.md)。
<!-- CURRENT_STATUS_END -->

旧日期版记录是历史快照；最新统计以 [PROJECT_STATUS.md](guides/PROJECT_STATUS.md)、数据文件和审计结果为准。

## 研究、学习与问答

| 入口 | 内容 |
|---|---|
| [AI 应用页面](https://rua-creeper-233.github.io/battery-materials-agent/ai-battery-applications.html) | 固态扩散、电解液/聚合物筛选、反应性 SEI、正极筛选、界面与多尺度、科研证据助手 |
| [AI 实施指南](guides/AI_BATTERY_APPLICATIONS.md) | 数据、模型、计算、验证和软硬件实现路径 |
| [数据驱动复现路线](guides/REPRODUCIBLE_BATTERY_AI_20261008.md) | LiTraj、SevenNet 液态电解液、领域通用势的小规模起步与验收 |
| [未来方向](guides/BATTERY_COMPUTATION_FUTURE_DIRECTIONS.md) | 近期综述与方法论文支持的研究问题、最小验证和适用边界 |
| 首页学习区 | MS、VASP、DFT、MD 的入门教程、步骤和练习 |
| [模型与 Agent 接入](FINETUNE_INTEGRATION.md) | RTX 3060 6GB、WSL、QLoRA 数据、适配器服务与 RAG 配置 |

论文卡片提供 `MS / DFT / MD / VASP / 方法论文 / 进展论文 / 综述 / 观点` 标签。`MS` 表示论文方法中确有 BIOVIA Materials Studio 的使用证据。

搜索支持中文问题以及 `tag:DFT`、`tag:MD`、`tag:VASP`、`tag:MS`、`type:方法论文`。结果显示命中理由、DOI、已有 WOS UT 和本机全文页码。检索排序调参与模型微调分别维护。

配置兼容接口后，可启用引用约束 RAG；本机工具 Agent 能选择“找论文、取记录、查全文、生成工作流”，最多四次只读动作。未配置模型时使用确定性流程。引用或数值检查失败会回退；科学结论仍要回看原文与计算。

## 启动

Windows 双击 `start.bat`，或在仓库目录运行：

```powershell
.\start.ps1
```

打开 `http://127.0.0.1:8765`。`start-rag.bat` 启动可选模型问答，`start-share.bat` 建立临时 HTTPS 共享入口。公开 GitHub Pages 可独立浏览；上传、全文、Zotero 深链和本地模型需要本地后端。见 [共享指南](SHARING_GUIDE.md) 和 [RAG 配置](RAG_SETUP.md)。

## 文献与全文维护

`data/papers.json` 是公开精选书目，保存准确标题、作者、年份、DOI、体系、方法、简述与核验来源。出版社核验、WOS 核验、全文下载和阅读理解分别记录。

```powershell
python fetch_literature.py --try-publisher
python audit_library.py
python extract_method_evidence.py
python build_paper_tags.py
```

下载器使用开放获取、作者公开稿、机构仓储与当前有权访问来源，校验 PDF、题名、正文/补充材料、页数和 SHA-256。失败项保留 DOI 入口。自动方法信号帮助定位原文，最终计算参数需根据体系核验与收敛。状态见 [全文审计](FULLTEXT_AUDIT.md)、[方法定位](METHOD_EVIDENCE_AUDIT.md) 和 [书目审计](PAPER_AUDIT.md)。

新增书目按 DOI 幂等导入本机 Zotero：

```powershell
python import_zotero_library.py --apply
python sync_zotero_links.py
```

已有书目缺附件时，下载、审计后执行 `python attach_zotero_pdf.py --paper-id <ID>`；本机写授权由 Zotero 提示。深链保存在 Git 忽略的 `private/` 中；本机结果见 [Zotero 审计](ZOTERO_IMPORT_AUDIT.md)，云同步由客户端确认。

## QLoRA 数据与模型

新版三路数据从精选元数据和人工简述生成：

```powershell
python training/expand_dataset.py
python training/validate_dataset.py --train finetune/data/train.jsonl --eval finetune/data/validation.jsonl --test finetune/data/test.jsonl
```

训练、验证、测试按 DOI/来源论文连通分组隔离。验证集用于选择方案，测试集在方案固定后使用。`finetune/data/manifest.json` 记录数量、来源和文件哈希。旧 `training/generate_dataset.py` 的二路数据保留为历史/回归材料，不与新版留出集混合训练。

QLoRA 学习问答组织、引用和证据不足时的响应；MLIP 学习能量、力、应力以运行原子模拟。二者的标签与验收不同。RTX 3060 6GB 的执行步骤见 [接入指南](FINETUNE_INTEGRATION.md) 和 [硬件指南](training/README_RTX3060.md)。新增数据不等于模型已经重训，指标改善通过留出测试确认。

## 稳定接口

| 接口 | 用途 |
|---|---|
| `GET /api/capabilities` | 上传限制、服务与关键词功能 |
| `POST /api/chat` | 检索回答与可选 RAG |
| `POST /api/agent` | 受限工具选择流程 |
| `POST /api/upload` | 本机/授权共享 PDF 上传与索引 |
| `POST /api/keywords` | 版本化关键词提取，保留模型接入位置 |
| `GET /api/paper-tags` | 标签和逐篇方法证据 |
| `GET /api/zotero-links` | 仅本机私有文库深链 |

上传文献存入本机私有库；远程接口使用临时密钥与限定 Origin。论文全文、本机下载清单、机构会话、API 密钥、Zotero 私有键和模型权重不进入公开包。下载清单保留在本机 `literature/manifest.json`，公开数量由 `data/project_status.json` 提供。VASP 源码、许可证与 POTCAR 由授权环境管理。

## 验证与大版本发布

```powershell
python -m unittest discover -s tests
node --test tests/test_learning_ui.mjs
python update_project_status.py --date 2026-10-08
python build_pages.py
```

GitHub Pages 使用 `main:/docs`。完成一轮有实际验证的大版本后，统一更新发布说明与 distill，再提交、推送；小改动在本地整合。每个大版本提交作为回退点。

下一步优先做独立科研问题评测、关键论文参数人工核验、可追踪结构来源与计算结果检查。研究建议结合可用数据、算力和目标体系确定。
