# baseline 补充论文下载清单

整理日期：2026-10-14。以下 11 篇的 DOI 不在现有 176 篇精选目录中，已按出版社/期刊官方记录核验书目。这里是建议清单，不表示已经下载、导入 Zotero 或取得机构全文权限；下载后再核验与入库。

baseline 在这里是科研过程中反复查验的常备参考，不是入门课程或模型对照。先补统计、采样、DFT 质量核验与数据规范；经典理论按具体任务查阅即可。社区常用方法不等于通用工业标准。

| 优先级 | 年份 | 论文完整题名 | DOI / 出版社 | 什么时候查 |
|---|---:|---|---|---|
| 现在优先下载 | 2018 | Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations [Article v1.0] | [10.33011/livecoms.1.1.5067](https://livecomsjournal.org/index.php/livecoms/article/view/v1i1e5067) | 做 MD 结果分析时查采样质量、相关性、有效样本和误差条；帮助写结果可信度与局限。 |
| 现在优先下载 | 2016 | A Simple Method for Automated Equilibration Detection in Molecular Simulations | [10.1021/acs.jctc.5b00784](https://pubs.acs.org/doi/10.1021/acs.jctc.5b00784) | 确定丢弃哪段平衡数据、选生产区间和评估有效样本；帮助写 MD 数据处理方法。 |
| 现在优先下载 | 1989 | Error estimates on averages of correlated data | [10.1063/1.457480](https://doi.org/10.1063/1.457480) | 解释为什么轨迹帧不是独立样本，查分块平均与相关数据的误差估计。 |
| 现在优先下载 | 2016 | Reproducibility in density functional theory calculations of solids | [10.1126/science.aad3000](https://www.science.org/doi/10.1126/science.aad3000) | 检查不同代码/赝势之间的数值可复现性，区分数值精度与物理准确性。 |
| 现在优先下载 | 2024 | How to verify the precision of density-functional-theory implementations via reproducible and universal workflows | [10.1038/s42254-023-00655-3](https://www.nature.com/articles/s42254-023-00655-3) | 用专家建议整理 DFT 精度核验、参考数据、统一工作流与适用范围；卷年 2024，线上发表于 2023。 |
| 现在优先下载 | 2016 | The FAIR Guiding Principles for scientific data management and stewardship | [10.1038/sdata.2016.18](https://www.nature.com/articles/sdata201618) | 检查数据/代码如何可查找、可获取、可互操作与可复用；FAIR 不等于所有资源都必须无限公开。 |
| 理论出处，按需查阅 | 1964 | Inhomogeneous Electron Gas | [10.1103/PhysRev.136.B864](https://journals.aps.org/pr/abstract/10.1103/PhysRev.136.B864) | DFT 的基础定理出处；写电子结构理论背景或查基态密度与能量泛函的基本假设。 |
| 理论出处，按需查阅 | 1965 | Self-Consistent Equations Including Exchange and Correlation Effects | [10.1103/PhysRev.140.A1133](https://journals.aps.org/pr/abstract/10.1103/PhysRev.140.A1133) | 查 Kohn–Sham 体系、自洽求解与交换关联处理的理论来源；不替代现代软件手册。 |
| 理论出处，按需查阅 | 1967 | Computer ‘Experiments’ on Classical Fluids. I. Thermodynamical Properties of Lennard-Jones Molecules | [10.1103/PhysRev.159.98](https://journals.aps.org/pr/abstract/10.1103/PhysRev.159.98) | 查经典 MD 数值推进与 Lennard-Jones 计算实验出处；实际积分实现需核对所用软件。 |
| 理论出处，按需查阅 | 1984 | A unified formulation of the constant temperature molecular dynamics methods | [10.1063/1.447334](https://doi.org/10.1063/1.447334) | 查恒温 MD 的理论与系综假设，写所用恒温方法的出处；不是所有恒温器的通用引用。 |
| 理论出处，按需查阅 | 1985 | Canonical dynamics: Equilibrium phase-space distributions | [10.1103/PhysRevA.31.1695](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.31.1695) | 查 Nosé–Hoover 动力学与采样假设；仍须检查目标体系的温度分布与采样表现。 |

## 下载和保存

按 DOI 进入正式论文记录，通过你本人获许可的机构入口或出版社开放版本逐篇保存主文，另存所需补充信息，不用补充材料替代正文。文件名可保留原名或完整题名；下载后告知保存位置，再做 DOI/题名/版本/完整性核验、证据入库与 Zotero 幂等附加。不要发送密码、Cookie 或带授权签名的链接，也不要将受限全文推到 GitHub。

## 年份与阅读边界

- Bosoni 等的专家建议正式卷年为 2024，线上发表于 2023-11-14，正确 DOI 为 `10.1038/s42254-023-00655-3`。这里以正式卷年列示。
- Grossfield 等 v1.0 页的正式引用年份为 2018（该卷期标为 2019）；本清单按官方 How to Cite 的年份列示。
- 原始理论文章用于查出处；操作时还须核对现行软件手册、已验证协议和自己的参数/采样检查。
- FAIR 关注可查找、可获取、互操作与复用，访问可受合理权限限制；它不是要求公开个人数据或受限文件。

完整分阶段路线见 [学习路线](../learning-route.html)。这些候选与现有库、常备跨阶段引用分开计数，避免重复或冒充已下载论文。
