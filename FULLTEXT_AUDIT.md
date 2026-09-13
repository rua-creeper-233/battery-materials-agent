# 本地全文与证据索引审计

审计时间：2026-09-13T07:59:11+00:00

结论：16 篇种子论文和 WOS UT 均已核验；本地可检索正文 16/16 篇，共 743 个页级文本块。未下载项不会伪装成全文，会回退到精确 WOS 记录和 DOI 页面。

所有保留文件均通过 PDF 解析、标题匹配、正文/补充材料区分、SHA-256 和重复文件检查。M3GNet 的补充材料单独放在 `literature/supplementary/`，不进入正文索引。

| # | 年份 | 论文 | 本地状态 | 页数 | 文本块 | 标题匹配 | 获取依据 |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 2016 | Computational understanding of Li-ion batteries | 已下载正文 | 13 | 63 | 1.0 | openalex_open_access_pdf |
| 2 | 1997 | Ab initio study of lithium intercalation in metal oxides and metal dichalcogenides | 已下载正文 | 12 | 40 | 1.0 | vetted_public_author_or_repository_copy |
| 3 | 1998 | Identification of cathode materials for lithium batteries guided by first-principles calculations | 已下载正文 | 3 | 15 | 0.889 | user_supplied_zotero_attachment |
| 4 | 2001 | First-principles theory of ionic diffusion with nondilute carriers | 已下载正文 | 17 | 61 | 1.0 | vetted_public_author_or_repository_copy |
| 5 | 2011 | Voltage, stability and diffusion barrier differences between sodium-ion and lithium-ion intercalation materials | 已下载正文 | 9 | 37 | 1.0 | vetted_public_author_or_repository_copy |
| 6 | 2013 | Phase stability, electrochemical stability and ionic conductivity of the Li10±1MP2X12 family of superionic conductors | 已下载正文 | 9 | 33 | 1.0 | vetted_public_author_or_repository_copy |
| 7 | 2013 | Defect Thermodynamics and Diffusion Mechanisms in Li2CO3 and Implications for the Solid Electrolyte Interphase in Li-Ion Batteries | 已下载正文 | 15 | 66 | 0.9 | user_supplied_zotero_attachment |
| 8 | 2017 | Holistic computational structure screening of more than 12,000 candidates for solid lithium-ion conductor materials | 已下载正文 | 15 | 59 | 1.0 | vetted_public_author_or_repository_copy |
| 9 | 2020 | Diffusion of lithium ions in Lithium-argyrodite solid-state electrolytes | 已下载正文 | 10 | 45 | 1.0 | openalex_open_access_pdf |
| 10 | 2022 | A universal graph deep learning interatomic potential for the periodic table | 已下载正文 | 58 | 92 | 1.0 | vetted_public_author_or_repository_copy |
| 11 | 2024 | High-throughput investigation of stability and Li diffusion of doped solid electrolytes via neural network potential without configurational knowledge | 已下载正文 | 8 | 23 | 1.0 | open_access_landing_page |
| 12 | 2022 | A review of the recent progress in battery informatics | 已下载正文 | 22 | 108 | 1.0 | openalex_open_access_pdf |
| 13 | 2000 | A climbing image nudged elastic band method for finding saddle points and minimum energy paths | 已下载正文 | 8 | 30 | 0.917 | vetted_public_author_or_repository_copy |
| 14 | 2010 | Ab initio molecular dynamics simulations of the initial stages of solid-electrolyte interphase formation on lithium ion battery graphitic anodes | 已下载正文 | 5 | 15 | 1.0 | openalex_open_access_pdf |
| 15 | 2012 | First Principles Study of the Li10GeP2S12 Lithium Super Ionic Conductor Material | 已下载正文 | 3 | 12 | 0.889 | vetted_public_author_or_repository_copy |
| 16 | 2023 | CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling | 已下载正文 | 11 | 44 | 1.0 | openalex_open_access_pdf |

## 尚未保存的正文

当前 16 篇种子论文均已有经校验的本地正文。

## 使用边界

本地全文命中是定位原文页码的入口，不自动等于经过人工复核的科学结论。涉及具体计算参数、数值或因果判断时，仍应回到对应页、图、表与补充材料核对。
