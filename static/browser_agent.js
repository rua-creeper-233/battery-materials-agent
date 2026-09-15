(function () {
  const aliases = {
    '第一性原理': ['dft', 'first-principles', 'density functional'],
    '反应识别': ['automatic reaction identification', 'reaction sequence'],
    '均方位移': ['msd', 'diffusion', 'molecular dynamics'],
    '微调': ['fine-tuning', 'transfer learning', 'MACE-freeze'],
    '不确定性': ['uncertainty', 'quantile regression', 'readout ensemble'],
    '电压': ['voltage', 'intercalation', 'total energy', 'thermodynamic'],
    '扩散': ['diffusion', 'migration', 'barrier', 'neb', 'aimd', 'msd'],
    '迁移': ['diffusion', 'migration', 'barrier', 'neb'],
    '势垒': ['barrier', 'migration', 'neb', 'ci-neb'],
    '界面': ['interface', 'sei', 'electrode-electrolyte', 'surface'],
    '稳定性': ['stability', 'phase diagram', 'electrochemical window', 'energy above hull'],
    '固态电解质': ['solid electrolyte', 'superionic', 'lgps', 'ionic conductivity'],
    '机器学习势': ['machine-learning potential', 'neural network potential', 'm3gnet', 'chgnet', 'deepmd', 'dp-gen', 'nequip', 'allegro', 'gap', 'nnp', 'mlip'],
    '神经网络势': ['neural network potential', 'nnp', 'mlip', 'deepmd', 'nequip', 'allegro'],
    '主动学习': ['active learning', 'concurrent learning', 'dp-gen', 'model deviation'],
    '高通量': ['high-throughput', 'screening', 'materials project', 'atomate2', 'aiida'],
    '缺陷': ['defect', 'vacancy', 'interstitial', 'formation energy', 'pymatgen-analysis-defects'],
    '入门': ['starter', 'protocol', 'vaspkit', 'pymatgen', 'ase', 'sumo', 'lammps', 'dscribe', 'matbench'],
    '声子': ['phonon', 'phonopy', 'finite displacement', 'force constants'],
    '后处理': ['post-processing', 'vaspkit', 'sumo', 'band structure', 'dos'],
    '反应力场': ['reaxff', 'reactive molecular dynamics', 'force-field training'],
    '溶剂化': ['solvation', 'coordination', 'radial distribution'],
    '电解液': ['electrolyte', 'solvent', 'salt'],
    '双电层': ['electric double layer', 'edl', 'charged interface'],
    '相场': ['phase-field', 'continuum modeling', 'sei growth'],
    '多尺度': ['multiscale', 'phase-field', 'continuum modeling'],
    '聚合物电解质': ['polymer electrolyte', 'solid polymer electrolyte', 'spe'],
    '水解': ['hydrolysis', 'water-containing electrolyte'],
    '厚度演化': ['phase-field', 'sei growth', 'continuum modeling'],
    '纳秒到秒': ['multiscale', 'phase-field', 'time scales'],
    '点缺陷': ['point defect', 'pymatgen-analysis-defects', 'defect formation energy'],
    '一万多个晶体': ['high-throughput', 'screening', '12,000', 'classifier'],
    '小数据': ['small data', 'few-shot', 'fine-tuning', 'transfer learning'],
    '迁移学习': ['transfer learning', 'fine-tuning', 'MACE-freeze'],
    '风险判断': ['uncertainty', 'calibration', 'overconfidence'],
    '锂硫': ['lithium-sulfur', 'li-s', 'reaxff'],
    '硅负极': ['silicon anode', 'reaxff'],
    'materials studio': ['biovia materials studio'],
    '钠': ['sodium', 'na-ion'], '锂': ['lithium', 'li-ion'],
    'dft': ['density functional', 'first-principles', 'total energy'],
    'vasp': ['incar', 'kpoints', 'potcar', 'plane-wave'],
    'aimd': ['ab initio molecular dynamics', 'molecular dynamics', 'msd', 'diffusion'],
    'md': ['molecular dynamics', 'trajectory', 'msd'],
    'ms': ['materials studio']
  };
  const defaultWeights = {
    title: 6, role: 4.5, methods: 5, tags: 4, systems_properties: 2.5,
    summary_evidence: 1.5, phrase_bonus: 8, alias_factor: 0.65, doi_bonus: 50
  };
  const taskRules = [
    ['mlp', ['机器学习势','神经网络势','mlip','m3gnet','chgnet','mace','deepmd','nnp']],
    ['interface', ['界面','sei','电解液','表面']],
    ['diffusion', ['扩散','迁移','势垒','neb','aimd','msd','电导率']],
    ['voltage', ['电压','容量','嵌锂','脱锂','开路']],
    ['stability', ['稳定性','相图','凸包','分解','电化学窗口']],
    ['dft_setup', ['dft','vasp','incar','kpoints','potcar','截断能','k点','赝势','第一性原理']],
    ['md_setup', ['md','分子动力学','lammps','forcite','compass','nvt','npt','rdf']],
    ['screening', ['筛选','高通量','候选','数据库']]
  ];
  const leads = {
    general: '请先明确材料、目标性质和已有数据；当前问题不足以指定唯一计算路线。',
    md_setup: 'MD先确认力的来源、力场适用域、平衡与采样，再解释结构或输运性质；经典MD并不需要照抄VASP的ENCUT与k点。',
    voltage: '电压问题应以不同嵌入组分的稳定相和一致设置下的总能为核心，而不是只算一个端点。',
    diffusion: '扩散问题先分清“单跳势垒”与“有限温度扩散系数”：NEB适合前者，AIMD/MLMD适合后者。',
    interface: '界面问题建议先做反应热力学，再做显式界面；否则容易在本就会分解的界面上过度解释电荷密度。',
    stability: '稳定性至少分为体相、相对竞争相、电化学窗口和界面反应四层，不能用单一形成能替代。',
    screening: '高通量宜分层筛选：便宜指标先缩小空间，昂贵DFT动力学最后验证。',
    mlp: '机器学习势把近似DFT精度扩展到更大体系和更长时间，但适用域验证比模型名称更重要。',
    dft_setup: 'VASP/DFT 入门应先建立可复现的收敛与验证流程，再计算电压、扩散或界面；参数不能脱离材料和目标性质照抄。'
  };
  const workflows = {
    general: ['补充材料、目标性质与已有计算条件后，再选择DFT、MD或数据驱动路线。'],
    md_setup: ['选择覆盖元素、物相、温压和成键模式的力场，并核对电荷、原子类型与单位。','消除不合理接触并平衡温度与密度；根据研究目的选择NVT/NPT，不把平衡段计入生产统计。','测试时间步长、体系大小、轨迹时长和独立初态，输出能量、温度、结构与轨迹。','分开解释RDF/配位数的结构信息和MSD/相关函数的动力学信息。'],
    voltage: ['枚举相邻稳定嵌入组分和占位构型，分别做自旋极化弛豫与静态总能。','构建组分—能量凸包，避免用两个亚稳端点制造虚假电压平台。','按 ΔG≈ΔE 计算平均电压，并检查金属参比相、磁序、DFT+U和O2相关误差。','与实验平台或高质量已发表计算交叉验证。'],
    diffusion: ['先确认空位、间隙或协同机制以及可能通道；稀释极限NEB不自动代表真实浓度。','NEB需检查超胞、中间像、原子映射、弹簧数和力收敛。','AIMD/MLMD需使用多个温度与独立初态，报告MSD线性区、有效跃迁数和误差。','计算电导率时说明载流子浓度、相关运动和Nernst–Einstein近似。'],
    interface: ['先用相图和反应能判断热力学相容性，再决定是否构建显式界面。','枚举表面、终止与晶格匹配，报告应变、面积、真空和偶极修正。','静态DFT回答粘附/电荷转移，AIMD或反应型ML势回答有限温度反应。','对SEI/CEI建立化学势—缺陷形成能—NEB—电导的完整链路。'],
    stability: ['收集同一化学空间的竞争相，统一计算或使用同版本数据库能量。','计算凸包能、分解反应和工作离子化学势范围。','区分热力学窗口、动力学钝化窗口和实验表观窗口。','对温度敏感体系评估振动自由能或说明零温DFT近似。'],
    screening: ['定义元素、凸包能、容量、电压、体积变化与成本等硬筛选条件。','数据库特征先过滤，DFT弛豫、NEB/AIMD再分层投入。','按化学体系或结构原型划分测试集，避免近重复结构泄漏。','最终候选回到高精度计算并给出不确定性、失败模式与可合成性证据。'],
    mlp: ['固定元素、相、缺陷、表面/界面、温压和反应适用域。','用DFT生成覆盖平衡与非平衡构型的能量/力/应力标签，并主动学习补点。','按轨迹、组分与结构家族分组切分，避免相邻帧泄漏。','除MAE外验证RDF、声子/弹性、缺陷能、NEB势垒和扩散系数。','只有通过目标性质验证后才做大体系长时间MLMD，并设置OOD报警。'],
    dft_setup: ['完成赝势、ENCUT、k点、展宽和电子收敛测试，并同时观察总能与目标性质。','根据元素价态和目标性质确定磁序、DFT+U、范德华修正与自旋轨道耦合。','分开设置弛豫、高精度静态计算和性质后处理。','后处理保留原始VASP输出、软件版本、路径和单位。','用已知材料或文献基准验证晶格、磁矩、能隙或电压。']
  };
  const common = ['定义材料、工作离子、荷电状态、温度和目标性质。','记录结构来源、数据库版本、结构ID和所有计算版本。','按所选方法测试数值精度、有限尺寸与采样误差；不同方法不能共用未经验证的参数模板。'];
  const fieldLabels = {title:'标题',role:'定位',methods:'方法',tags:'标签',systems_properties:'体系/性质',summary_evidence:'摘要/证据',doi:'DOI'};

  function triggered(text, trigger) {
    return /^[a-z0-9]+$/i.test(trigger)
      ? new RegExp(`(^|[^a-z0-9])${trigger.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^a-z0-9]|$)`, 'i').test(text)
      : text.includes(trigger);
  }
  function tokens(text) { return (String(text).toLowerCase().match(/[a-z][a-z0-9+_.:/-]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]{2,}/g) || []); }
  function flatten(value) {
    if (Array.isArray(value)) return value.map(flatten).join(' ');
    if (value && typeof value === 'object') return Object.values(value).map(flatten).join(' ');
    return String(value || '');
  }
  function fields(p) {
    return {
      title: flatten(p.title).toLowerCase(), role: flatten(p.role).toLowerCase(), methods: flatten(p.methods).toLowerCase(),
      tags: flatten([p.tags_zh, p.display_tags]).toLowerCase(), systems_properties: flatten([p.systems, p.properties]).toLowerCase(),
      summary_evidence: flatten([p.summary,p.evidence,p.protocol_steps,p.scope_note]).toLowerCase()
    };
  }
  function parseFilters(query) {
    const tags = [...query.matchAll(/(?:tag|标签)\s*[:：]\s*(MS|DFT|MD|VASP)\b/gi)].map(m => m[1].toUpperCase());
    const types = [...query.matchAll(/(?:type|类型)\s*[:：]\s*(方法论文|进展论文|综述)/gi)].map(m => m[1]);
    const clean = query.replace(/(?:tag|标签)\s*[:：]\s*(?:MS|DFT|MD|VASP)\b/gi, ' ').replace(/(?:type|类型)\s*[:：]\s*(?:方法论文|进展论文|综述)/gi, ' ').replace(/\s+/g, ' ').trim();
    return {clean, filters:{tags:[...new Set(tags)], types:[...new Set(types)]}};
  }
  function expand(query) {
    const added = [];
    Object.entries(aliases).forEach(([key, values]) => { if (triggered(query.toLowerCase(), key)) added.push(...values); });
    return {text:[query, ...added].join(' '), added:[...new Set(added)]};
  }
  function taskType(q) {
    const text = q.toLowerCase();
    return (taskRules.find(([, words]) => words.some(word => triggered(text, word))) || ['general'])[0];
  }
  function searchDetailed(query, papers, limit=5, config={}) {
    const weights = {...defaultWeights, ...(config.weights || {})};
    const parsed = parseFilters(String(query || ''));
    const expanded = expand(parsed.clean);
    const original = new Set(tokens(parsed.clean));
    const queryTokens = tokens(expanded.text);
    const documentFields = papers.map(fields);
    const documents = documentFields.map(row => tokens(Object.values(row).join(' ')));
    const df = {};
    documents.forEach(row => [...new Set(row)].forEach(token => { df[token] = (df[token] || 0) + 1; }));
    const idf = token => Math.log((papers.length + 1) / ((df[token] || 0) + 1)) + 1;
    const scored = [];
    papers.forEach((paper, index) => {
      const displayTags = new Set(paper.display_tags || []);
      if (parsed.filters.tags.length && !parsed.filters.tags.every(tag => displayTags.has(tag))) return;
      if (parsed.filters.types.length && !parsed.filters.types.every(tag => displayTags.has(tag))) return;
      let score = (parsed.filters.tags.length || parsed.filters.types.length) ? 0.001 : 0;
      const hits = {};
      Object.entries(documentFields[index]).forEach(([field, text]) => {
        const counts = {}; tokens(text).forEach(token => { counts[token] = (counts[token] || 0) + 1; });
        const fieldHits = [];
        queryTokens.forEach(token => {
          if (!counts[token]) return;
          const factor = original.has(token) ? 1 : weights.alias_factor;
          score += weights[field] * factor * (1 + Math.log(counts[token])) * idf(token);
          fieldHits.push(token);
        });
        expanded.added.filter(term => term.includes(' ') && text.includes(term)).forEach(term => { score += weights[field] * weights.alias_factor; fieldHits.push(term); });
        if (fieldHits.length) hits[field] = [...new Set(fieldHits)].slice(0,8);
      });
      const allText = Object.values(documentFields[index]).join(' ');
      if (parsed.clean && allText.includes(parsed.clean.toLowerCase())) score += weights.phrase_bonus;
      if (paper.doi && String(query).toLowerCase().includes(String(paper.doi).toLowerCase())) { score += weights.doi_bonus; hits.doi = [String(paper.doi).toLowerCase()]; }
      if (score <= 0) return;
      const matchedTerms = [...new Set(Object.values(hits).flat())].slice(0,8);
      const matchedFields = Object.keys(hits).map(field => fieldLabels[field] || field);
      const reason = [
        parsed.filters.tags.length ? `满足标签 ${parsed.filters.tags.join('/')}` : '', parsed.filters.types.length ? `满足类型 ${parsed.filters.types.join('/')}` : '',
        matchedFields.length ? `命中${matchedFields.join('、')}` : '', matchedTerms.length ? `关键词：${matchedTerms.slice(0,5).join(' / ')}` : ''
      ].filter(Boolean).join('；') || '满足筛选条件';
      scored.push({...paper, retrieval:{score:Number(score.toFixed(4)),matched_terms:matchedTerms,matched_fields:matchedFields,reason}});
    });
    scored.sort((a,b) => b.retrieval.score-a.retrieval.score || (b.year || 0)-(a.year || 0));
    return {results:scored.slice(0,limit),query:{original:query,clean:parsed.clean,expanded_terms:expanded.added,filters:parsed.filters,mode:'explainable_weighted_retrieval'}};
  }
  function search(query, papers, limit=5, config={}) { return searchDetailed(query,papers,limit,config).results; }
  function citation(p, i) {
    const wos = p.wos_uid ? `；[WOS记录](https://www.webofscience.com/wos/woscc/full-record/${p.wos_uid})` : '';
    const doi = p.doi ? ` DOI: [${p.doi}](https://doi.org/${p.doi})` : '';
    return `[${i}] ${(p.authors || ['Unknown'])[0]} 等, ${p.year || '未知年份'}, *${p.title}*, ${p.journal || '来源待补充'}.${doi}${wos}`;
  }
  function answer(question, papers, config={}) {
    const task = taskType(question);
    const retrieval = searchDetailed(question, papers, 5, config);
    const found = retrieval.results;
    const lower = question.toLowerCase();
    const guidance = (config.answer_guidance || []).find(card => card.all_of.every(group => group.some(term => triggered(lower, term))));
    const wantsPlan = ['怎么','如何','方案','路线','流程','计划','workflow','复现'].some(w => lower.includes(w));
    const wantsCompare = ['比较','区别','还是','对比','vs'].some(w => lower.includes(w));
    const intent = wantsPlan ? '工作流' : wantsCompare ? '对比' : '证据检索';
    const filterLabels = [...retrieval.query.filters.tags, ...retrieval.query.filters.types];
    const lead = guidance ? guidance.answer : found.length ? leads[task] : '当前没有匹配的论文证据，不能据此给出材料结论或计算参数。';
    const lines = ['### 检索理解','',`- **意图**：${intent}；**任务**：${task}。`,`- **查询扩展**：${retrieval.query.expanded_terms.slice(0,8).join(' / ') || '无'}。`,`- **显式筛选**：${filterLabels.join(' / ') || '无'}。`,'','### 结论','',lead];
    if (guidance) {
      lines.push('', '### 方法解释与下一步（教学规则，非论文全文推断）', '');
      guidance.steps.forEach((s,i) => lines.push(`${i+1}. ${s}`));
      lines.push('', '需要补充：' + guidance.ask, '', '参考：' + guidance.sources.map(s => `[${s.label}](${s.url})`).join(' · '));
    }
    if (!found.length) {
      lines.push('', '当前证据库没有达到最低匹配条件的论文，因此不自动拿最新论文填充答案。请增加“材料＋任务＋方法＋输出量”，或使用 `tag:DFT`、`tag:MD`、`tag:VASP`、`type:方法论文`。');
    } else if (guidance) {
      lines.push('', '相关论文用于继续查阅，不能仅凭关键词命中当作对上述每句话的验证。');
    } else if (wantsCompare && found.length >= 2) {
      lines.push('', '### 对比抓手', ''); found.slice(0,3).forEach((p,i) => lines.push(`- **${p.role}**：${p.summary} 〔${i+1}〕`));
    } else if (wantsPlan) {
      lines.push('', `### 可执行工作流：${task}`, ''); [...common, ...workflows[task]].forEach((step,i) => lines.push(`${i+1}. ${step}`));
    } else {
      lines.push('', '### 文献证据', ''); found.forEach((p,i) => lines.push(`- **〔${i+1}〕${p.role}**：${p.evidence?.[0]?.claim || p.summary}`));
    }
    if (found.length) {
      lines.push('', '### 为什么命中', ''); found.forEach((p,i) => lines.push(`- **〔${i+1}〕${p.title}**：${p.retrieval.reason}（分数 ${p.retrieval.score}）。`));
      lines.push('', '### 证据来源', ''); found.forEach((p,i) => lines.push('- ' + citation(p,i+1)));
    }
    lines.push('', '### 边界与下一步', '', '这是可解释检索与规则工作流，不是自由生成式大模型。具体INCAR/KPOINTS、U值、赝势、超胞和温度必须回到全文/补充信息并重新收敛。');
    const wosCount = papers.filter(p => p.wos_uid).length;
    const starterCount = papers.filter(p => p.collection === 'starter').length;
    return {question,task,guidance_id:guidance?.id || null,answer_markdown:lines.join('\n'),papers:found,retrieval:retrieval.query,rag:{enabled:false,used:false,reason:'static_mode'},provenance:{wos_note:`当前 ${papers.length} 篇：${wosCount} 篇核心论文已取得 WOS UT，${starterCount} 篇方法路线论文已核对 DOI 与出版社记录；静态版不包含受版权保护的 PDF。`}};
  }
  window.BatteryBrowserAgent = {answer,search,searchDetailed,taskType};
})();
