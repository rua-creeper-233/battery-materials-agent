# 电池材料计算科研子智能体

面向 DFT / VASP、NEB、AIMD、机器学习势和电池材料计算的本地、证据优先科研助手。它不是有机太阳能电池智能体：OSC 论文只提供了“文献数据集＋科研问答”的方法启发，知识库已经完全换成电池材料计算。

## 当前可用能力

- 16 篇代表性种子论文全部完成 DOI 与 WOS Core Collection 核验，并保存唯一 WOS UT；
- 14/16 篇已有合法可访问的本地正文，共 662 个带页码文本块；
- 中文检索电压、稳定性、扩散、固态电解质、界面、高通量和机器学习势；
- 回答中给出论文级证据、DOI、精确 WOS 记录和本地全文页码；
- 为 DFT / NEB / AIMD / MLIP 任务生成带质量控制项的工作流；
- 从本地正文中自动定位软件、泛函、截断能、k 点、超胞、MD 条件、NEB 和机器学习训练信号，并逐条保留 PDF 页码；
- 本地有 PDF 时显示“打开本地 PDF”，没有时回退到 WOS 与 DOI；
- 可生成 Zotero 可导入的 RIS，但不会自动改动或同步 Zotero 文库。

全文状态与审计证据见 [FULLTEXT_AUDIT.md](FULLTEXT_AUDIT.md)，自动方法信号见 [METHOD_EVIDENCE_AUDIT.md](METHOD_EVIDENCE_AUDIT.md)，书目真实性和 WOS UT 见 [PAPER_AUDIT.md](PAPER_AUDIT.md)。

## 启动

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

当前结果包含 115 条信号，覆盖 14 篇本地正文。程序会排除参考文献区，并限制每篇每类最多 3 条；所有结果都标为 `auto_extracted_needs_human_review`。页面中的参数只能帮助你快速跳到原文，不能直接作为 VASP、NEB、AIMD 或 MLIP 的最终设置。

当前尚未保存本地正文的两篇：

- Ceder et al. 1998，DOI `10.1038/33647`：书目及高校公开页面已确认，但本地下载链路被远端拒绝；
- Shi et al. 2013，DOI `10.1021/jp310591u`：出版社为订阅访问。

两者在网页中保留精确 WOS/DOI 入口。

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

## GitHub Pages

生成静态发布包：

```powershell
python .\build_pages.py
```

把仓库推送到 GitHub 后，在 `Settings → Pages` 选择 `main` 分支和 `/docs` 文件夹。不要提交 WOS 密码、学校 VPN 信息、Cookie、Zotero 数据库、受版权保护的 PDF 或全文转储；`.gitignore` 已排除 PDF、全文 JSONL、RIS 和 Zotero 数据库。静态站只发布书目、短方法信号与页码，不发布论文正文。

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

1. 对 14 篇全文做“方法参数—结果数值—页码/图表”的结构化人工复核；
2. 接入 Materials Project/COD 的结构 ID 与可追溯 CIF；
3. 生成可审查而非自动执行的 VASP 输入草案；
4. 增加 VASP 收敛、NEB 势垒、MSD/D/σ 的结果检查器；
5. 在全文证据之上接入受引用约束的 LLM，禁止引用库外虚构来源。
