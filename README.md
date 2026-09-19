# 电池材料计算科研子智能体

面向 DFT / VASP、NEB、AIMD、机器学习势和电池材料计算的本地、证据优先科研助手。它不是有机太阳能电池智能体：OSC 论文只提供了“文献数据集＋科研问答”的方法启发，知识库已经完全换成电池材料计算。

## 当前可用能力

- 证据库共 65 篇：16 篇核心论文完成 DOI 与 WOS Core Collection 核验，另有 49 篇完成 DOI 与出版社/权威索引记录核验；
- 63/65 篇已有用户合法取得或公开可访问的本地正文，共 3649 个带页码文本块；缺失项明确标记并回退到 DOI/出版社入口；
- 中文检索电压、稳定性、扩散、固态电解质、界面、高通量和机器学习势；
- 论文卡片显示 `MS / DFT / MD / VASP` 与“方法论文 / 进展论文”标签，并支持右栏一键筛选；
- 检索采用可解释的字段加权、同义词扩展与 `tag:` / `type:` 语法，回答会显示查询理解和逐篇命中理由；无匹配时不再用最新论文凑答案；
- 提供可选的证据约束 RAG：模型只收到检索后的元数据与短页码摘录，必须返回 `[P1]` 格式引用；引用缺失或越界时自动回退到规则回答；
- 提供仅限本机的受限工具 Agent：模型最多选择 4 次“查论文、取记录、查全文、生成工作流”只读工具，最终回答必须引用实际读取的来源；
- 回答中给出论文级证据、DOI、精确 WOS 记录和本地全文页码；
- 为 DFT / NEB / AIMD / MLIP 任务生成带质量控制项的工作流；
- 从本地正文中自动定位软件、泛函、截断能、k 点、超胞、MD 条件、NEB 和机器学习训练信号，并逐条保留 PDF 页码；
- 本地有 PDF 时显示“打开本地 PDF”，没有时回退到 WOS 与 DOI；
- 支持按 DOI 幂等写入 Zotero，并可在 Zotero 10 用户确认授权后给已有条目补挂已审计 PDF；本地深链与条目键不会进入 GitHub Pages；
- 支持从网页上传 PDF：校验正文、识别/补充元数据、建立全文索引并返回关键词；用户上传的新增条目保存在本机私有库，不进入 GitHub Pages 发布包。

全文状态与审计证据见 [FULLTEXT_AUDIT.md](FULLTEXT_AUDIT.md)，自动方法信号见 [METHOD_EVIDENCE_AUDIT.md](METHOD_EVIDENCE_AUDIT.md)，书目真实性和 WOS UT 见 [PAPER_AUDIT.md](PAPER_AUDIT.md)。

## 启动

Windows 下可直接双击：

- `start.bat`：一键启动仅本机使用的网页；
- `start-rag.bat`：临时输入兼容接口、模型和密钥，启动带证据约束 RAG 的本地网页；
- `start-share.bat`：一键启动本地服务、临时 HTTPS 隧道并打开 GitHub Pages，供导师临时访问上传和 API。

批处理文件只负责启动和给出明确报错，不会自动安装 Python 包、Cloudflare 客户端或修改系统设置。

在 PowerShell 中进入本目录并运行：

```powershell
.\start.ps1
```

浏览器访问：

```text
http://127.0.0.1:8765
```

也可直接在命令行提问：

```powershell
python .\agent.py "如何计算 LGPS 的锂离子扩散系数？"
```

本地网页使用 Python 服务后端时，才能打开本地 PDF 和检索全文；GitHub Pages 版只包含论文元数据与规则型问答，不上传 PDF。

RAG 的配置、隐私边界与本机模型示例见 [RAG_SETUP.md](RAG_SETUP.md)。密钥只进入当前启动进程，不写入文件；使用远程模型时，精选元数据和短摘录会离开本机，但 PDF 文件不会被发送。

## 全文库维护

只发现开放获取、作者/课题组公开稿或当前网络合法可访问的出版社 PDF：

```powershell
python .\fetch_literature.py --try-publisher
```

脚本不会登录、保存 Cookie、修改 WOS/Zotero，也不会绕过付费墙。HTML 登录页或权限页不会被当作 PDF。下载后进行离线完整性审计：

```powershell
python .\audit_library.py
```

审计包括 PDF 解析、标题匹配、正文/补充材料区分、SHA-256、重复文件、唯一 DOI/WOS UT 和逐页文本抽取。M3GNet 的补充材料单独保存在 `literature/supplementary/`，不会混入正文索引。

重建索引后，可生成方法设置定位器：

```powershell
python .\extract_method_evidence.py
```

方法信号数与覆盖篇数以 [METHOD_EVIDENCE_AUDIT.md](METHOD_EVIDENCE_AUDIT.md) 为准，新增正文后必须重新抽取。程序排除参考文献区及不属于公开精选库的私有论文，并限制每篇每类最多 3 条；所有结果都标为 `auto_extracted_needs_human_review`。页面中的参数只能帮助你快速跳到原文，不能直接作为 VASP、NEB、AIMD 或 MLIP 的最终设置。

## 2026-09-14 新版

新增 MACE-MP-0（正式发表版2025）、冻结层迁移学习、不确定性量化三篇方法论文。新卡片提供“适用范围与迁移边界”和“代码、数据与复现入口”，并区分原文体系与迁移到电池的建议步骤。

新增可审计标签与检索权重训练：当前 65 篇中，DFT 36 篇、MD 34 篇、VASP 14 篇、MS 7 篇、方法论文 29 篇、进展论文 36 篇。`MS` 专指论文方法明确使用 BIOVIA Materials Studio 的条目，不能根据背景提及误标。标签规则与命中依据在 `data/paper_tags.json`。

网页现在支持 `tag:DFT`、`tag:MD`、`tag:VASP`、`tag:MS`、`type:方法论文` 和 `type:进展论文`。`data/search_training.json` 包含 48 条训练问题和 12 条留出问题；运行 `python train_search.py` 会重新选择字段权重并生成 `data/search_config.json`。当前留出集 MRR@5 为 0.9167、Recall@5 为 0.9583、Top-1 为 0.8333；该小集合做过一次词表错误分析，只适合回归，不是独立泛化基准。这是检索排序调参，不是大模型微调；完整说明见 [SEARCH_TRAINING.md](SEARCH_TRAINING.md)。

## 2026-09-18 工具 Agent 与研究路线更新

新增 PEMD、HiTPoly、氧掺杂 Li6PS5Cl 界面、长程电响应机器学习势和熵驱动训练数据选择 5 篇论文。新增论文、复现顺序、候选课题和学术/工业验证清单见 [电池研究路线图](guides/BATTERY_RESEARCH_ROADMAP_20260918.md)。

本地 `/api/agent` 实现了受限、可审计的模型选工具循环；无模型时明确显示确定性工作流，不把关键词检索伪装成生成式 Agent。如何配置模型、建立评测集和逐步加入 RAG/工具选择见 [工具 Agent 实现说明](guides/AGENT_IMPLEMENTATION_GUIDE.md)。

本轮新增 9 篇电池计算论文：6 篇明确使用 Materials Studio 的电解液、聚合物电解质、人工 SEI、相场多尺度和添加剂案例，另有 1 篇电解液 ReaxFF 参数化论文及 2 篇 SEI/ReaxFF 综述。每条均保存 DOI、作者、期刊、方法证据与核验来源；全文以 [FULLTEXT_AUDIT.md](FULLTEXT_AUDIT.md) 的实际状态为准。

导出全库书目供 Zotero 导入：`python export_ris.py --all-curated`。输出为 `exports/battery_materials_all_curated.ris`，只有实际存在 WOS UT 的16篇会标注WOS核验，其余保留DOI/出版社核验状态。导出不会自动写入Zotero，不含PDF。

前端方法卡回归检查：`node tests/test_learning_ui.mjs`。Python回归检查：`python -m unittest discover -s tests`。

## 入门方法论文集

新增 12 篇“能照着学习和复现”的方法论文，网页数据卡内附建议复现步骤：

- VASPKIT：2025 年 Nature Protocols 逐步协议＋2021 年主软件论文；
- Python/自动化：pymatgen、ASE、atomate2、Materials Project；
- 扩散：IDPP 初始路径和 AIMD 扩散统计误差；
- 电池 DFT：过渡金属正极的 DFT+U 电压；
- AI4S：机器学习势选型、数据和验证实用指南；
- 热力学/后处理：phonopy 与 sumo。

这 12 篇已经核对 DOI、题名、作者、期刊和出版社记录；其 WOS 状态仍不会冒充为“已取得 WOS UT”。本地全文状态以 [FULLTEXT_AUDIT.md](FULLTEXT_AUDIT.md) 为准，书目核验见 [PAPER_AUDIT.md](PAPER_AUDIT.md)。

Ceder et al. 1998 与 Shi et al. 2013 的 PDF 已由用户从有权访问的来源下载并导入 Zotero，随后作为 `user_supplied_zotero_attachment` 纳入本地全文索引。PDF 本身继续由 `.gitignore` 排除，不会上传 GitHub。

## 上传文献与关键词 API

本机启动服务后，网页右上角选择“上传文献”。支持 PDF 正文、标题、DOI、年份、期刊和作者；标题、DOI、年份留空时会尝试从 PDF 元数据或首页识别。单文件上限 50 MiB。

新增文献的元数据写入 `private/user-papers.local.json`，PDF 写入 `literature/pdfs/`，随后更新全文索引。已存在 DOI 会补充原条目，不创建重复记录；已有不同 PDF 时拒绝静默覆盖。

当前保留以下稳定接口，便于以后把内置关键词规则替换成 LLM、KeyBERT 或领域模型，而不改网页调用方式：

| 接口 | 方法 | 用途 |
|---|---|---|
| `/api/capabilities` | GET | 查询上传限制、关键词接口版本和隐私策略 |
| `/api/upload` | POST multipart | 上传 PDF、补充元数据、建立索引并返回关键词 |
| `/api/keywords` | POST JSON | 按 `text` 或 `paper_id` 提取关键词，当前版本 `v1` |
| `/api/chat` | POST JSON | 检索本地证据并回答；配置模型后可用引用校验 RAG，传 `use_rag:false` 可关闭 |
| `/api/agent` | POST JSON | 仅限本机的受限工具 Agent；最多 4 次只读工具动作并校验最终引用 |
| `/api/paper-tags` | GET | 读取标签定义、计数与逐篇标签依据 |
| `/api/search-config` | GET | 读取当前可解释检索权重与训练指标 |

通过公网隧道调用写接口时必须提供 `Authorization: Bearer <临时访问密钥>`。访问密钥不写入 Git 或浏览器持久存储，只保存在当前标签页的 `sessionStorage`。

## Zotero

生成 16 篇已核验记录的 RIS：

```powershell
python .\export_ris.py
```

文件位于 `exports/battery_materials_16_verified.ris`，可由用户在 Zotero 中选择“文件 → 导入”。这是有意设计的人工确认步骤，避免本地 Zotero 自动同步造成线上写入。

如只想读取现有 Zotero 文库并生成深链：

```powershell
python .\sync_zotero_links.py
python .\build_pages.py
```

`sync_zotero_links.py` 只读取本机 Zotero API 的 DOI、条目键和 PDF 附件键，不读取账号密码。导师没有你的本地 Zotero 文库时，应使用网页一直保留的 WOS 或 DOI 入口。

要先预览、再按 DOI 幂等导入当前证据库书目；已有本地 PDF 的核心论文会附加原文，新加入的入门论文先只导入书目：

```powershell
python .\import_zotero_library.py
python .\import_zotero_library.py --apply
python .\sync_zotero_links.py
python .\build_pages.py
```

导入器通过 Zotero 本机 Connector 接口写入，不读取账号密码；已存在 DOI 会跳过，避免重复。新条目统一带 `battery-materials-agent` 与 `WOS-verified` 标签。Zotero 9 无需为此创建 Web API 密钥；若文库开启同步，新增书目和存储型附件可能在下一次同步时上传到 Zotero 云端。

Zotero 10 中，如书目已经存在但缺少 PDF，可在取得并审计正文后运行：

```powershell
python .\attach_zotero_pdf.py --paper-id <论文ID>
```

Zotero 会显示本地写入授权对话框。脚本只给指定 DOI 的既有条目创建存储型 PDF 子附件，授权密钥仅保存在当前进程内，不会打印或写盘；随后重新运行 `sync_zotero_links.py`。

`sync_zotero_links.py` 把条目键和附件键写入被 Git 忽略的 `private/zotero-links.local.json`。本地服务器只向真正的本机页面提供这些深链；即使请求经公网隧道回到 `127.0.0.1`，Host/Origin 双重检查也会阻止 Zotero 键和本地 PDF 外泄。导师端显示 WOS/DOI 入口，你自己的本地页面仍可直接打开 Zotero/PDF。

## GitHub Pages

生成静态发布包：

```powershell
python .\build_pages.py
```

把仓库推送到 GitHub 后，在 `Settings → Pages` 选择 `main` 分支和 `/docs` 文件夹。不要提交 WOS 密码、学校 VPN 信息、Cookie、Zotero 数据库/条目键、受版权保护的 PDF 或全文转储；`.gitignore` 已排除私有 Zotero 映射、PDF、全文 JSONL、RIS 和 Zotero 数据库。静态站只发布书目、短方法信号与页码，不发布论文正文。

### 让导师访问，同时让服务跑在你的电脑上

公开网页固定使用：

```text
https://rua-creeper-233.github.io/battery-materials-agent/
```

导师只浏览种子库和静态问答时，你不需要启动电脑或服务器。若要让导师上传论文、使用刚加入的本地全文或调用关键词 API，需要在你的电脑上建立 HTTPS 隧道：

1. 首次安装 Cloudflare Tunnel 客户端：

   ```powershell
   winget install --id Cloudflare.cloudflared
   ```

2. 在项目目录运行：

   ```powershell
   .\start-share.ps1
   ```

3. 保持该窗口开启。脚本会显示一个临时访问密钥，Cloudflare 随后显示一个 `https://...trycloudflare.com` 地址。
4. 在 GitHub 页面点击“上传文献”，填入隧道地址和临时访问密钥，先点“测试连接”。把同一地址和密钥通过可信渠道发给导师。
5. 使用结束后按 `Ctrl+C`；本地服务、隧道和本次访问密钥随即失效。

GitHub Pages 只托管 HTML/CSS/JavaScript，不能运行 Python。Quick Tunnel 只适合演示和短期协作，地址每次启动都会变化；如果以后需要长期稳定的 API 地址，应准备一个托管在 Cloudflare 的自有域名并建立 named tunnel。无论哪种隧道，当前实现都不允许远程打开本地 PDF 或 Zotero 私有深链。

完整架构、安全边界和逐步操作见 [SHARING_GUIDE.md](SHARING_GUIDE.md)。

为了便于回退，每完成一轮可运行且测试通过的改进，就创建一个独立 Git 提交并推送。`main` 上的提交记录就是版本时间线；需要固定里程碑时可额外创建标签。

## 数据结构

每篇论文可逐步细化为：

- `Publication`：标题、作者、年份、期刊、DOI、WOS UT；
- `MaterialSystem`：组成、结构、工作离子、荷电态、缺陷、界面终止；
- `CalculationProtocol`：泛函、U、赝势、ENCUT、k 点、超胞、磁序、收敛；
- `Thermodynamics`：总能、形成能、凸包能、反应能、电压和相图；
- `Transport`：通道、NEB 势垒、温度、轨迹、MSD、D、σ、Ea 和误差；
- `Interface`：表面、终止、晶格失配、电势参比和反应产物；
- `ModelArtifact`：训练集版本、能量/力/应力标签、切分、模型版本和 OOD 判据；
- `Validation`：实验值、高精度基准、误差、不确定性和失败模式；
- `Provenance`：原文页码/表格/图、抽取时间与人工复核状态。

## 边界

- 这是可审计的检索与工作流代理，不会把检索到的句子自动当作已验证的科学结论；
- 不能运行 VASP，也不包含 VASP 许可证或 PAW 赝势；
- 不能从摘要可靠还原完整计算参数，具体 INCAR/KPOINTS/U/超胞必须回到原文并重新收敛；
- WOS 是检索与引文数据库，不应当作无条件全文仓库；
- 机器学习势不能替代目标体系的 DFT 验证，尤其是新元素、缺陷、界面、反应和极端温压构型。

## 下一步

1. 对 50 篇全文做“方法参数—结果数值—页码/图表”的结构化人工复核，并通过学校机构访问、开放获取或作者公开稿合法补齐其余 2 篇正文；
2. 接入 Materials Project/COD 的结构 ID 与可追溯 CIF；
3. 生成可审查而非自动执行的 VASP 输入草案；
4. 增加 VASP 收敛、NEB 势垒、MSD/D/σ 的结果检查器；
5. 积累 30—50 个真实问题并划分独立测试集，再评估检索；随后在全文证据之上接入受引用约束的 LLM，禁止引用库外虚构来源。
