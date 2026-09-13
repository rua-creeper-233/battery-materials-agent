# 计算方法证据自动抽取审计

> 所有条目均为“自动抽取、待人工核对”。它们是原文定位器，不是可直接复制到 VASP/MD 输入文件的最终参数。

- 本地有正文的论文：14
- 抽取到至少一条方法信号的论文：14
- 方法信号总数：115
- 参考文献区：已排除
- 每篇每类上限：3 条
- 公开数据只保存短方法信号与页码，不保存连续正文上下文

## 分论文结果

### Computational understanding of Li-ion batteries

- 泛函与电子结构近似：p.1 `DFT+U`；p.2 `LDA`；p.2 `local density approximation`
- 扩散与迁移势垒方法：p.5 `mean squared displacement`；p.5 `migration barrier`；p.5 `MSD`
- 分子动力学条件：p.5 `NVT`

### Ab initio study of lithium intercalation in metal oxides and metal dichalcogenides

- 泛函与电子结构近似：p.2 `LDA`；p.9 `LDA`

### Identification of cathode materials for lithium batteries guided by first-principles calculations

- 未抽取到方法设置；可能无本地正文或正文未给出可识别参数。

### First-principles theory of ionic diffusion with nondilute carriers

- 泛函与电子结构近似：p.1 `local density approximation`；p.5 `LDA`；p.5 `local density approximation`
- 计算软件：p.5 `Vienna ab initio simulation package`
- 机器学习训练设置：p.11 `root mean square error`

### Voltage, stability and diffusion barrier differences between sodium-ion and lithium-ion intercalation materials

- 泛函与电子结构近似：p.4 `GGA`；p.4 `projector augmented-wave`；p.5 `GGA`
- 扩散与迁移势垒方法：p.4 `migration barrier`；p.4 `NEB`；p.4 `nudged elastic band`
- 计算软件：p.4 `VASP`

### Phase stability, electrochemical stability and ionic conductivity of the Li10±1MP2X12 family of superionic conductors

- 泛函与电子结构近似：p.2 `GGA`；p.2 `PBE`；p.3 `HSE`
- 计算软件：p.2 `pymatgen`；p.2 `VASP`；p.3 `VASP`
- 扩散与迁移势垒方法：p.3 `mean square displacement`；p.4 `mean square displacement`
- 分子动力学条件：p.3 `NVT`；p.3 `time step of molecular dynamics was chosen to be 2 fs`

### Defect Thermodynamics and Diffusion Mechanisms in Li2CO3 and Implications for the Solid Electrolyte Interphase in Li-Ion Batteries

- 未抽取到方法设置；可能无本地正文或正文未给出可识别参数。

### Holistic computational structure screening of more than 12,000 candidates for solid lithium-ion conductor materials

- 机器学习训练设置：p.2 `training set`；p.4 `Training set`；p.5 `training set`
- 计算软件：p.3 `Pymatgen`
- 收敛判据：p.11 `ionic threshold of 10`

### Diffusion of lithium ions in Lithium-argyrodite solid-state electrolytes

- 扩散与迁移势垒方法：p.1 `Arrhenius relation`；p.2 `Arrhenius equation`；p.3 `MSD`
- 分子动力学条件：p.2 `simulations at 300 K`；p.3 `35 ps for the simulation`；p.3 `simulations at 300 K`
- 平面波截断能：p.8 `cutoff energy of 280 Ry`
- 泛函与电子结构近似：p.8 `generalized gradient approximation`；p.8 `GGA`；p.8 `PBE`
- k 点采样：p.8 `1 × 1 × 1 k-point`
- 计算软件：p.8 `CP2K`

### A universal graph deep learning interatomic potential for the periodic table

- 机器学习训练设置：p.4 `stress error`；p.6 `training data`；p.8 `force error`
- 泛函与电子结构近似：p.8 `generalized gradient approximation`；p.8 `GGA`；p.8 `PBE`
- 分子动力学条件：p.10 `NpT`；p.25 `NVT`
- 扩散与迁移势垒方法：p.18 `Arrhenius plot`

### High-throughput investigation of stability and Li diffusion of doped solid electrolytes via neural network potential without configurational knowledge

- 扩散与迁移势垒方法：p.2 `NEB`；p.2 `nudged elastic band`；p.3 `mean square displacement`
- 泛函与电子结构近似：p.6 `PAW`；p.6 `PBE`；p.6 `projector-augmented wave`
- 机器学习训练设置：p.6 `MAE`；p.6 `mean absolute error`；p.6 `root mean squared error`
- 分子动力学条件：p.6 `NVT`；p.6 `time step was chosen to be 0.5 fs`

### A review of the recent progress in battery informatics

- 扩散与迁移势垒方法：p.2 `NEB`；p.7 `migration barrier`；p.8 `mean square displacement`
- 泛函与电子结构近似：p.5 `scan`；p.16 `scan`
- 机器学习训练设置：p.8 `training data`；p.13 `Machine learning potential`；p.13 `MAE`
- 超胞与模型规模：p.12 `supercell of ~200 atoms`；p.14 `2 × 2 × 2 supercell`；p.14 `supercell containing 1520 atoms`
- 分子动力学条件：p.12 `1200 K, while LOTF-MD`

### A climbing image nudged elastic band method for finding saddle points and minimum energy paths

- 扩散与迁移势垒方法：p.1 `NEB`；p.1 `nudged elastic band`；p.2 `NEB`
- 计算软件：p.7 `VASP`；p.8 `VASP`

### Ab initio molecular dynamics simulations of the initial stages of solid-electrolyte interphase formation on lithium ion battery graphitic anodes

- 泛函与电子结构近似：p.1 `PBE`；p.2 `PBE`
- 分子动力学条件：p.1 `17 ps trajectory`；p.1 `time steps of 1 fs`；p.2 `7 ps AIMD trajectory`

### First Principles Study of the Li10GeP2S12 Lithium Super Ionic Conductor Material

- 泛函与电子结构近似：p.1 `GGA`；p.1 `projector augmented-wave`；p.2 `GGA`
- 计算软件：p.1 `VASP`；p.1 `Vienna Ab initio Simulation Package`
- 扩散与迁移势垒方法：p.2 `Arrhenius plot`；p.2 `mean square displacement`；p.3 `Arrhenius plot`
- 分子动力学条件：p.2 `40 ps of MD simulation`；p.2 `simulations at 900 K`；p.2 `time step was chosen to be 2 fs`

### CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling

- 机器学习训练设置：p.1 `machine-learning interatomic potential`；p.2 `Machine-learning interatomic potential`；p.3 `test set`
- 泛函与电子结构近似：p.2 `generalized gradient approximation`；p.2 `GGA`；p.5 `GGA`
- 分子动力学条件：p.4 `simulation at 1,100 K`；p.8 `NVT`；p.8 `time step of 2 fs`
- 扩散与迁移势垒方法：p.6 `Arrhenius plot`；p.8 `mean squared displacement`
- 计算软件：p.7 `pymatgen`；p.7 `Vienna Ab initio Simulation Package`；p.8 `Vienna Ab initio Simulation Package`
