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


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "papers.json"
DEFAULT_FULLTEXT = ROOT / "data" / "fulltext_chunks.jsonl"


ALIASES = {
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


class BatteryResearchAgent:
    def __init__(
        self,
        data_path: str | Path = DEFAULT_DATA,
        fulltext_path: str | Path | None = DEFAULT_FULLTEXT,
        extra_data_path: str | Path | None = USER_PAPERS,
    ):
        self.data_path = Path(data_path)
        self.extra_data_path = Path(extra_data_path) if extra_data_path else None
        self.papers: list[dict[str, Any]] = load_library_papers(
            self.data_path, self.extra_data_path
        )
        self._documents = [_flatten(paper).lower() for paper in self.papers]
        self._doc_tokens = [Counter(_tokens(document)) for document in self._documents]
        self._idf = self._build_idf()
        self.fulltext_path = Path(fulltext_path) if fulltext_path else None
        self.fulltext_chunks = self._load_fulltext()
        self._chunk_tokens = [Counter(_tokens(row.get("text", ""))) for row in self.fulltext_chunks]
        self._chunk_idf = self._build_idf_for(self._chunk_tokens)

    def reload(self) -> None:
        """Reload paper metadata and the full-text index after local ingestion."""
        self.__init__(self.data_path, self.fulltext_path, self.extra_data_path)

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

    def _expanded_query(self, question: str) -> str:
        expanded = [question]
        lowered = question.lower()
        for trigger, additions in ALIASES.items():
            if trigger in lowered:
                expanded.extend(additions)
        return " ".join(expanded)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        expanded = self._expanded_query(query)
        query_tokens = Counter(_tokens(expanded))
        lowered = expanded.lower()
        scored: list[tuple[float, dict[str, Any]]] = []
        for paper, document, token_counts in zip(self.papers, self._documents, self._doc_tokens):
            score = 0.0
            for token, q_count in query_tokens.items():
                if token in token_counts:
                    score += (1 + math.log(token_counts[token])) * self._idf.get(token, 1.0) * q_count
            for phrase in ALIASES.values():
                for item in phrase:
                    if item in lowered and item in document:
                        score += 1.3
            if str(paper.get("doi", "")).lower() in lowered:
                score += 50
            if score > 0:
                scored.append((score, paper))
        scored.sort(key=lambda row: (row[0], row[1].get("year", 0)), reverse=True)
        if not scored:
            return sorted(self.papers, key=lambda p: p.get("year", 0), reverse=True)[:limit]
        return [paper for _, paper in scored[:limit]]

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
            ("mlp", ["机器学习势", "神经网络势", "mlip", "m3gnet", "deepmd", "nnp"]),
            ("interface", ["界面", "sei", "电解液", "表面", "electrode-electrolyte"]),
            ("diffusion", ["扩散", "迁移", "势垒", "neb", "aimd", "msd", "电导率"]),
            ("voltage", ["电压", "容量", "嵌锂", "脱锂", "开路"]),
            ("stability", ["稳定性", "相图", "凸包", "分解", "电化学窗口"]),
            ("screening", ["筛选", "高通量", "候选", "数据库"]),
        ]
        for name, words in rules:
            if any(word in lowered for word in words):
                return name
        return "screening"

    def workflow(self, question: str) -> dict[str, Any]:
        task = self._task_type(question)
        common = [
            "定义材料、工作离子、荷电状态、温度和目标性质；不要从软件参数开始倒推问题。",
            "从论文补充信息或可信晶体库取得结构，保留来源、数据库版本和结构ID。",
            "先做ENCUT、k点、超胞、磁序和必要的U值收敛；所有比较相必须使用一致设置。",
            "保存输入、软件版本、赝势标识、原始输出和后处理脚本，失败计算也要记录。",
        ]
        specific = {
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
        }
        checks = {
            "voltage": ["能量/原子与力收敛", "磁序和U值敏感性", "凸包端点正确", "参比相一致"],
            "diffusion": ["跃迁通道完整", "独立轨迹", "有效跃迁数", "MSD拟合窗口", "有限尺寸"],
            "interface": ["终止面与匹配枚举", "界面应变", "反应产物", "时间尺度", "电势对齐"],
            "stability": ["竞争相完整", "数据库版本一致", "零温近似说明", "动力学/热力学区分"],
            "screening": ["数据去重", "分组外推测试", "不确定性", "负样本", "最终DFT复核"],
            "mlp": ["OOD检测", "能量/力/应力", "目标性质", "长时稳定性", "主动学习停止准则"],
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

    def answer(self, question: str, limit: int = 5) -> dict[str, Any]:
        question = question.strip()
        if not question:
            question = "电池材料计算有哪些核心任务？"
        papers = self.search(question, limit=limit)
        fulltext_hits = self.search_fulltext(question, limit=min(limit + 1, 8))
        task = self._task_type(question)
        wants_plan = any(word in question.lower() for word in ["怎么", "如何", "方案", "路线", "流程", "计划", "workflow", "复现"])
        wants_compare = any(word in question.lower() for word in ["比较", "区别", "还是", "对比", "vs"])

        lead = {
            "voltage": "电压问题应以不同嵌入组分的稳定相和一致设置下的总能为核心，而不是只算一个端点。",
            "diffusion": "扩散问题先分清‘单跳势垒’与‘有限温度扩散系数’：NEB适合前者，AIMD/MLMD适合后者。",
            "interface": "界面问题建议先做反应热力学，再做显式界面；否则很容易在一个本就会分解的界面上过度解释电荷密度。",
            "stability": "稳定性至少分为体相、相对竞争相、电化学窗口和界面反应四层，不能用单一形成能替代。",
            "screening": "高通量最有效的做法是分层筛选：便宜指标先缩小空间，昂贵DFT动力学最后验证。",
            "mlp": "机器学习势的价值是把DFT精度近似扩展到更大体系和更长时间，但适用域验证比模型名称更重要。",
        }[task]

        lines = ["### 结论", "", lead]
        if wants_compare and len(papers) >= 2:
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
            "answer_markdown": "\n".join(lines),
            "papers": papers,
            "workflow": self.workflow(question) if wants_plan else None,
            "graph": self.graph(papers),
            "fulltext_hits": fulltext_hits,
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
