# 43 篇论文真实性与分级核验

核验日期：2026-09-14（新增3篇；既有40篇保留原核验记录）

结论：当前 43 条均已核对 DOI 与出版社/正式期刊记录。原有 16 篇核心论文还在华南师范大学机构会话下以 DOI 精确检索过 Web of Science Core Collection，并取得 16/16 个唯一 UT；其余 27 篇方法路线论文没有冒充为 WOS 已核验，状态明确记录为 `not_checked`。这里的书目核验不代表出版社 PDF 都可无条件下载。

## 2026-09-14 新增：预训练、微调和不确定性

| 论文 | DOI / 正式记录 | 学习用途 |
|---|---|---|
| Batatia et al., 2025. A foundation model for atomistic materials chemistry | [JCP](https://doi.org/10.1063/5.0297006)，[作者预印本](https://arxiv.org/abs/2401.00096) | MACE-MP-0推理、MD与目标域验证 |
| Radova et al., 2025. Fine-tuning foundation models of materials interatomic potentials with frozen transfer learning | [出版社](https://www.nature.com/articles/s41524-025-01727-x) | 小数据、冻结层、学习曲线对照 |
| Bilbrey et al., 2025. Uncertainty quantification for neural network potential foundation models | [出版社](https://www.nature.com/articles/s41524-025-01572-y)，[作者代码](https://github.com/pnnl/SNAP) | 不确定性校准、过度自信与主动学习 |

新增三篇均逐项对照Crossref的题名、完整作者名单、年份、期刊和DOI。方法卡中的复现步骤为本库整理，不是已执行的复现结果。后两篇的原文案例不是锂电池，不把跨体系迁移当成已经验证的结论。

## 核心论文：16 篇 DOI＋WOS UT 已核验

| # | 年份 | 简称 | DOI | WOS UT |
|---:|---:|---|---|---|
| 1 | 2016 | Urban：Computational understanding of Li-ion batteries | [10.1038/npjcompumats.2016.2](https://doi.org/10.1038/npjcompumats.2016.2) | `WOS:000426821500008` |
| 2 | 1997 | Aydinol：Ab initio lithium intercalation | [10.1103/PhysRevB.56.1354](https://doi.org/10.1103/PhysRevB.56.1354) | `WOS:A1997XM76600066` |
| 3 | 1998 | Ceder：First-principles-guided cathode identification | [10.1038/33647](https://doi.org/10.1038/33647) | `WOS:000073129000051` |
| 4 | 2001 | Van der Ven：Ionic diffusion with nondilute carriers | [10.1103/PhysRevB.64.184307](https://doi.org/10.1103/PhysRevB.64.184307) | `WOS:000172239400054` |
| 5 | 2011 | Ong：Li/Na voltage, stability and barriers | [10.1039/C1EE01782A](https://doi.org/10.1039/C1EE01782A) | `WOS:000294306900068` |
| 6 | 2013 | Ong：Li10±1MP2X12 superionic conductors | [10.1039/C2EE23355J](https://doi.org/10.1039/C2EE23355J) | `WOS:000312337700019` |
| 7 | 2013 | Shi：Li2CO3 defects and SEI diffusion | [10.1021/jp310591u](https://doi.org/10.1021/jp310591u) | `WOS:000318536600001` |
| 8 | 2017 | Sendek：12,831 solid conductor candidates | [10.1039/C6EE02697D](https://doi.org/10.1039/C6EE02697D) | `WOS:000395208000028` |
| 9 | 2020 | Baktash：Li-argyrodite diffusion | [10.1038/s41524-020-00432-1](https://doi.org/10.1038/s41524-020-00432-1) | `WOS:000584639000001` |
| 10 | 2022 | Chen：M3GNet universal potential | [10.1038/s43588-022-00349-3](https://doi.org/10.1038/s43588-022-00349-3) | `WOS:000890324500016` |
| 11 | 2024 | Sawada：NNP screening of doped solid electrolytes | [10.1038/s41598-024-62054-7](https://doi.org/10.1038/s41598-024-62054-7) | `WOS:001229023500115` |
| 12 | 2022 | Ling：Battery informatics review | [10.1038/s41524-022-00713-x](https://doi.org/10.1038/s41524-022-00713-x) | `WOS:000757839700001` |
| 13 | 2000 | Henkelman：CI-NEB | [10.1063/1.1329672](https://doi.org/10.1063/1.1329672) | `WOS:000165584900005` |
| 14 | 2010 | Leung：Initial SEI AIMD | [10.1039/B925853A](https://doi.org/10.1039/B925853A) | `WOS:000278824400004` |
| 15 | 2012 | Mo：LGPS first-principles study | [10.1021/cm203303y](https://doi.org/10.1021/cm203303y) | `WOS:000298908400006` |
| 16 | 2023 | Deng：CHGNet | [10.1038/s42256-023-00716-3](https://doi.org/10.1038/s42256-023-00716-3) | `WOS:001085170400007` |

本地全文的来源、页数、哈希与缺失项另见 [FULLTEXT_AUDIT.md](FULLTEXT_AUDIT.md)。当前核心正文为 16/16；新增方法论文尚未保存的正文仍提供 DOI/出版社回退，不会被系统伪装成已有全文或 WOS 已核验。

## 第一批入门方法论文：12 篇 DOI＋出版社记录已核验

| # | 年份 | 用途 | 论文 | DOI | 核验入口 |
|---:|---:|---|---|---|---|
| 17 | 2025 | VASPKIT逐步协议 | Empowering materials science with VASPKIT | [10.1038/s41596-025-01160-w](https://doi.org/10.1038/s41596-025-01160-w) | [Nature Protocols](https://www.nature.com/articles/s41596-025-01160-w) |
| 18 | 2021 | VASPKIT功能与示例 | VASPKIT: A user-friendly interface… | [10.1016/j.cpc.2021.108033](https://doi.org/10.1016/j.cpc.2021.108033) | [Computer Physics Communications](https://www.sciencedirect.com/science/article/pii/S0010465521001454) |
| 19 | 2013 | pymatgen与电池相图 | Python Materials Genomics (pymatgen)… | [10.1016/j.commatsci.2012.10.028](https://doi.org/10.1016/j.commatsci.2012.10.028) | [Computational Materials Science](https://www.sciencedirect.com/science/article/pii/S0927025612006295) |
| 20 | 2017 | ASE结构、MD与NEB | The atomic simulation environment… | [10.1088/1361-648X/aa680e](https://doi.org/10.1088/1361-648X/aa680e) | [IOP](https://doi.org/10.1088/1361-648X/aa680e) |
| 21 | 2025 | atomate2可复现工作流 | Atomate2: modular workflows for materials science | [10.1039/D5DD00019J](https://doi.org/10.1039/D5DD00019J) | [Digital Discovery](https://pubs.rsc.org/en/content/articlelanding/2025/dd/d5dd00019j) |
| 22 | 2013 | Materials Project数据来源 | Commentary: The Materials Project… | [10.1063/1.4812323](https://doi.org/10.1063/1.4812323) | [APL Materials](https://doi.org/10.1063/1.4812323) |
| 23 | 2014 | IDPP-NEB初始路径 | Improved initial guess for minimum energy path calculations | [10.1063/1.4878664](https://doi.org/10.1063/1.4878664) | [Journal of Chemical Physics](https://doi.org/10.1063/1.4878664) |
| 24 | 2018 | AIMD扩散统计流程 | Statistical variances of diffusional properties… | [10.1038/s41524-018-0074-y](https://doi.org/10.1038/s41524-018-0074-y) | [npj Computational Materials](https://www.nature.com/articles/s41524-018-0074-y) |
| 25 | 2004 | 正极电压与DFT+U | First-principles prediction of redox potentials… | [10.1103/PhysRevB.70.235121](https://doi.org/10.1103/PhysRevB.70.235121) | [Physical Review B](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.70.235121) |
| 26 | 2025 | MLIP实用选型指南 | A practical guide to machine learning interatomic potentials… | [10.1016/j.cossms.2025.101214](https://doi.org/10.1016/j.cossms.2025.101214) | [作者公开稿](https://arxiv.org/abs/2503.09814) |
| 27 | 2015 | phonopy与声子热力学 | First principles phonon calculations in materials science | [10.1016/j.scriptamat.2015.07.021](https://doi.org/10.1016/j.scriptamat.2015.07.021) | [Scripta Materialia](https://doi.org/10.1016/j.scriptamat.2015.07.021) |
| 28 | 2018 | VASP能带/DOS后处理 | sumo: Command-line tools for plotting… | [10.21105/joss.00717](https://doi.org/10.21105/joss.00717) | [JOSS](https://joss.theoj.org/papers/10.21105/joss.00717) |

## 第二批方法与进阶论文：12 篇 DOI＋出版社记录已核验

| # | 年份 | 用途 | 论文 | DOI | 核验入口 |
|---:|---:|---|---|---|---|
| 29 | 2018 | Deep Potential训练与MD | DeePMD-kit: A deep learning package… | [10.1016/j.cpc.2018.03.016](https://doi.org/10.1016/j.cpc.2018.03.016) | [Computer Physics Communications](https://www.sciencedirect.com/science/article/pii/S0010465518300882) |
| 30 | 2020 | 主动学习生成势函数数据 | DP-GEN: A concurrent learning platform… | [10.1016/j.cpc.2020.107206](https://doi.org/10.1016/j.cpc.2020.107206) | [Computer Physics Communications](https://www.sciencedirect.com/science/article/pii/S001046552030045X) |
| 31 | 2022 | 等变势与锂扩散 | E(3)-equivariant graph neural networks… | [10.1038/s41467-022-29939-5](https://doi.org/10.1038/s41467-022-29939-5) | [Nature Communications](https://www.nature.com/articles/s41467-022-29939-5) |
| 32 | 2023 | 大规模局域等变MD | Learning local equivariant representations… | [10.1038/s41467-023-36329-y](https://doi.org/10.1038/s41467-023-36329-y) | [Nature Communications](https://www.nature.com/articles/s41467-023-36329-y) |
| 33 | 2021 | GPR/GAP系统入门 | Gaussian Process Regression for Materials and Molecules | [10.1021/acs.chemrev.1c00022](https://doi.org/10.1021/acs.chemrev.1c00022) | [Chemical Reviews](https://pubs.acs.org/doi/10.1021/acs.chemrev.1c00022) |
| 34 | 2022 | 经典与机器学习势MD | LAMMPS - a flexible simulation tool… | [10.1016/j.cpc.2021.108171](https://doi.org/10.1016/j.cpc.2021.108171) | [Computer Physics Communications](https://www.sciencedirect.com/science/article/pii/S0010465521002836) |
| 35 | 2016 | 可追溯计算工作流 | AiiDA: automated interactive infrastructure… | [10.1016/j.commatsci.2015.09.013](https://doi.org/10.1016/j.commatsci.2015.09.013) | [Computational Materials Science](https://www.sciencedirect.com/science/article/pii/S0927025615005820) |
| 36 | 2020 | SOAP等结构描述符 | DScribe: Library of descriptors… | [10.1016/j.cpc.2019.106949](https://doi.org/10.1016/j.cpc.2019.106949) | [Computer Physics Communications](https://www.sciencedirect.com/science/article/pii/S0010465519303042) |
| 37 | 2018 | 晶体图神经网络基线 | Crystal Graph Convolutional Neural Networks… | [10.1103/PhysRevLett.120.145301](https://doi.org/10.1103/PhysRevLett.120.145301) | [Physical Review Letters](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.120.145301) |
| 38 | 2020 | 材料机器学习标准评测 | Benchmarking materials property prediction methods… | [10.1038/s41524-020-00406-3](https://doi.org/10.1038/s41524-020-00406-3) | [npj Computational Materials](https://www.nature.com/articles/s41524-020-00406-3) |
| 39 | 2010 | 石墨负极热力学与动力学 | Thermodynamic and kinetic properties of the Li-graphite system… | [10.1103/PhysRevB.82.125416](https://doi.org/10.1103/PhysRevB.82.125416) | [Physical Review B](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.82.125416) |
| 40 | 2024 | 晶体点缺陷工作流 | pymatgen-analysis-defects… | [10.21105/joss.05941](https://doi.org/10.21105/joss.05941) | [JOSS](https://joss.theoj.org/papers/10.21105/joss.05941) |

## “已核验”不等于什么

- 不等于 40 篇都可以免费获得出版社 PDF；全文权限取决于开放获取、作者公开稿或学校订阅。
- 不等于每篇都是任何具体问题的唯一最佳论文；它们是覆盖电压、扩散、界面、固态电解质、高通量和机器学习势的首批方法学语料。
- 不等于摘要和正文中的结论已经复现；计算参数与数值仍需从原文、补充信息和实际复算中验证。
