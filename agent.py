"""Evidence-grounded research assistant for computational battery materials.

The first version deliberately works without an external LLM.  It retrieves from a
curated evidence store and composes auditable answers/workflows.  This makes every
claim inspectable and gives a stable base for adding an LLM later without letting it
invent papers or calculation parameters.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from library_store import USER_PAPERS, load_library_papers
from paper_tagging import attach_tags
from rag import EvidenceRAG


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "papers.json"
DEFAULT_FULLTEXT = ROOT / "data" / "fulltext_chunks.jsonl"
DEFAULT_SEARCH_CONFIG = ROOT / "data" / "search_config.json"

DEFAULT_SEARCH_WEIGHTS = {
    "title": 6.0,
    "role": 4.5,
    "methods": 5.0,
    "tags": 4.0,
    "systems_properties": 2.5,
    "summary_evidence": 1.5,
    "phrase_bonus": 8.0,
    "alias_factor": 0.65,
    "doi_bonus": 50.0,
}


ALIASES = {
    "第一性原理": ["dft", "first-principles", "density functional"],
    "反应识别": ["automatic reaction identification", "reaction sequence"],
    "均方位移": ["msd", "diffusion", "molecular dynamics"],
    "微调": ["fine-tuning", "transfer learning", "MACE-freeze"],
    "不确定性": ["uncertainty", "quantile regression", "readout ensemble"],
    "电压": ["voltage", "intercalation", "total energy", "thermodynamic"],
    "开路电压": ["voltage", "open circuit voltage", "intercalation"],
    "扩散": ["diffusion", "migration", "barrier", "neb", "aimd", "msd"],
    "迁移": ["diffusion", "migration", "barrier", "neb"],
    "势垒": ["barrier", "migration", "neb", "ci-neb"],
    "分子动力学": ["molecular dynamics", "md", "aimd", "trajectory", "msd"],
    "机器学习势": ["machine-learning potential", "neural network potential", "m3gnet", "chgnet", "deepmd", "dp-gen", "nequip", "allegro", "gap", "nnp", "mlip"],
    "神经网络势": ["neural network potential", "nnp", "mlip", "deepmd", "nequip", "allegro"],
    "主动学习": ["active learning", "concurrent learning", "dp-gen", "model deviation"],
    "稳定性": ["stability", "phase diagram", "electrochemical window", "energy above hull"],
    "界面": ["interface", "sei", "electrode-electrolyte", "surface"],
    "固态电解质": ["solid electrolyte", "superionic", "lgps", "argyrodite", "ionic conductivity"],
    "正极": ["cathode", "intercalation", "layered oxide"],
    "负极": ["anode", "sei", "lithium metal"],
    "缺陷": ["defect", "vacancy", "interstitial", "chemical potential"],
    "高通量": ["high-throughput", "screening", "classifier", "materials project", "atomate2", "aiida"],
    "钠": ["sodium", "na-ion", "na"],
    "锂": ["lithium", "li-ion", "li"],
    "文献": ["paper", "review", "article", "doi"],
    "入门": ["starter", "protocol", "vaspkit", "pymatgen", "ase", "sumo", "lammps", "dscribe", "matbench"],
    "声子": ["phonon", "phonopy", "finite displacement", "force constants"],
    "后处理": ["post-processing", "vaspkit", "sumo", "band structure", "dos"],
    "反应力场": ["reaxff", "reactive molecular dynamics", "force-field training"],
    "溶剂化": ["solvation", "coordination", "radial distribution"],
    "电解液": ["electrolyte", "solvent", "salt"],
    "双电层": ["electric double layer", "edl", "charged interface"],
    "相场": ["phase-field", "continuum modeling", "sei growth"],
    "多尺度": ["multiscale", "phase-field", "continuum modeling"],
    "聚合物电解质": ["polymer electrolyte", "solid polymer electrolyte", "spe"],
    "水解": ["hydrolysis", "water-containing electrolyte"],
    "厚度演化": ["phase-field", "sei growth", "continuum modeling"],
    "纳秒到秒": ["multiscale", "phase-field", "time scales"],
    "点缺陷": ["point defect", "pymatgen-analysis-defects", "defect formation energy"],
    "一万多个晶体": ["high-throughput", "screening", "12,000", "classifier"],
    "小数据": ["small data", "few-shot", "fine-tuning", "transfer learning"],
    "迁移学习": ["transfer learning", "fine-tuning", "MACE-freeze"],
    "风险判断": ["uncertainty", "calibration", "overconfidence"],
    "锂硫": ["lithium-sulfur", "li-s", "reaxff"],
    "硅负极": ["silicon anode", "reaxff"],
    # The suite name should match every MS paper without guessing a particular
    # module.  Module names stay as explicit user terms when they matter.
    "materials studio": ["biovia materials studio"],
    "dft": ["density functional", "first-principles", "total energy"],
    "vasp": ["incar", "kpoints", "potcar", "plane-wave"],
    "aimd": ["ab initio molecular dynamics", "molecular dynamics", "msd", "diffusion"],
    "md": ["molecular dynamics", "trajectory", "msd"],
    "ms": ["materials studio"],
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+_.:/-]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]{2,}")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    return str(value)


def _triggered(text: str, trigger: str) -> bool:
    """Match Chinese aliases as substrings and short ASCII aliases as words."""
    if trigger.isascii():
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(trigger)}(?![a-z0-9])", text, re.I))
    return trigger in text


class BatteryResearchAgent:
    def __init__(
        self,
        data_path: str | Path = DEFAULT_DATA,
        fulltext_path: str | Path | None = DEFAULT_FULLTEXT,
        extra_data_path: str | Path | None = USER_PAPERS,
        search_config_path: str | Path | None = DEFAULT_SEARCH_CONFIG,
        search_weights: dict[str, float] | None = None,
        rag: EvidenceRAG | None = None,
    ):
        self.data_path = Path(data_path)
        self.extra_data_path = Path(extra_data_path) if extra_data_path else None
        self.search_config_path = Path(search_config_path) if search_config_path else None
        self.papers: list[dict[str, Any]] = attach_tags(
            load_library_papers(self.data_path, self.extra_data_path)
        )
        self.search_config = self._load_search_config(search_weights)
        self.search_weights = self.search_config["weights"]
        self.answer_guidance = json.loads((ROOT / "data" / "answer_guidance.json").read_text(encoding="utf-8"))
        self.rag = rag or EvidenceRAG.from_environment()
        self._search_fields = [self._paper_search_fields(paper) for paper in self.papers]
        self._documents = [_flatten(paper).lower() for paper in self.papers]
        self._doc_tokens = [Counter(_tokens(document)) for document in self._documents]
        self._idf = self._build_idf()
        self.fulltext_path = Path(fulltext_path) if fulltext_path else None
        self.fulltext_chunks = self._load_fulltext()
        self._chunk_tokens = [Counter(_tokens(row.get("text", ""))) for row in self.fulltext_chunks]
        self._chunk_idf = self._build_idf_for(self._chunk_tokens)

    def reload(self) -> None:
        """Reload paper metadata and the full-text index after local ingestion."""
        self.__init__(
            self.data_path,
            self.fulltext_path,
            self.extra_data_path,
            self.search_config_path,
        )

    def _load_search_config(self, override: dict[str, float] | None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.search_config_path and self.search_config_path.exists():
            try:
                raw = json.loads(self.search_config_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    payload = raw
            except (OSError, json.JSONDecodeError):
                payload = {}
        weights = {**DEFAULT_SEARCH_WEIGHTS, **payload.get("weights", {})}
        if override:
            weights.update(override)
        return {
            **payload,
            "schema_version": payload.get("schema_version", 1),
            "mode": "explainable_weighted_retrieval",
            "weights": weights,
        }

    @staticmethod
    def _paper_search_fields(paper: dict[str, Any]) -> dict[str, str]:
        return {
            "title": _flatten(paper.get("title", "")).lower(),
            "role": _flatten(paper.get("role", "")).lower(),
            "methods": _flatten(paper.get("methods", [])).lower(),
            "tags": _flatten(
                [paper.get("tags_zh", []), paper.get("display_tags", [])]
            ).lower(),
            "systems_properties": _flatten(
                [paper.get("systems", []), paper.get("properties", [])]
            ).lower(),
            "summary_evidence": _flatten(
                [
                    paper.get("summary", ""),
                    paper.get("evidence", []),
                    paper.get("protocol_steps", []),
                    paper.get("scope_note", ""),
                ]
            ).lower(),
        }

    def _build_idf(self) -> dict[str, float]:
        return self._build_idf_for(self._doc_tokens)

    @staticmethod
    def _build_idf_for(tokenized_documents: list[Counter[str]]) -> dict[str, float]:
        counts: Counter[str] = Counter()
        for token_counts in tokenized_documents:
            counts.update(token_counts.keys())
        n_docs = max(len(tokenized_documents), 1)
        return {token: math.log((n_docs + 1) / (count + 1)) + 1 for token, count in counts.items()}

    def _load_fulltext(self) -> list[dict[str, Any]]:
        if not self.fulltext_path or not self.fulltext_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.fulltext_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("paper_id") and row.get("text"):
                rows.append(row)
        return rows

    def _expanded_query_parts(self, question: str) -> tuple[str, list[str]]:
        expanded = [question]
        added: list[str] = []
        lowered = question.lower()
        for trigger, terms in ALIASES.items():
            if _triggered(lowered, trigger):
                expanded.extend(terms)
                added.extend(terms)
        return " ".join(expanded), list(dict.fromkeys(added))

    def _expanded_query(self, question: str) -> str:
        return self._expanded_query_parts(question)[0]

    @staticmethod
    def _parse_filters(query: str) -> tuple[str, dict[str, list[str]]]:
        tag_filters = re.findall(r"(?:tag|标签)\s*[:：]\s*(MS|DFT|MD|VASP)\b", query, re.I)
        kind_filters = re.findall(r"(?:type|类型)\s*[:：]\s*(方法论文|进展论文|综述)", query, re.I)
        clean = re.sub(r"(?:tag|标签)\s*[:：]\s*(?:MS|DFT|MD|VASP)\b", " ", query, flags=re.I)
        clean = re.sub(r"(?:type|类型)\s*[:：]\s*(?:方法论文|进展论文|综述)", " ", clean, flags=re.I)
        return re.sub(r"\s+", " ", clean).strip(), {
            "tags": list(dict.fromkeys(tag.upper() for tag in tag_filters)),
            "types": list(dict.fromkeys(kind_filters)),
        }

    def search_detailed(self, query: str, limit: int = 5) -> dict[str, Any]:
        clean_query, filters = self._parse_filters(query)
        expanded, alias_terms = self._expanded_query_parts(clean_query)
        original_tokens = set(_tokens(clean_query))
        expanded_tokens = Counter(_tokens(expanded))
        weights = self.search_weights
        scored: list[tuple[float, dict[str, Any]]] = []
        for paper, fields in zip(self.papers, self._search_fields):
            display_tags = set(paper.get("display_tags", []))
            if filters["tags"] and not all(tag in display_tags for tag in filters["tags"]):
                continue
            if filters["types"] and not all(tag in display_tags for tag in filters["types"]):
                continue
            score = 0.001 if any(filters.values()) else 0.0
            hits: dict[str, list[str]] = {}
            for field, document in fields.items():
                field_hits: list[str] = []
                field_weight = float(weights.get(field, 1.0))
                token_counts = Counter(_tokens(document))
                for token, q_count in expanded_tokens.items():
                    frequency = token_counts.get(token, 0)
                    if not frequency:
                        continue
                    factor = 1.0 if token in original_tokens else float(weights.get("alias_factor", 0.65))
                    score += field_weight * factor * (1 + math.log(frequency)) * self._idf.get(token, 1.0) * q_count
                    field_hits.append(token)
                # Multi-word alias phrases carry meaning that token matching can dilute.
                for phrase in alias_terms:
                    if " " in phrase and phrase in document:
                        score += field_weight * float(weights.get("alias_factor", 0.65))
                        field_hits.append(phrase)
                if field_hits:
                    hits[field] = list(dict.fromkeys(field_hits))[:8]
            lowered_doc = " ".join(fields.values())
            if clean_query and clean_query.lower() in lowered_doc:
                score += float(weights.get("phrase_bonus", 8.0))
            doi = str(paper.get("doi", "")).lower()
            if doi and doi in query.lower():
                score += float(weights.get("doi_bonus", 50.0))
                hits["doi"] = [doi]
            if score <= 0:
                continue
            matched_terms = list(dict.fromkeys(term for terms in hits.values() for term in terms))[:8]
            field_labels = {
                "title": "标题", "role": "定位", "methods": "方法", "tags": "标签",
                "systems_properties": "体系/性质", "summary_evidence": "摘要/证据", "doi": "DOI",
            }
            matched_fields = [field_labels.get(field, field) for field in hits]
            reason_parts = []
            if filters["tags"]:
                reason_parts.append("满足标签 " + "/".join(filters["tags"]))
            if filters["types"]:
                reason_parts.append("满足类型 " + "/".join(filters["types"]))
            if matched_fields:
                reason_parts.append("命中" + "、".join(matched_fields))
            if matched_terms:
                reason_parts.append("关键词：" + " / ".join(matched_terms[:5]))
            enriched = {
                **paper,
                "retrieval": {
                    "score": round(score, 4),
                    "matched_terms": matched_terms,
                    "matched_fields": matched_fields,
                    "reason": "；".join(reason_parts) or "满足筛选条件",
                },
            }
            scored.append((score, enriched))
        scored.sort(key=lambda row: (row[0], row[1].get("year", 0)), reverse=True)
        return {
            "results": [paper for _, paper in scored[:limit]],
            "query": {
                "original": query,
                "clean": clean_query,
                "expanded_terms": alias_terms,
                "filters": filters,
                "mode": self.search_config.get("mode", "explainable_weighted_retrieval"),
            },
        }

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return self.search_detailed(query, limit)["results"]

    @staticmethod
    def _short_excerpt(text: str, query_tokens: set[str], max_words: int = 24) -> str:
        words = re.findall(r"\S+", re.sub(r"\s+", " ", text).strip())
        if not words:
            return ""
        lowered = [re.sub(r"[^a-zA-Z0-9+_.:/-]", "", word).lower() for word in words]
        hit = next((i for i, word in enumerate(lowered) if word in query_tokens), 0)
        start = max(0, hit - max_words // 3)
        end = min(len(words), start + max_words)
        prefix = "…" if start else ""
        suffix = "…" if end < len(words) else ""
        return prefix + " ".join(words[start:end]) + suffix

    def search_fulltext(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        """Return page-level hits from locally downloaded PDFs only."""
        if not self.fulltext_chunks:
            return []
        expanded = self._expanded_query(query)
        query_counts = Counter(_tokens(expanded))
        query_set = set(query_counts)
        scored: list[tuple[float, dict[str, Any]]] = []
        for row, token_counts in zip(self.fulltext_chunks, self._chunk_tokens):
            score = 0.0
            for token, q_count in query_counts.items():
                frequency = token_counts.get(token, 0)
                if frequency:
                    score += (1 + math.log(frequency)) * self._chunk_idf.get(token, 1.0) * q_count
            if query.strip().lower() in row.get("text", "").lower():
                score += 8
            if row.get("section") == "references":
                score *= 0.08
            if score > 0:
                hit = {key: value for key, value in row.items() if key != "text"}
                hit["score"] = round(score, 4)
                hit["excerpt"] = self._short_excerpt(row.get("text", ""), query_set)
                hit["local_pdf_url"] = f"/local-pdf/{row['paper_id']}.pdf#page={row.get('page', 1)}"
                scored.append((score, hit))
        scored.sort(key=lambda pair: (pair[0], -int(pair[1].get("page", 0))), reverse=True)
        selected: list[dict[str, Any]] = []
        per_paper: Counter[str] = Counter()
        for _, hit in scored:
            paper_id = str(hit.get("paper_id"))
            if per_paper[paper_id] >= 1:
                continue
            selected.append(hit)
            per_paper[paper_id] += 1
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def citation(paper: dict[str, Any], index: int) -> str:
        first_author = paper.get("authors", ["Unknown"])[0]
        citation = (
            f"[{index}] {first_author} 等, {paper.get('year', '未知年份')}, "
            f"*{paper['title']}*, {paper.get('journal', '来源待补充')}."
        )
        if paper.get("doi"):
            citation += f" DOI: [{paper['doi']}](https://doi.org/{paper['doi']})"
        if paper.get("wos_uid"):
            citation += f"；[WOS记录](https://www.webofscience.com/wos/woscc/full-record/{paper['wos_uid']})"
        return citation

    @staticmethod
    def _task_type(question: str) -> str:
        lowered = question.lower()
        rules = [
            ("mlp", ["机器学习势", "神经网络势", "mlip", "m3gnet", "chgnet", "mace", "deepmd", "nnp"]),
            ("interface", ["界面", "sei", "电解液", "表面", "electrode-electrolyte"]),
            ("diffusion", ["扩散", "迁移", "势垒", "neb", "aimd", "msd", "电导率"]),
            ("voltage", ["电压", "容量", "嵌锂", "脱锂", "开路"]),
            ("stability", ["稳定性", "相图", "凸包", "分解", "电化学窗口"]),
            ("dft_setup", ["dft", "vasp", "incar", "kpoints", "potcar", "截断能", "k点", "赝势", "第一性原理"]),
            ("md_setup", ["md", "分子动力学", "lammps", "forcite", "compass", "nvt", "npt", "rdf"]),
            ("screening", ["筛选", "高通量", "候选", "数据库"]),
        ]
        for name, words in rules:
            if any(_triggered(lowered, word) for word in words):
                return name
        return "general"

    def workflow(self, question: str) -> dict[str, Any]:
        task = self._task_type(question)
        common = [
            "定义材料、工作离子、荷电状态、温度和目标性质；不要从软件参数开始倒推问题。",
            "从论文补充信息或可信晶体库取得结构，保留来源、数据库版本和结构ID。",
            "按所选方法测试数值精度、有限尺寸与采样误差；不同方法不能共用未经验证的参数模板。",
            "保存输入、软件版本、赝势标识、原始输出和后处理脚本，失败计算也要记录。",
        ]
        specific = {
            "general": ["补充材料、目标性质与已有计算条件后，再选择DFT、MD或数据驱动路线。"],
            "md_setup": ["选择覆盖元素、物相、温压和成键模式的力场，并核对电荷、原子类型与单位。", "消除不合理接触并平衡温度与密度；根据研究目的选择NVT/NPT，不把平衡段计入生产统计。", "测试时间步长、体系大小、轨迹时长和独立初态，输出能量、温度、结构与轨迹。", "分开解释RDF/配位数的结构信息和MSD/相关函数的动力学信息。"],
            "voltage": [
                "枚举相邻稳定嵌入组分或占位构型，分别进行自旋极化结构弛豫和静态总能计算。",
                "构建组分—能量凸包，避免用两个亚稳端点直接画成虚假的电压平台。",
                "按 ΔG≈ΔE 计算平均电压，并对金属参比相、磁序、DFT+U和O2相关误差做敏感性分析。",
                "与至少一个实验电压平台或高质量已发表计算交叉验证。",
            ],
            "diffusion": [
                "先确认载流缺陷（空位/间隙/协同机制）和可能通道；稀释极限NEB并不自动代表真实浓度。",
                "NEB：建立足够大超胞，生成连续中间像，逐像检查原子映射并进行弹簧数与超胞收敛。",
                "AIMD/MLMD：用多个温度和独立初态，统计MSD线性区、有效跃迁数及误差，再做Arrhenius外推。",
                "若要求电导率，同时考虑载流子浓度、Haven比/相关运动和Nernst–Einstein假设的适用性。",
            ],
            "interface": [
                "先用相图/反应能判断热力学相容性，再决定是否值得构建显式界面。",
                "枚举低指数表面、终止方式和晶格匹配；报告应变、面积、真空层、偶极修正与有限尺寸效应。",
                "静态DFT回答粘附/电荷转移，AIMD或反应型ML势回答有限温度反应；两者结论不可混写。",
                "对SEI/CEI成分建立缺陷形成能＋NEB＋化学势/电压的闭环。",
            ],
            "stability": [
                "收集同一化学空间内的竞争相，统一计算或使用同一版本数据库能量。",
                "计算能量高于凸包、分解反应和工作离子化学势范围；区分动力学亚稳与热力学稳定。",
                "把稳定窗口分成热力学窗口、动力学钝化窗口与实验表观窗口，禁止直接等同。",
                "对温度敏感体系评估振动自由能或至少说明零温DFT近似。",
            ],
            "screening": [
                "定义硬筛选条件：元素禁限、形成能/凸包能、理论容量、电压范围、体积变化与成本代理。",
                "用廉价数据库特征先过滤，再把DFT弛豫、NEB/AIMD分层分配给候选。",
                "按化学体系或结构原型划分训练/测试集，防止近重复结构造成数据泄漏。",
                "最终候选必须回到高精度计算，并给出不确定性、失败模式和实验可合成性证据。",
            ],
            "mlp": [
                "固定适用域：元素、相、缺陷、表面/界面、温压范围和反应是否允许。",
                "用DFT生成覆盖平衡与非平衡构型的能量/力/应力标签；主动学习补充高不确定构型。",
                "按轨迹、组分和结构家族分组切分数据，避免同一轨迹相邻帧同时进入训练与测试。",
                "除MAE外验证RDF、声子/弹性、缺陷能、NEB势垒、扩散系数与崩溃测试。",
                "只有通过目标性质验证后才进行大体系长时间MLMD，并保留超出适用域的报警阈值。",
            ],
            "dft_setup": [
                "先用原始晶胞完成赝势、ENCUT、k点、展宽方法与电子收敛测试，并记录总能和目标性质的共同收敛。",
                "再确定磁性初态、DFT+U、范德华修正与自旋轨道耦合；这些选择必须由元素价态和目标性质驱动。",
                "按“弛豫→高精度静态计算→性质后处理”分开设置任务，避免直接用弛豫精度解释能带、态密度或微小能差。",
                "用 VASPKIT、pymatgen 或 sumo 做后处理时保留原始 VASP 输出，并检查软件版本、路径和单位约定。",
                "最后用已知材料或文献基准验证晶格常数、磁矩、能隙/电压等目标量，再迁移到新体系。",
            ],
        }
        checks = {
            "general": ["材料明确", "目标量明确", "方法适用性"],
            "md_setup": ["力场适用域", "电荷与单位", "平衡段剔除", "时间步长", "独立轨迹与误差"],
            "voltage": ["能量/原子与力收敛", "磁序和U值敏感性", "凸包端点正确", "参比相一致"],
            "diffusion": ["跃迁通道完整", "独立轨迹", "有效跃迁数", "MSD拟合窗口", "有限尺寸"],
            "interface": ["终止面与匹配枚举", "界面应变", "反应产物", "时间尺度", "电势对齐"],
            "stability": ["竞争相完整", "数据库版本一致", "零温近似说明", "动力学/热力学区分"],
            "screening": ["数据去重", "分组外推测试", "不确定性", "负样本", "最终DFT复核"],
            "mlp": ["OOD检测", "能量/力/应力", "目标性质", "长时稳定性", "主动学习停止准则"],
            "dft_setup": ["ENCUT/k点收敛", "赝势一致", "磁序/U值", "静态与弛豫分离", "原始输出可追溯"],
        }
        return {"task": task, "steps": common + specific[task], "checks": checks[task]}

    def graph(self, papers: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
        nodes: dict[str, dict[str, str]] = {}
        edges: list[dict[str, str]] = []
        for paper in papers:
            paper_id = paper["id"]
            nodes[paper_id] = {"id": paper_id, "label": f"{paper['year']} · {paper['role']}", "kind": "paper"}
            for relation in paper.get("relations", []):
                source_id = f"entity:{relation['source']}"
                target_id = f"entity:{relation['target']}"
                nodes[source_id] = {"id": source_id, "label": relation["source"], "kind": "entity"}
                nodes[target_id] = {"id": target_id, "label": relation["target"], "kind": "property"}
                edges.append({"source": source_id, "relation": relation["relation"], "target": target_id, "paper": paper_id})
        return {"nodes": list(nodes.values()), "edges": edges}

    def answer(self, question: str, limit: int = 5, use_rag: bool = True) -> dict[str, Any]:
        question = question.strip()
        if not question:
            question = "电池材料计算有哪些核心任务？"
        retrieval = self.search_detailed(question, limit=limit)
        papers = retrieval["results"]
        fulltext_hits = self.search_fulltext(question, limit=min(limit + 1, 8))
        task = self._task_type(question)
        wants_plan = any(word in question.lower() for word in ["怎么", "如何", "方案", "路线", "流程", "计划", "workflow", "复现"])
        wants_compare = any(word in question.lower() for word in ["比较", "区别", "还是", "对比", "vs"])

        lead = {
            "general": "请先明确材料、目标性质和已有数据；当前问题不足以指定唯一计算路线。",
            "md_setup": "MD先确认力的来源、力场适用域、平衡与采样，再解释结构或输运性质；经典MD并不需要照抄VASP的ENCUT与k点。",
            "voltage": "电压问题应以不同嵌入组分的稳定相和一致设置下的总能为核心，而不是只算一个端点。",
            "diffusion": "扩散问题先分清‘单跳势垒’与‘有限温度扩散系数’：NEB适合前者，AIMD/MLMD适合后者。",
            "interface": "界面问题建议先做反应热力学，再做显式界面；否则很容易在一个本就会分解的界面上过度解释电荷密度。",
            "stability": "稳定性至少分为体相、相对竞争相、电化学窗口和界面反应四层，不能用单一形成能替代。",
            "screening": "高通量最有效的做法是分层筛选：便宜指标先缩小空间，昂贵DFT动力学最后验证。",
            "mlp": "机器学习势的价值是把DFT精度近似扩展到更大体系和更长时间，但适用域验证比模型名称更重要。",
            "dft_setup": "VASP/DFT 入门应先建立一套可复现的收敛与验证流程，再计算电压、扩散或界面；软件参数不能脱离材料和目标性质单独照抄。",
        }[task]
        guidance = next((card for card in self.answer_guidance if all(any(_triggered(question.lower(), term) for term in group) for group in card["all_of"])), None)
        if guidance:
            lead = guidance["answer"]
        elif not papers:
            lead = "当前没有匹配的论文证据，不能据此给出材料结论或计算参数。"

        query_info = retrieval["query"]
        intent = "工作流" if wants_plan else "对比" if wants_compare else "证据检索"
        filter_labels = query_info["filters"]["tags"] + query_info["filters"]["types"]
        lines = [
            "### 检索理解",
            "",
            f"- **意图**：{intent}；**任务**：{task}。",
            f"- **查询扩展**：{' / '.join(query_info['expanded_terms'][:8]) if query_info['expanded_terms'] else '无'}。",
            f"- **显式筛选**：{' / '.join(filter_labels) if filter_labels else '无'}。",
            "",
            "### 结论",
            "",
            lead,
        ]
        if guidance:
            lines += ["", "### 方法解释与下一步（教学规则，非论文全文推断）", ""]
            lines += [f"{i}. {step}" for i, step in enumerate(guidance["steps"], 1)]
            lines += ["", "需要补充：" + guidance["ask"], "", "参考：" + " · ".join(f"[{s['label']}]({s['url']})" for s in guidance["sources"])]
        rag_result = (
            self.rag.generate(question, papers, fulltext_hits)
            if use_rag
            else {**self.rag.status(), "used": False, "valid_citations": False, "reason": "disabled_for_request"}
        )
        if rag_result.get("used"):
            lines += ["", "### RAG 综合回答", "", rag_result["answer_markdown"]]
        if not papers:
            lines += [
                "",
                "当前证据库没有达到最低匹配条件的论文，因此不自动拿最新论文填充答案。请增加“材料＋任务＋方法＋输出量”，例如“LGPS＋锂扩散＋AIMD＋扩散系数”，或使用 `tag:DFT`、`tag:MD`、`tag:VASP`、`type:方法论文` 缩小范围。",
            ]
        elif guidance:
            lines += ["", "相关论文用于继续查阅，不能仅凭关键词命中当作对上述每句话的验证。"]
        elif wants_compare and len(papers) >= 2:
            lines += ["", "### 对比抓手", ""]
            for index, paper in enumerate(papers[:3], 1):
                lines.append(f"- **{paper['role']}**：{paper['summary']} 〔{index}〕")
        elif wants_plan:
            flow = self.workflow(question)
            lines += ["", f"### 可执行工作流：{flow['task']}", ""]
            for index, step in enumerate(flow["steps"], 1):
                lines.append(f"{index}. {step}")
            lines += ["", "**交付前检查：** " + "；".join(flow["checks"]) + "。"]
        else:
            lines += ["", "### 文献证据", ""]
            for index, paper in enumerate(papers, 1):
                claim = paper.get("evidence", [{}])[0].get("claim", paper["summary"])
                lines.append(f"- **〔{index}〕{paper['role']}**：{claim}")

        if papers:
            lines += ["", "### 为什么命中", ""]
            for index, paper in enumerate(papers, 1):
                lines.append(f"- **〔{index}〕{paper['title']}**：{paper['retrieval']['reason']}（分数 {paper['retrieval']['score']}）。")
            lines += ["", "### 证据来源", ""]
            lines.extend(f"- {self.citation(paper, index)}" for index, paper in enumerate(papers, 1))
        if fulltext_hits:
            lines += ["", "### 本地全文命中（用于回到原文核对）", ""]
            for hit in fulltext_hits:
                lines.append(
                    f"- **{hit['title']}，PDF 第 {hit['page']} 页**：{hit['excerpt']} "
                    f"([打开本地原文]({hit['local_pdf_url']}) · [DOI](https://doi.org/{hit['doi']}))"
                )
        lines += [
            "",
            "### 边界与下一步",
            "",
            "工作流建议来自已入库的论文级证据；上面的全文命中只作为回到原文核对的入口，不自动等同于经过人工复核的结论。具体INCAR/KPOINTS、U值、赝势、超胞和温度不能由题目自动猜定；应在锁定材料、价态与目标性质后，再从原文方法和补充信息抽取并做收敛测试。",
        ]
        wos_count = sum(bool(paper.get("wos_uid")) for paper in self.papers)
        starter_count = sum(paper.get("collection") == "starter" for paper in self.papers)
        return {
            "question": question,
            "task": task,
            "guidance_id": guidance["id"] if guidance else None,
            "answer_markdown": "\n".join(lines),
            "papers": papers,
            "workflow": self.workflow(question) if wants_plan else None,
            "graph": self.graph(papers),
            "fulltext_hits": fulltext_hits,
            "retrieval": query_info,
            "rag": {key: value for key, value in rag_result.items() if key != "answer_markdown"},
            "provenance": {
                "data_file": str(self.data_path),
                "paper_count": len(self.papers),
                "fulltext_file": str(self.fulltext_path) if self.fulltext_path else None,
                "fulltext_paper_count": len({row["paper_id"] for row in self.fulltext_chunks}),
                "fulltext_chunk_count": len(self.fulltext_chunks),
                "wos_note": (
                    f"当前 {len(self.papers)} 篇：{wos_count} 篇核心论文已取得 WOS UT，"
                    f"{starter_count} 篇方法路线论文已核对 DOI 与出版社记录。"
                ),
            },
        }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Battery materials research agent")
    parser.add_argument("question", nargs="*", help="Question in Chinese or English")
    parser.add_argument("--json", action="store_true", help="Print the complete JSON result")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to the paper knowledge base")
    args = parser.parse_args()
    question = " ".join(args.question) or "如何计算固态电解质中的锂离子扩散？"
    result = BatteryResearchAgent(args.data).answer(question)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["answer_markdown"])


if __name__ == "__main__":
    main()
