# 本地全文与证据索引审计

审计时间：2026-09-18T14:20:21+00:00

结论：证据库共 65 篇，DOI/出版社记录已核验 65/65；其中 16 篇核心论文已取得 WOS UT。本地可检索正文 62/65 篇，共 3595 个页级文本块。未下载项不会伪装成全文，会回退到 DOI 页面或已记录的 WOS 入口。

所有保留文件均通过 PDF 解析、标题匹配、正文/补充材料区分、SHA-256 和重复文件检查。M3GNet 的补充材料单独放在 `literature/supplementary/`，不进入正文索引。

| # | 年份 | 论文 | 本地状态 | 页数 | 文本块 | 标题匹配 | 获取依据 |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 2026 | PEMD: a high-throughput simulation and analysis framework for solid polymer electrolytes | 已下载正文 | 10 | 35 | 1.0 | 已核验来源 |
| 2 | 2026 | Computational discovery of polymer electrolytes with Bayesian optimization and high-throughput molecular dynamics simulations | 已下载正文 | 28 | 41 | 1.0 | curated_public_source |
| 3 | 2026 | Enhanced Ionic Conductivity at the Solid Electrolyte Interphase of Oxygen-Doped Li6PS5Cl | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 4 | 2025 | Machine learning interatomic potential can infer electrical response | 已下载正文 | 11 | 44 | 1.0 | curated_public_source |
| 5 | 2025 | Information-entropy-driven generation of material-agnostic datasets for machine-learning interatomic potentials | 已下载正文 | 17 | 63 | 1.0 | curated_public_source |
| 6 | 2018 | Machine learning for molecular and materials science | 已下载正文 | 9 | 49 | 1.0 | user_existing_Zotero_attachment |
| 7 | 2026 | Machine learning force field molecular dynamics simulation of SEI formation on lithium metal | 已下载正文 | 31 | 45 | 1.0 | user_existing_Zotero_attachment |
| 8 | 2019 | Graph dynamical networks for unsupervised learning of atomic scale dynamics in materials | 已下载正文 | 9 | 37 | 1.0 | curated_public_source |
| 9 | 2022 | Accelerating amorphous polymer electrolyte screening by learning to reduce errors in molecular dynamics simulated properties | 已下载正文 | 10 | 45 | 1.0 | curated_public_source |
| 10 | 2023 | Design principles for sodium superionic conductors | 已下载正文 | 9 | 37 | 1.0 | curated_public_source |
| 11 | 2017 | Origin of fast ion diffusion in super-ionic conductors | 已下载正文 | 7 | 25 | 1.0 | vetted_public_author_or_repository_copy |
| 12 | 2020 | Low-temperature paddlewheel effect in glassy solid electrolytes | 已下载正文 | 11 | 52 | 1.0 | vetted_public_author_or_repository_copy |
| 13 | 2023 | Design principles for NASICON super-ionic conductors | 已下载正文 | 11 | 42 | 1.0 | vetted_public_author_or_repository_copy |
| 14 | 2016 | Computational understanding of Li-ion batteries | 已下载正文 | 13 | 63 | 1.0 | openalex_open_access_pdf |
| 15 | 1997 | Ab initio study of lithium intercalation in metal oxides and metal dichalcogenides | 已下载正文 | 12 | 40 | 1.0 | vetted_public_author_or_repository_copy |
| 16 | 1998 | Identification of cathode materials for lithium batteries guided by first-principles calculations | 已下载正文 | 3 | 15 | 0.889 | user_supplied_authorized_copy |
| 17 | 2001 | First-principles theory of ionic diffusion with nondilute carriers | 已下载正文 | 17 | 61 | 1.0 | vetted_public_author_or_repository_copy |
| 18 | 2011 | Voltage, stability and diffusion barrier differences between sodium-ion and lithium-ion intercalation materials | 已下载正文 | 9 | 37 | 1.0 | vetted_public_author_or_repository_copy |
| 19 | 2013 | Phase stability, electrochemical stability and ionic conductivity of the Li10±1MP2X12 family of superionic conductors | 已下载正文 | 9 | 33 | 1.0 | vetted_public_author_or_repository_copy |
| 20 | 2013 | Defect Thermodynamics and Diffusion Mechanisms in Li2CO3 and Implications for the Solid Electrolyte Interphase in Li-Ion Batteries | 已下载正文 | 15 | 66 | 0.9 | user_supplied_zotero_attachment |
| 21 | 2017 | Holistic computational structure screening of more than 12,000 candidates for solid lithium-ion conductor materials | 已下载正文 | 15 | 59 | 1.0 | vetted_public_author_or_repository_copy |
| 22 | 2020 | Diffusion of lithium ions in Lithium-argyrodite solid-state electrolytes | 已下载正文 | 10 | 45 | 1.0 | openalex_open_access_pdf |
| 23 | 2022 | A universal graph deep learning interatomic potential for the periodic table | 已下载正文 | 58 | 92 | 1.0 | vetted_public_author_or_repository_copy |
| 24 | 2024 | High-throughput investigation of stability and Li diffusion of doped solid electrolytes via neural network potential without configurational knowledge | 已下载正文 | 8 | 23 | 1.0 | open_access_landing_page |
| 25 | 2022 | A review of the recent progress in battery informatics | 已下载正文 | 22 | 108 | 1.0 | openalex_open_access_pdf |
| 26 | 2000 | A climbing image nudged elastic band method for finding saddle points and minimum energy paths | 已下载正文 | 8 | 30 | 0.917 | vetted_public_author_or_repository_copy |
| 27 | 2010 | Ab initio molecular dynamics simulations of the initial stages of solid-electrolyte interphase formation on lithium ion battery graphitic anodes | 已下载正文 | 5 | 15 | 1.0 | openalex_open_access_pdf |
| 28 | 2012 | First Principles Study of the Li10GeP2S12 Lithium Super Ionic Conductor Material | 已下载正文 | 3 | 12 | 0.889 | vetted_public_author_or_repository_copy |
| 29 | 2023 | CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling | 已下载正文 | 11 | 44 | 1.0 | openalex_open_access_pdf |
| 30 | 2025 | Empowering materials science with VASPKIT: a toolkit for enhanced simulation and analysis | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 31 | 2021 | VASPKIT: A user-friendly interface facilitating high-throughput computing and analysis using VASP code | 已下载正文 | 33 | 77 | 1.0 | vetted_public_author_or_repository_copy |
| 32 | 2013 | Python Materials Genomics (pymatgen): A robust, open-source python library for materials analysis | 已下载正文 | 6 | 26 | 1.0 | vetted_public_author_or_repository_copy |
| 33 | 2017 | The atomic simulation environment—a Python library for working with atoms | 已下载正文 | 60 | 119 | 1.0 | vetted_public_author_or_repository_copy |
| 34 | 2025 | Atomate2: modular workflows for materials science | 已下载正文 | 73 | 118 | 1.0 | vetted_public_author_or_repository_copy |
| 35 | 2013 | Commentary: The Materials Project: A materials genome approach to accelerating materials innovation | 已下载正文 | 12 | 27 | 1.0 | vetted_open_licensed_redistribution_copy |
| 36 | 2014 | Improved initial guess for minimum energy path calculations | 已下载正文 | 14 | 21 | 1.0 | vetted_public_author_or_repository_copy |
| 37 | 2018 | Statistical variances of diffusional properties from ab initio molecular dynamics simulations | 已下载正文 | 9 | 40 | 1.0 | vetted_public_author_or_repository_copy |
| 38 | 2004 | First-principles prediction of redox potentials in transition-metal compounds with LDA+U | 已下载正文 | 21 | 33 | 1.0 | vetted_public_author_or_repository_copy |
| 39 | 2025 | A practical guide to machine learning interatomic potentials – Status and future | 已下载正文 | 83 | 165 | 1.0 | vetted_public_author_or_repository_copy |
| 40 | 2015 | First principles phonon calculations in materials science | 已下载正文 | 6 | 21 | 1.0 | vetted_public_author_or_repository_copy |
| 41 | 2018 | sumo: Command-line tools for plotting and analysis of periodic ab initio calculations | 已下载正文 | 3 | 6 | 1.0 | vetted_public_author_or_repository_copy |
| 42 | 2018 | DeePMD-kit: A deep learning package for many-body potential energy representation and molecular dynamics | 已下载正文 | 22 | 35 | 1.0 | vetted_public_author_or_repository_copy |
| 43 | 2020 | DP-GEN: A concurrent learning platform for the generation of reliable deep learning based potential energy models | 已下载正文 | 29 | 48 | 1.0 | vetted_public_author_or_repository_copy |
| 44 | 2022 | E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials | 已下载正文 | 11 | 54 | 0.889 | vetted_public_author_or_repository_copy |
| 45 | 2023 | Learning local equivariant representations for large-scale atomistic dynamics | 已下载正文 | 15 | 65 | 1.0 | vetted_public_author_or_repository_copy |
| 46 | 2021 | Gaussian Process Regression for Materials and Molecules | 已下载正文 | 87 | 278 | 1.0 | vetted_public_author_or_repository_copy |
| 47 | 2022 | LAMMPS - a flexible simulation tool for particle-based materials modeling at the atomic, meso, and continuum scales | 已下载正文 | 34 | 169 | 0.917 | vetted_open_licensed_redistribution_copy |
| 48 | 2016 | AiiDA: automated interactive infrastructure and database for computational science | 已下载正文 | 30 | 61 | 1.0 | vetted_public_author_or_repository_copy |
| 49 | 2020 | DScribe: Library of descriptors for machine learning in materials science | 已下载正文 | 17 | 55 | 1.0 | vetted_public_author_or_repository_copy |
| 50 | 2018 | Crystal Graph Convolutional Neural Networks for an Accurate and Interpretable Prediction of Material Properties | 已下载正文 | 15 | 33 | 1.0 | vetted_public_author_or_repository_copy |
| 51 | 2020 | Benchmarking materials property prediction methods: the Matbench test set and Automatminer reference algorithm | 已下载正文 | 10 | 45 | 1.0 | vetted_public_author_or_repository_copy |
| 52 | 2010 | Thermodynamic and kinetic properties of the Li-graphite system from first-principles calculations | 已下载正文 | 9 | 34 | 1.0 | vetted_public_author_or_repository_copy |
| 53 | 2024 | pymatgen-analysis-defects: A Python package for analyzing point defects in crystalline materials | 已下载正文 | 4 | 8 | 1.0 | vetted_public_author_or_repository_copy |
| 54 | 2025 | A foundation model for atomistic materials chemistry | 已下载正文 | 153 | 324 | 1.0 | vetted_public_author_or_repository_copy |
| 55 | 2025 | Fine-tuning foundation models of materials interatomic potentials with frozen transfer learning | 已下载正文 | 11 | 46 | 1.0 | vetted_public_author_or_repository_copy |
| 56 | 2025 | Uncertainty quantification for neural network potential foundation models | 已下载正文 | 8 | 31 | 0.857 | vetted_public_author_or_repository_copy |
| 57 | 2023 | Effect of the Electric Double Layer (EDL) in Multicomponent Electrolyte Reduction and Solid Electrolyte Interphase (SEI) Formation in Lithium Batteries | 已下载正文 | 12 | 50 | 1.0 | official_open_access_pdf_via_user_authorized_xjtu_access |
| 58 | 2024 | Unraveling the Hydrolysis Mechanism of LiPF6 in Electrolyte of Lithium Ion Batteries | 已下载正文 | 8 | 25 | 0.857 | user_authorized_xjtu_institutional_access |
| 59 | 2024 | A polymeric artificial solid electrolyte interface dramatically enhances lithium-ion transport | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 60 | 2025 | Reactivity of Carbonyl-Containing Solid Polymer Electrolytes in Lithium–Metal Batteries from First-Principles Molecular Dynamics | 已下载正文 | 11 | 40 | 1.0 | vetted_public_author_or_repository_copy |
| 61 | 2025 | Simulating solid electrolyte interphase formation spanning 10^8 time scales with an atomically informed phase-field model | 已下载正文 | 14 | 53 | 1.0 | official_open_access_pdf_after_user_completed_rsc_security_verification |
| 62 | 2025 | De-solvation of heteroalkali cations enabling stable solid electrolyte interphase for dendrite-free lithium metal batteries | 已下载正文 | 30 | 57 | 1.0 | vetted_public_author_or_repository_copy |
| 63 | 2020 | Lithium-electrolyte solvation and reaction in the electrolyte of a lithium ion battery: A ReaxFF reactive force field study | 已下载正文 | 15 | 38 | 1.0 | user_authorized_xjtu_institutional_access |
| 64 | 2018 | Review on modeling of the anode solid electrolyte interphase (SEI) for lithium-ion batteries | 已下载正文 | 26 | 113 | 1.0 | vetted_public_author_or_repository_copy |
| 65 | 2021 | Application of Reaction Force Field Molecular Dynamics in Lithium Batteries | 已下载正文 | 5 | 22 | 1.0 | openalex_open_access_pdf |

## 尚未保存的正文

- Enhanced Ionic Conductivity at the Solid Electrolyte Interphase of Oxygen-Doped Li6PS5Cl，DOI `10.1002/advs.76563`：本地未保存正文，使用 WOS/DOI 回退。
- Empowering materials science with VASPKIT: a toolkit for enhanced simulation and analysis，DOI `10.1038/s41596-025-01160-w`：本地未保存正文，使用 WOS/DOI 回退。
- A polymeric artificial solid electrolyte interface dramatically enhances lithium-ion transport，DOI `10.1039/d4cc03688c`：本地未保存正文，使用 WOS/DOI 回退。

## 使用边界

本地全文命中是定位原文页码的入口，不自动等于经过人工复核的科学结论。涉及具体计算参数、数值或因果判断时，仍应回到对应页、图、表与补充材料核对。
