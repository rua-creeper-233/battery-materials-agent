(function () {
  const aliases = {
    '电压': ['voltage', 'intercalation', 'total energy'],
    '扩散': ['diffusion', 'migration', 'barrier', 'neb', 'aimd', 'msd'],
    '迁移': ['diffusion', 'migration', 'barrier', 'neb'],
    '势垒': ['barrier', 'migration', 'ci-neb'],
    '界面': ['interface', 'sei', 'electrode-electrolyte'],
    '稳定性': ['stability', 'phase diagram', 'electrochemical window'],
    '固态电解质': ['solid electrolyte', 'superionic', 'lgps', 'ionic conductivity'],
    '机器学习势': ['machine-learning potential', 'neural network potential', 'm3gnet', 'chgnet', 'nnp'],
    '神经网络势': ['neural network potential', 'nnp', 'mlip'],
    '高通量': ['high-throughput', 'screening', 'materials project'],
    '钠': ['sodium', 'na-ion'], '锂': ['lithium', 'li-ion']
  };
  const taskRules = [
    ['mlp', ['机器学习势','神经网络势','mlip','m3gnet','chgnet','deepmd','nnp']],
    ['interface', ['界面','sei','电解液','表面']],
    ['diffusion', ['扩散','迁移','势垒','neb','aimd','msd','电导率']],
    ['voltage', ['电压','容量','嵌锂','脱锂','开路']],
    ['stability', ['稳定性','相图','凸包','分解','电化学窗口']],
    ['screening', ['筛选','高通量','候选','数据库']]
  ];
  const leads = {
    voltage: '电压问题应以不同嵌入组分的稳定相和一致设置下的总能为核心，而不是只算一个端点。',
    diffusion: '扩散问题先分清“单跳势垒”与“有限温度扩散系数”：NEB适合前者，AIMD/MLMD适合后者。',
    interface: '界面问题建议先做反应热力学，再做显式界面；否则容易在本就会分解的界面上过度解释电荷密度。',
    stability: '稳定性至少分为体相、相对竞争相、电化学窗口和界面反应四层，不能用单一形成能替代。',
    screening: '高通量宜分层筛选：便宜指标先缩小空间，昂贵DFT动力学最后验证。',
    mlp: '机器学习势把近似DFT精度扩展到更大体系和更长时间，但适用域验证比模型名称更重要。'
  };
  const workflows = {
    voltage: [
      '枚举相邻稳定嵌入组分和占位构型，分别做自旋极化弛豫与静态总能。',
      '构建组分—能量凸包，避免用两个亚稳端点制造虚假电压平台。',
      '按 ΔG≈ΔE 计算平均电压，并检查金属参比相、磁序、DFT+U和O2相关误差。',
      '与实验平台或高质量已发表计算交叉验证。'
    ],
    diffusion: [
      '先确认空位、间隙或协同机制以及可能通道；稀释极限NEB不自动代表真实浓度。',
      'NEB需检查超胞、中间像、原子映射、弹簧数和力收敛。',
      'AIMD/MLMD需使用多个温度与独立初态，报告MSD线性区、有效跃迁数和误差。',
      '计算电导率时说明载流子浓度、相关运动和Nernst–Einstein近似。'
    ],
    interface: [
      '先用相图和反应能判断热力学相容性，再决定是否构建显式界面。',
      '枚举表面、终止与晶格匹配，报告应变、面积、真空和偶极修正。',
      '静态DFT回答粘附/电荷转移，AIMD或反应型ML势回答有限温度反应。',
      '对SEI/CEI建立化学势—缺陷形成能—NEB—电导的完整链路。'
    ],
    stability: [
      '收集同一化学空间的竞争相，统一计算或使用同版本数据库能量。',
      '计算凸包能、分解反应和工作离子化学势范围。',
      '区分热力学窗口、动力学钝化窗口和实验表观窗口。',
      '对温度敏感体系评估振动自由能或说明零温DFT近似。'
    ],
    screening: [
      '定义元素、凸包能、容量、电压、体积变化与成本等硬筛选条件。',
      '数据库特征先过滤，DFT弛豫、NEB/AIMD再分层投入。',
      '按化学体系或结构原型划分测试集，避免近重复结构泄漏。',
      '最终候选回到高精度计算并给出不确定性、失败模式与可合成性证据。'
    ],
    mlp: [
      '固定元素、相、缺陷、表面/界面、温压和反应适用域。',
      '用DFT生成覆盖平衡与非平衡构型的能量/力/应力标签，并主动学习补点。',
      '按轨迹、组分与结构家族分组切分，避免相邻帧泄漏。',
      '除MAE外验证RDF、声子/弹性、缺陷能、NEB势垒和扩散系数。',
      '只有通过目标性质验证后才做大体系长时间MLMD，并设置OOD报警。'
    ]
  };
  const common = [
    '定义材料、工作离子、荷电状态、温度和目标性质。',
    '记录结构来源、数据库版本、结构ID和所有计算版本。',
    '先完成ENCUT、k点、超胞、磁序和必要U值的收敛。'
  ];
  function taskType(q) {
    const text = q.toLowerCase();
    return (taskRules.find(([, words]) => words.some(word => text.includes(word))) || ['screening'])[0];
  }
  function search(query, papers, limit=5) {
    let expanded = query.toLowerCase();
    Object.entries(aliases).forEach(([key, values]) => { if (expanded.includes(key)) expanded += ' ' + values.join(' '); });
    const tokens = expanded.match(/[a-z][a-z0-9+_.:/-]*|[\u4e00-\u9fff]{2,}/g) || [];
    return papers.map(p => {
      const doc = JSON.stringify(p).toLowerCase();
      const score = tokens.reduce((sum, token) => sum + (doc.includes(token) ? (token.length > 3 ? 2 : 1) : 0), 0);
      return {p, score};
    }).sort((a,b) => b.score-a.score || b.p.year-a.p.year).slice(0,limit).map(row => row.p);
  }
  function citation(p, i) {
    const wos = p.wos_uid ? `；[WOS记录](https://www.webofscience.com/wos/woscc/full-record/${p.wos_uid})` : '';
    return `[${i}] ${p.authors[0]} 等, ${p.year}, *${p.title}*, ${p.journal}. DOI: [${p.doi}](https://doi.org/${p.doi})${wos}`;
  }
  function answer(question, papers) {
    const task = taskType(question);
    const found = search(question, papers, 5);
    const wantsPlan = ['怎么','如何','方案','路线','流程','计划','workflow','复现'].some(w => question.toLowerCase().includes(w));
    const lines = ['### 结论','',leads[task]];
    if (wantsPlan) {
      lines.push('', `### 可执行工作流：${task}`, '');
      [...common, ...workflows[task]].forEach((step, i) => lines.push(`${i+1}. ${step}`));
    } else {
      lines.push('', '### 文献证据', '');
      found.forEach((p,i) => lines.push(`- **〔${i+1}〕${p.role}**：${p.evidence?.[0]?.claim || p.summary}`));
    }
    lines.push('', '### 证据来源', '');
    found.forEach((p,i) => lines.push('- ' + citation(p,i+1)));
    lines.push('', '### 边界与下一步', '', '具体INCAR/KPOINTS、U值、赝势、超胞和温度不能自动猜定；必须回到全文/补充信息并重新收敛。');
    return {question, task, answer_markdown:lines.join('\n'), papers:found, provenance:{wos_note:'16篇种子论文已于2026-09-13在华南师范大学机构会话中逐条取得WOS UT；静态版不包含受版权保护的PDF。'}};
  }
  window.BatteryBrowserAgent = {answer, search};
})();
