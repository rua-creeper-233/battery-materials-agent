# 本地全文与证据索引审计

审计时间：2026-10-07T22:19:30+00:00

结论：证据库共 176 篇，DOI/出版社记录已核验 176/176；其中 16 篇核心论文已取得 WOS UT。本地可检索正文 128/176 篇，共 6858 个页级文本块。未下载项不会伪装成全文，会回退到 DOI 页面或已记录的 WOS 入口。

所有保留文件均通过 PDF 解析、标题匹配、正文/补充材料区分、SHA-256 和重复文件检查。M3GNet 的补充材料单独放在 `literature/supplementary/`，不进入正文索引。

| # | 年份 | 论文 | 本地状态 | 页数 | 文本块 | 标题匹配 | 获取依据 |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 2026 | PEMD: a high-throughput simulation and analysis framework for solid polymer electrolytes | 已下载正文 | 10 | 35 | 1.0 | 已核验来源 |
| 2 | 2026 | Computational discovery of polymer electrolytes with Bayesian optimization and high-throughput molecular dynamics simulations | 已下载正文 | 28 | 41 | 1.0 | curated_public_source |
| 3 | 2026 | Enhanced Ionic Conductivity at the Solid Electrolyte Interphase of Oxygen-Doped Li6PS5Cl | 已下载正文 | 14 | 54 | 0.889 | user_supplied_authorized_copy |
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
| 26 | 2000 | A climbing image nudged elastic band method for finding saddle points and minimum energy paths | 已下载正文 | 4 | 17 | 1.0 | curated_public_source |
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
| 66 | 1993 | Ab initio molecular dynamics for liquid metals | 已下载正文 | 4 | 13 | 1.0 | public_aps_fulltext |
| 67 | 1994 | Ab initio molecular-dynamics simulation of the liquid-metal–amorphous-semiconductor transition in germanium | 已下载正文 | 21 | 57 | 1.0 | public_aps_fulltext |
| 68 | 1996 | Efficiency of ab-initio total energy calculations for metals and semiconductors using a plane-wave basis set | 已下载正文 | 36 | 99 | 1.0 | curated_public_source |
| 69 | 1994 | Projector-augmented-wave method | 已下载正文 | 46 | 65 | 0.0 | curated_public_source |
| 70 | 1999 | From ultrasoft pseudopotentials to the projector augmented-wave method | 已下载正文 | 18 | 66 | 1.0 | public_aps_fulltext |
| 71 | 1996 | Generalized Gradient Approximation Made Simple | 已下载正文 | 5 | 14 | 1.0 | curated_public_source |
| 72 | 1998 | Electron-energy-loss spectra and the structural stability of nickel oxide: An LSDA+U study | 已下载正文 | 5 | 16 | 1.0 | public_aps_fulltext |
| 73 | 2003 | Hybrid functionals based on a screened Coulomb potential | 已下载正文 | 104 | 105 | 0.833 | curated_public_source |
| 74 | 2010 | A consistent and accurate ab initio parametrization of density functional dispersion correction (DFT-D) for the 94 elements H-Pu | 已下载正文 | 20 | 79 | 1.0 | institutional_proxy_download |
| 75 | 1976 | Special points for Brillouin-zone integrations | 已下载正文 | 5 | 12 | 1.0 | public_aps_fulltext |
| 76 | 1989 | High-precision sampling for Brillouin-zone integration in metals | 已下载正文 | 6 | 20 | 1.0 | public_aps_fulltext |
| 77 | 2000 | Improved tangent estimate in the nudged elastic band method for finding minimum energy paths and saddle points | 已下载正文 | 8 | 30 | 1.0 | curated_public_source |
| 78 | 2006 | A fast and robust algorithm for Bader decomposition of charge density | 已下载正文 | 7 | 24 | 1.0 | curated_public_source |
| 79 | 1997 | Maximally localized generalized Wannier functions for composite energy bands | 已下载正文 | 22 | 69 | 1.0 | openalex_open_access_pdf |
| 80 | 2007 | Generalized neural-network representation of high-dimensional potential-energy surfaces | 已下载正文 | 4 | 15 | 1.0 | curated_public_source |
| 81 | 2011 | Atom-centered symmetry functions for constructing high-dimensional neural network potentials | 已下载正文 | 14 | 46 | 1.0 | institutional_proxy_download |
| 82 | 2010 | Gaussian Approximation Potentials: Accuracy of Quantum Mechanics, without the Electrons | 已下载正文 | 10 | 22 | 1.0 | openalex_open_access_pdf |
| 83 | 2015 | Spectral neighbor analysis method for automated generation of quantum-accurate interatomic potentials | 已下载正文 | 32 | 50 | 1.0 | openalex_open_access_pdf |
| 84 | 2018 | Deep Potential Molecular Dynamics: A Scalable Model with the Accuracy of Quantum Mechanics | 已下载正文 | 22 | 33 | 1.0 | openalex_open_access_pdf |
| 85 | 2017 | Active learning of linearly parametrized interatomic potentials | 已下载正文 | 12 | 43 | 1.0 | openalex_open_access_pdf |
| 86 | 2020 | On-the-fly active learning of interpretable Bayesian force fields for atomistic rare events | 已下载正文 | 11 | 48 | 0.889 | openalex_open_access_pdf |
| 87 | 2020 | On-the-Fly Active Learning of Interatomic Potentials for Large-Scale Atomistic Simulations | 已下载正文 | 10 | 44 | 1.0 | institutional_proxy_download |
| 88 | 2019 | On-the-fly Machine Learning Force Field Generation: Application to Melting Points | 已下载正文 | 15 | 46 | 1.0 | openalex_open_access_pdf |
| 89 | 2019 | De Novo Exploration and Self-Guided Learning of Potential-Energy Surfaces | 已下载正文 | 9 | 39 | 1.0 | openalex_open_access_pdf |
| 90 | 2019 | Machine learning interatomic potentials as emerging tools for materials science | 已下载正文 | 45 | 77 | 1.0 | curated_public_source |
| 91 | 2021 | Machine-learning interatomic potentials for materials science | 已下载正文 | 48 | 88 | 1.0 | curated_public_source |
| 92 | 2021 | Machine Learning Force Fields | 已下载正文 | 120 | 240 | 0.75 | curated_public_source |
| 93 | 2020 | Machine learning for interatomic potential models | 已下载正文 | 14 | 60 | 1.0 | institutional_proxy_download |
| 94 | 2006 | Factors that affect Li mobility in layered lithium transition metal oxides | 已下载正文 | 7 | 24 | 1.0 | public_aps_fulltext |
| 95 | 2014 | Structures, Thermodynamics, and Li+ Mobility of Li10GeP2S12: A First-Principles Analysis | 已下载正文 | 6 | 23 | 1.0 | 已核验来源 |
| 96 | 2016 | Origin of Fast Ion Conduction in Li10GeP2S12, a Superionic Conductor | 已下载正文 | 9 | 31 | 1.0 | institutional_proxy_download |
| 97 | 2012 | One-dimensional stringlike cooperative migration of lithium ions in an ultrafast ionic conductor | 已下载正文 | 4 | 11 | 1.0 | institutional_proxy_download |
| 98 | 2019 | High-Throughput Screening of Solid-State Li-Ion Conductors Using Lattice-Dynamics Descriptors | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 99 | 2019 | First-principles prediction of potentials and space-charge layers in all-solid-state batteries | 已下载正文 | 6 | 19 | 1.0 | openalex_open_access_pdf |
| 100 | 2024 | Machine Learning-Accelerated First-Principles Study of Atomic Configuration and Ionic Diffusion in Li10GeP2S12 Solid Electrolyte | 已下载正文 | 14 | 53 | 1.0 | curated_public_source |
| 101 | 2022 | First-principles study on selenium-doped Li10GeP2S12 solid electrolyte: Effects of doping on moisture stability and Li-ion transport properties | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 102 | 2023 | Toward the Formation of the Solid Electrolyte Interphase on Alkaline Metal Anodes: Ab Initio Simulations | 已下载正文 | 8 | 29 | 1.0 | open_access_landing_page |
| 103 | 2021 | Quantum chemical calculations of lithium-ion battery electrolyte and interphase species | 已下载正文 | 15 | 52 | 1.0 | openalex_open_access_pdf |
| 104 | 2017 | Review—SEI: Past, Present and Future | 已下载正文 | 17 | 95 | 1.0 | curated_public_source |
| 105 | 2015 | FireWorks: a dynamic workflow system designed for high-throughput applications | 已下载正文 | 58 | 82 | 1.0 | openalex_open_access_pdf |
| 106 | 2017 | Atomate: A high-level interface to generate, execute, and analyze computational materials science workflows | 已下载正文 | 22 | 52 | 0.909 | openalex_open_access_pdf |
| 107 | 2020 | Materials Cloud, a platform for open computational science | 已下载正文 | 12 | 41 | 1.0 | openalex_open_access_pdf |
| 108 | 2018 | matminer: An open source toolkit for materials data mining | 已下载正文 | 21 | 46 | 1.0 | openalex_open_access_pdf |
| 109 | 2025 | Understanding solid-state battery electrolytes using atomistic modelling and machine learning | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 110 | 2025 | Toward AI ecosystems for electrolyte and interface engineering in solid-state batteries | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 111 | 2026 | Machine learning pipelines for the design of solid-state electrolytes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 112 | 2026 | A perspective on training machine learning force fields for solid-state electrolyte materials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 113 | 2026 | Redefining atomistic simulations of all-solid-state batteries through machine learning interatomic potentials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 114 | 2025 | Application-oriented design of machine learning paradigms for battery science | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 115 | 2024 | Machine learning interatomic potential: Bridge the gap between small-scale models and realistic device-scale simulations | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 116 | 2025 | Enabling accurate modelling of materials for a solid electrolyte interphase in lithium-ion batteries using effective machine learning interatomic potentials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 117 | 2025 | A pre-trained deep potential model for sulfide solid electrolytes with broad coverage and high accuracy | 已下载正文 | 15 | 36 | 1.0 | curated_public_source |
| 118 | 2024 | Principal component analysis enables the design of deep learning potential precisely capturing LLZO phase transitions | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 119 | 2024 | Probing degradation at solid-state battery interfaces using machine-learning interatomic potential | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 120 | 2024 | Size dependent lithium-ion conductivity of solid electrolytes in machine learning molecular dynamics simulations | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 121 | 2024 | Machine Learning-Assisted Property Prediction of Solid-State Electrolyte | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 122 | 2024 | Computationally Guided Synthesis of Battery Materials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 123 | 2024 | Scalable Parallel Algorithm for Graph Neural Network Interatomic Potentials in Molecular Dynamics Simulations | 已下载正文 | 36 | 54 | 1.0 | curated_public_source |
| 124 | 2025 | Data-Efficient Multifidelity Training for High-Fidelity Machine Learning Interatomic Potentials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 125 | 2025 | CHIPS-FF: Evaluating Universal Machine Learning Force Fields for Material Properties | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 126 | 2025 | Assessment and Application of Universal Machine Learning Interatomic Potentials in Solid-State Electrolyte Research | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 127 | 2026 | Machine Learning Interatomic Potentials for Modeling Solid-State Batteries | 已下载正文 | 18 | 82 | 1.0 | curated_public_source |
| 128 | 2026 | Machine-learning interatomic potentials for interfaces in all-solid-state batteries: Perspectives on training data, model selection, and validation | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 129 | 2026 | Constructing machine learning interatomic potentials with minimum amount of ab initio data | 已下载正文 | 10 | 38 | 1.0 | 已核验来源 |
| 130 | 2024 | Computational prediction of solvation structures in calcium battery electrolytes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 131 | 2024 | A Perspective on the Molecular Modeling of Electrolyte Decomposition Reactions for Solid Electrolyte Interphase Growth in Lithium‐Ion Batteries | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 132 | 2025 | A foundation machine learning potential with polarizable long-range interactions for materials modelling | 已下载正文 | 12 | 53 | 1.0 | official_publisher_current_network |
| 133 | 2025 | Enhancing robustness in machine-learning-accelerated molecular dynamics: A multi-model nonparametric probabilistic approach | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 134 | 2026 | Machine learning interatomic potential enables interface-level insights into cathode/solid electrolyte adhesion in sodium-ion batteries | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 135 | 2023 | Scaling deep learning for materials discovery | 已下载正文 | 11 | 56 | 1.0 | official_publisher_current_network |
| 136 | 2025 | Disorder-induced enhancement of lithium-ion transport in solid-state electrolytes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 137 | 2025 | InterOptimus: An AI-assisted robust workflow for screening ground-state heterogeneous interface structures in lithium batteries | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 138 | 2025 | Machine learning study on the structural evolution of high-nickel layered cathodes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 139 | 2025 | Machine-learning-accelerated mechanistic exploration of interface modification in lithium metal anode | 已下载正文 | 8 | 35 | 0.9 | official_publisher_current_network |
| 140 | 2025 | Unraveling charge effects on interface reactions and dendrite growth in lithium metal anode | 已下载正文 | 10 | 34 | 1.0 | official_publisher_current_network |
| 141 | 2025 | Observation of dendrite formation at Li metal-electrolyte interface by a machine-learning enhanced constant potential framework | 已下载正文 | 13 | 56 | 1.0 | official_publisher_current_network |
| 142 | 2025 | Surface orientation-dependent adhesion behavior in Na-cathode and solid-state electrolyte interfaces using machine learning interatomic potential | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 143 | 2025 | Data-driven atomistic modeling of crystalline and glassy solid-state electrolytes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 144 | 2026 | Integrated machine learning-molecular dynamics framework for electrolyte property prediction | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 145 | 2026 | Electrolyte engineering for lithium-ion batteries: Mechanistic insights into the development of electrolyte from atomic-scale simulation | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 146 | 2024 | Machine learning interatomic potentials in engineering perspective for developing cathode materials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 147 | 2024 | Atomistic modeling of bulk and grain boundary diffusion in solid electrolyte Li6PS5Cl using machine-learning interatomic potentials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 148 | 2024 | Cartesian atomic cluster expansion for machine learning interatomic potentials | 已下载正文 | 10 | 36 | 1.0 | official_publisher_current_network |
| 149 | 2024 | Robust training of machine learning interatomic potentials with dimensionality reduction and stratified sampling | 已下载正文 | 11 | 42 | 0.909 | official_publisher_current_network |
| 150 | 2025 | Cartesian atomic moment machine learning interatomic potentials | 已下载正文 | 10 | 42 | 1.0 | official_publisher_current_network |
| 151 | 2025 | Machine learning of charges and long-range interactions from energies and forces | 已下载正文 | 17 | 59 | 1.0 | official_publisher_current_network |
| 152 | 2025 | Evidential deep learning for interatomic potentials | 已下载正文 | 11 | 39 | 1.0 | official_publisher_current_network |
| 153 | 2025 | Navigating chemical design spaces for metal-ion batteries via machine-learning-guided phase-field simulations | 已下载正文 | 13 | 55 | 0.917 | official_publisher_current_network |
| 154 | 2024 | Electronic Moment Tensor Potentials include both electronic and vibrational degrees of freedom | 已下载正文 | 10 | 41 | 1.0 | official_publisher_current_network |
| 155 | 2025 | Universal machine learning interatomic potentials are ready for phonons | 已下载正文 | 8 | 29 | 1.0 | official_publisher_current_network |
| 156 | 2025 | Dynamic oxygen-redox evolution of cathode reactions based on the multistate equilibrium potential model | 已下载正文 | 11 | 35 | 1.0 | official_publisher_current_network |
| 157 | 2025 | A Universal Machine Learning Framework Driven by Artificial Intelligence for Ion Battery Cathode Material Design | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 158 | 2025 | Machine-Learning-Accelerated Development of High-Nickel NCM Cathodes via Multivariable Co-optimization | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 159 | 2025 | Combined machine learning and computational protocols to predict electrolyte behavior and SEI formation in Li-metal batteries | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 160 | 2025 | Data‐Driven Lithium Salt Design for Long‐Cycle Lithium Metal Battery | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 161 | 2026 | Discovery Learning predicts battery cycle life from minimal experiments | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 162 | 2025 | Screening of potential candidates for solid electrolyte interphase materials for lithium-ion batteries through a data-driven approach | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 163 | 2026 | AI-driven exploration and design of inorganic battery materials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 164 | 2026 | Performance-Based Selection of Machine Learning Interatomic Potentials for Studying Solid-State Electrolytes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 165 | 2025 | Heterogeneous ensemble enables a universal uncertainty metric for atomistic foundation models | 已下载正文 | 12 | 54 | 1.0 | official_publisher_current_network |
| 166 | 2024 | Machine learning interatomic potential with DFT accuracy for general grain boundaries in α-Fe | 已下载正文 | 16 | 64 | 1.0 | official_publisher_current_network |
| 167 | 2026 | Molecular dynamics study on effect of crystal defects in NCM811 cathode structure based on machine learning potential | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 168 | 2025 | Probing Surface Degradation Pathways of Charged Nickel-Oxide Cathode Materials Using Machine-Learning Interatomic Potentials | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 169 | 2022 | Al‐Doping Driven Suppression of Capacity and Voltage Fadings in 4d‐Element Containing Li‐Ion‐Battery Cathode Materials: Machine Learning and Density Functional Theory | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 170 | 2020 | A database of battery materials auto-generated using ChemDataExtractor | 已下载正文 | 13 | 47 | 1.0 | official_publisher_current_network |
| 171 | 2023 | Data-driven electrolyte design for lithium metal anodes | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 172 | 2024 | Active learning for SNAP interatomic potentials via Bayesian predictive uncertainty | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 173 | 2026 | Benchmarking on-the-Fly Machine Learning Force Fields for Ion Hydration: Structure, Coordination, and Exchange Dynamics across Monovalent and Divalent Cations | 未保存本地全文 | — | — | — | WOS/DOI 回退 |
| 174 | 2025 | Benchmarking machine learning models for predicting lithium ion migration | 已下载正文 | 12 | 52 | 1.0 | curated_public_source |
| 175 | 2025 | Application of pretrained universal machine-learning interatomic potential for physicochemical simulation of liquid electrolytes in Li-ion batteries | 已下载正文 | 14 | 56 | 1.0 | curated_public_source |
| 176 | 2025 | Domain oriented universal machine learning potential enables fast exploration of chemical space of battery electrolytes | 已下载正文 | 12 | 49 | 1.0 | curated_public_source |

## 尚未保存的正文

- Empowering materials science with VASPKIT: a toolkit for enhanced simulation and analysis，DOI `10.1038/s41596-025-01160-w`：本地未保存正文，使用 WOS/DOI 回退。
- A polymeric artificial solid electrolyte interface dramatically enhances lithium-ion transport，DOI `10.1039/d4cc03688c`：本地未保存正文，使用 WOS/DOI 回退。
- High-Throughput Screening of Solid-State Li-Ion Conductors Using Lattice-Dynamics Descriptors，DOI `10.1016/j.isci.2019.05.036`：本地未保存正文，使用 WOS/DOI 回退。
- First-principles study on selenium-doped Li10GeP2S12 solid electrolyte: Effects of doping on moisture stability and Li-ion transport properties，DOI `10.1016/j.mtchem.2022.101223`：本地未保存正文，使用 WOS/DOI 回退。
- Understanding solid-state battery electrolytes using atomistic modelling and machine learning，DOI `10.1038/s41578-025-00817-y`：本地未保存正文，使用 WOS/DOI 回退。
- Toward AI ecosystems for electrolyte and interface engineering in solid-state batteries，DOI `10.1126/sciadv.aea0638`：本地未保存正文，使用 WOS/DOI 回退。
- Machine learning pipelines for the design of solid-state electrolytes，DOI `10.1039/d5mh01525a`：本地未保存正文，使用 WOS/DOI 回退。
- A perspective on training machine learning force fields for solid-state electrolyte materials，DOI `10.1038/s44456-026-00014-4`：本地未保存正文，使用 WOS/DOI 回退。
- Redefining atomistic simulations of all-solid-state batteries through machine learning interatomic potentials，DOI `10.1016/j.jechem.2025.08.058`：本地未保存正文，使用 WOS/DOI 回退。
- Application-oriented design of machine learning paradigms for battery science，DOI `10.1038/s41524-025-01575-9`：本地未保存正文，使用 WOS/DOI 回退。
- Machine learning interatomic potential: Bridge the gap between small-scale models and realistic device-scale simulations，DOI `10.1016/j.isci.2024.109673`：本地未保存正文，使用 WOS/DOI 回退。
- Enabling accurate modelling of materials for a solid electrolyte interphase in lithium-ion batteries using effective machine learning interatomic potentials，DOI `10.1039/d5mh01343g`：本地未保存正文，使用 WOS/DOI 回退。
- Principal component analysis enables the design of deep learning potential precisely capturing LLZO phase transitions，DOI `10.1038/s41524-024-01240-7`：本地未保存正文，使用 WOS/DOI 回退。
- Probing degradation at solid-state battery interfaces using machine-learning interatomic potential，DOI `10.1016/j.ensm.2024.103842`：本地未保存正文，使用 WOS/DOI 回退。
- Size dependent lithium-ion conductivity of solid electrolytes in machine learning molecular dynamics simulations，DOI `10.1016/j.aichem.2024.100051`：本地未保存正文，使用 WOS/DOI 回退。
- Machine Learning-Assisted Property Prediction of Solid-State Electrolyte，DOI `10.1002/aenm.202304480`：本地未保存正文，使用 WOS/DOI 回退。
- Computationally Guided Synthesis of Battery Materials，DOI `10.1021/acsenergylett.4c00821`：本地未保存正文，使用 WOS/DOI 回退。
- Data-Efficient Multifidelity Training for High-Fidelity Machine Learning Interatomic Potentials，DOI `10.1021/jacs.4c14455`：本地未保存正文，使用 WOS/DOI 回退。
- CHIPS-FF: Evaluating Universal Machine Learning Force Fields for Material Properties，DOI `10.1021/acsmaterialslett.5c00093`：本地未保存正文，使用 WOS/DOI 回退。
- Assessment and Application of Universal Machine Learning Interatomic Potentials in Solid-State Electrolyte Research，DOI `10.1021/acsmaterialslett.5c00336`：本地未保存正文，使用 WOS/DOI 回退。
- Machine-learning interatomic potentials for interfaces in all-solid-state batteries: Perspectives on training data, model selection, and validation，DOI `10.1557/s43579-026-00928-9`：本地未保存正文，使用 WOS/DOI 回退。
- Computational prediction of solvation structures in calcium battery electrolytes，DOI `10.1039/d4ta06675h`：本地未保存正文，使用 WOS/DOI 回退。
- A Perspective on the Molecular Modeling of Electrolyte Decomposition Reactions for Solid Electrolyte Interphase Growth in Lithium‐Ion Batteries，DOI `10.1002/adfm.202313188`：本地未保存正文，使用 WOS/DOI 回退。
- Enhancing robustness in machine-learning-accelerated molecular dynamics: A multi-model nonparametric probabilistic approach，DOI `10.1016/j.mechmat.2024.105237`：本地未保存正文，使用 WOS/DOI 回退。
- Machine learning interatomic potential enables interface-level insights into cathode/solid electrolyte adhesion in sodium-ion batteries，DOI `10.1016/j.est.2026.121104`：本地未保存正文，使用 WOS/DOI 回退。
- Disorder-induced enhancement of lithium-ion transport in solid-state electrolytes，DOI `10.1038/s41467-025-56322-x`：本地未保存正文，使用 WOS/DOI 回退。
- InterOptimus: An AI-assisted robust workflow for screening ground-state heterogeneous interface structures in lithium batteries，DOI `10.1016/j.jechem.2025.03.007`：本地未保存正文，使用 WOS/DOI 回退。
- Machine learning study on the structural evolution of high-nickel layered cathodes，DOI `10.1016/j.mtener.2025.101841`：本地未保存正文，使用 WOS/DOI 回退。
- Surface orientation-dependent adhesion behavior in Na-cathode and solid-state electrolyte interfaces using machine learning interatomic potential，DOI `10.1016/j.jpowsour.2025.237670`：本地未保存正文，使用 WOS/DOI 回退。
- Data-driven atomistic modeling of crystalline and glassy solid-state electrolytes，DOI `10.1039/d5cc04921k`：本地未保存正文，使用 WOS/DOI 回退。
- Integrated machine learning-molecular dynamics framework for electrolyte property prediction，DOI `10.1039/d6eb00024j`：本地未保存正文，使用 WOS/DOI 回退。
- Electrolyte engineering for lithium-ion batteries: Mechanistic insights into the development of electrolyte from atomic-scale simulation，DOI `10.1016/j.ensm.2025.104826`：本地未保存正文，使用 WOS/DOI 回退。
- Machine learning interatomic potentials in engineering perspective for developing cathode materials，DOI `10.1039/d4ta03452j`：本地未保存正文，使用 WOS/DOI 回退。
- Atomistic modeling of bulk and grain boundary diffusion in solid electrolyte Li6PS5Cl using machine-learning interatomic potentials，DOI `10.1103/physrevmaterials.8.115407`：本地未保存正文，使用 WOS/DOI 回退。
- A Universal Machine Learning Framework Driven by Artificial Intelligence for Ion Battery Cathode Material Design，DOI `10.1021/jacsau.5c00526`：本地未保存正文，使用 WOS/DOI 回退。
- Machine-Learning-Accelerated Development of High-Nickel NCM Cathodes via Multivariable Co-optimization，DOI `10.1021/acsenergylett.5c02723`：本地未保存正文，使用 WOS/DOI 回退。
- Combined machine learning and computational protocols to predict electrolyte behavior and SEI formation in Li-metal batteries，DOI `10.1016/j.cej.2025.163801`：本地未保存正文，使用 WOS/DOI 回退。
- Data‐Driven Lithium Salt Design for Long‐Cycle Lithium Metal Battery，DOI `10.1002/adsu.202500413`：本地未保存正文，使用 WOS/DOI 回退。
- Discovery Learning predicts battery cycle life from minimal experiments，DOI `10.1038/s41586-025-09951-7`：本地未保存正文，使用 WOS/DOI 回退。
- Screening of potential candidates for solid electrolyte interphase materials for lithium-ion batteries through a data-driven approach，DOI `10.1039/d5cp02726h`：本地未保存正文，使用 WOS/DOI 回退。
- AI-driven exploration and design of inorganic battery materials，DOI `10.1016/j.rser.2025.116633`：本地未保存正文，使用 WOS/DOI 回退。
- Performance-Based Selection of Machine Learning Interatomic Potentials for Studying Solid-State Electrolytes，DOI `10.1021/acs.chemmater.5c02352`：本地未保存正文，使用 WOS/DOI 回退。
- Molecular dynamics study on effect of crystal defects in NCM811 cathode structure based on machine learning potential，DOI `10.1016/j.jpowsour.2025.239008`：本地未保存正文，使用 WOS/DOI 回退。
- Probing Surface Degradation Pathways of Charged Nickel-Oxide Cathode Materials Using Machine-Learning Interatomic Potentials，DOI `10.1021/acsami.5c11818`：本地未保存正文，使用 WOS/DOI 回退。
- Al‐Doping Driven Suppression of Capacity and Voltage Fadings in 4d‐Element Containing Li‐Ion‐Battery Cathode Materials: Machine Learning and Density Functional Theory，DOI `10.1002/aenm.202201497`：本地未保存正文，使用 WOS/DOI 回退。
- Data-driven electrolyte design for lithium metal anodes，DOI `10.1073/pnas.2214357120`：本地未保存正文，使用 WOS/DOI 回退。
- Active learning for SNAP interatomic potentials via Bayesian predictive uncertainty，DOI `10.1016/j.commatsci.2024.113074`：本地未保存正文，使用 WOS/DOI 回退。
- Benchmarking on-the-Fly Machine Learning Force Fields for Ion Hydration: Structure, Coordination, and Exchange Dynamics across Monovalent and Divalent Cations，DOI `10.1021/acs.jpcb.6c02837`：本地未保存正文，使用 WOS/DOI 回退。

## 使用边界

本地全文命中是定位原文页码的入口，不自动等于经过人工复核的科学结论。涉及具体计算参数、数值或因果判断时，仍应回到对应页、图、表与补充材料核对。
