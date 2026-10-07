# 从论文到可复现的小实验

更新：2026-10-08 接续版。这是本项目建议的练习路线，不是已经完成的论文复现，也不保证可以发表。先选一个小问题，不同时下载所有数据或训练所有模型。

## 1. CPU 起步：LiTraj 迁移势垒基准

[论文 DOI](https://doi.org/10.1038/s41524-025-01571-z)；[作者数据与工具](https://github.com/AIRI-Institute/LiTraj)。

前置知识：Python、NumPy/pandas、训练/验证/测试划分、MAE/RMSE、晶体与迁移势垒的基本含义。先读论文 Methods 和数据仓库 README，区分 BVSE 代理标签、DFT-NEB 标签以及原子势的能量/力标签。

作者仓库提供 BVEL13k、nebBVSE122k、nebDFT2k 和 MPLiTrj。对本机练习，可先选择压缩约 11 MB 的 BVEL13k，而不是数 GB 的构型全集。数据大小与接口可能更新，下载前以仓库为准。

以下是作者公开工具接口的使用示意，在独立环境与独立工作目录运行；它会联网下载数据，本轮未执行该数据下载：

```bash
python -m venv .venv-litraj
# Linux/WSL: source .venv-litraj/bin/activate
# Windows: .venv-litraj\Scripts\activate
python -m pip install litraj
```

```python
from litraj.data import download_dataset, load_data

download_dataset("BVEL13k", "./litraj_data", unzip=True)
train, validation, test, index = load_data("BVEL13k", "./litraj_data")
for atoms in train[:3]:
    print(atoms.info["material_id"], atoms.info["E_1D"])
```

建议交付：

1. 记录数据版本、下载来源、许可、文件哈希与单位；查看缺失值及材料 ID 是否重复。
2. 先做训练集均值预测基线，再按论文/作者 notebook 的特征流程做小规模回归。预测特征不得包含目标标签或测试集统计量。
3. 沿用作者提供的划分，核查同源材料/路径泄漏；另做按材料或结构族留出的敏感性分析，说明与论文评估协议的区别。
4. 输出测试 MAE/RMSE、误差分布与失败材料清单。不要把 BVSE 标签的预测精度叫作 DFT 精度。
5. 后续再读取 nebDFT2k 的少量路径，比较端点、过渡态和势垒；做 MLIP-NEB 之前检查自旋、PBE/DFT+U、参考设置是否一致。

论文复现的价值是得到可信基线与误差解释，不是把作者数据重新随机分一次就当创新。

## 2. 小体系 GPU：SevenNet 液态电解液领域验证

[论文 DOI](https://doi.org/10.1039/D5DD00025D)；[作者预印本](https://arxiv.org/abs/2501.05211)；[数据与处理脚本](https://zenodo.org/records/15205477)；[SevenNet](https://github.com/MDIL-SNU/SevenNet)。

前置知识：ASE/LAMMPS、分子与周期边界、NVT/NPT、密度、RDF、MSD、范德华作用与统计误差。资料全集约 39.7 GB，先查看文件清单并取目标体系的小部分，不整包下载。

建议顺序：单分子/二聚体检查 → 单一纯溶剂的结构与密度 → 一个含盐配方的溶剂化 → 输运。先按论文 Methods/ESI 核对 DFT 参考和 D3 处理、势模型版本、温压与体系大小，再运行作者脚本。这里不编造论文未提供的通用输入参数。

至少保存：未微调势与适配势的对照、独立参考构型能量/力误差、密度及波动、RDF/配位数、轨迹稳定性、扩散拟合区间与多条轨迹误差。不要直接把通用势在无机晶体上的误差当成液体密度和输运的准确度。

本机 6 GB GPU 先试小体系；长时间 MD、多模型训练和较大数据集按实际资源评估。本项目的 CSV-MSD 合成示例不能代替真实液态轨迹。

## 3. 进阶：电解液领域通用势与并发学习

[论文 DOI](https://doi.org/10.1038/s41467-025-67982-0)；[作者模型/数据入口](https://doi.org/10.12463/AI4EC/QZCYP1)；[ai2-kit](https://github.com/chenggroup/ai2-kit)。正式引用卷年为 2026；在线日期为 2025-12-31，不能只从 DOI 后缀判断年份。

前置知识：DeePMD、LAMMPS、CP2K/DFT 标签、模型不确定性与主动/并发学习。先确认模型和数据可获取、元素/电荷/化学空间覆盖及许可，再挑一个已覆盖配方做基线；不要把训练所有体系作为入门任务。

建议流程：复现原模型的小体系结果 → 选未见配方/温度作为独立检验 → 识别失效构型 → 用统一 DFT 设置补标签 → 小规模适配 → 在同一独立检验上比较能量/力、配位和输运。采样用于选数据，不能把模型间一致性直接当作正确性；最终还需独立参考。

## 4. 每个算例的验收清单

- 可追踪输入：结构、配方、温压、版本、模型和参考计算设置。
- 数值与物理检查：收敛、有限尺寸、时间采样、守恒/稳定性、对照和不确定度。
- 数据协议：材料/路径/配方来源隔离；没有训练测试泄漏。
- 结果可复核：脚本、日志、失败例、单位、图表及原始数据位置。
- 文献声明边界：论文报道、自己的复现、自己的假设分别标记；没有实际运行的步骤写“计划”，不能写“完成”。

完成一个可靠基线后，再与课题指导者讨论明确的新问题。单纯换软件、扩大论文数量或模型名称并不构成可发表的科学贡献。
