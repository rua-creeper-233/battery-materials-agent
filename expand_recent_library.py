"""Build the 2026-10-08 DOI-verified literature expansion catalog.

This is deliberately a small, repeatable metadata step: every candidate is
looked up by DOI at Crossref, date-limited, and dropped when Crossref cannot
confirm it.  It never guesses bibliographic fields and never downloads PDFs.
"""
from __future__ import annotations

import json
import argparse
import html
import re
import time
from pathlib import Path
from typing import Any

from urllib.request import Request, urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "paper_expansion_20261008.json"
PAPERS = ROOT / "data" / "papers.json"
CATALOG_OLD = ROOT / "data" / "paper_expansion_20260920.json"
AS_OF = (2026, 10, 8)

# Seeded from the researcher handoff and publisher discovery.  General MLIP,
# workflow, data and uncertainty papers are retained because they are directly
# reusable for battery electrolyte/cathode/interface simulations.
CANDIDATES = [
    "10.1021/acs.jctc.4c00190", "10.1021/jacs.4c14455", "10.1021/acsmaterialslett.5c00093",
    "10.1021/acsmaterialslett.5c00336", "10.1021/acs.chemmater.6c01051", "10.1557/s43579-026-00928-9",
    "10.1038/s41524-026-02023-y", "10.1039/d4ta06675h", "10.1002/adfm.202313188",
    "10.1038/s41467-025-65496-3", "10.1016/j.mechmat.2024.105237", "10.1021/acs.jpcb.6c02837",
    "10.1016/j.est.2026.121104", "10.1038/s41586-023-06735-9", "10.1038/s41467-025-56322-x",
    "10.1016/j.jechem.2025.03.007", "10.1016/j.mtener.2025.101841", "10.1038/s41524-025-01747-7",
    "10.1038/s41524-025-01615-4", "10.1038/s41467-025-62824-5", "10.1016/j.jpowsour.2025.237670",
    "10.1039/d5cc04921k", "10.1039/d6eb00024j", "10.1016/j.ensm.2025.104826",
    "10.1039/d4ta03452j", "10.1103/physrevmaterials.8.115407", "10.1038/s41524-024-01332-4",
    "10.1038/s41524-024-01227-4", "10.1038/s41524-025-01623-4", "10.1038/s41467-025-63852-x",
    "10.1038/s41467-025-67663-y", "10.1038/s41524-025-01735-x", "10.1038/s41524-025-01911-z",
    "10.1038/s41524-024-01222-9", "10.1038/s41524-025-01650-1", "10.1038/s41524-025-01714-2",
    "10.1021/jacsau.5c00526", "10.1021/acsenergylett.5c02723", "10.1016/j.cej.2025.163801",
    "10.1002/adsu.202500413", "10.1016/j.cossms.2025.101214", "10.1038/s41586-025-09951-7",
    "10.1039/d5cp02726h", "10.1016/j.rser.2025.116633", "10.1021/acs.chemmater.5c02352",
    "10.1038/s41524-025-01905-x", "10.1038/s41524-024-01451-y", "10.1038/s41524-025-01989-z",
    "10.1016/j.jpowsour.2025.239008", "10.1021/acsami.5c11818", "10.1002/aenm.202201497",
    "10.1038/s41597-020-00602-2", "10.1073/pnas.2214357120", "10.1016/j.ensm.2024.103842",
    "10.1016/j.isci.2024.109673", "10.1016/j.commatsci.2024.113074", "10.1021/acs.chemrev.0c01111",
    "10.1038/s41524-020-0283-z", "10.1021/acs.jpclett.0c01061", "10.1103/physrevb.100.014105",
]

def norm(doi: str) -> str:
    return doi.lower().strip().removeprefix("https://doi.org/").rstrip(".,;)")


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    """Attach short, publisher-grounded method descriptions; no numeric guesses."""
    record["scope_note"] = "本条简述基于出版社元数据或公开摘要；本机全文可用性由 verification.fulltext 记录。具体参数、结果和页码须核对正文与补充材料，不能据元数据补猜。"
    detail = {
        "10.1038/s41524-026-02023-y": {
            "role": "预训练 MACE 采样、少量 DFT 适配与 NEP 蒸馏，研究固态电解质的离子输运。",
            "systems": ["LGPS", "LATP", "Li3YCl6", "固态电解质"],
            "methods": ["DFT", "AIMD", "MD", "MLIP", "MACE", "NEP", "微调", "模型蒸馏"],
            "properties": ["能量和力", "迁移势垒", "扩散系数", "轨迹稳定性"],
            "summary": "用预训练 MACE 进行构型采样并补充 DFT 标签，适配后向轻量 NEP 蒸馏；同时检验势垒、扩散与 MD 稳定性。少数据结果的适用范围是文中验证的体系，不能推广为任意材料的样本量保证。",
            "source": "https://www.nature.com/articles/s41524-026-02023-y",
        },
        "10.1039/d6eb00024j": {
            "role": "MD 采样溶剂化构型与结构感知 GNN 联合预测电解液前线轨道能。",
            "systems": ["锂电池液态电解液", "溶剂化结构", "离子对"],
            "methods": ["MD", "DFT", "GNN", "机器学习", "溶剂化采样"],
            "properties": ["HOMO", "LUMO", "HOMO-LUMO gap"],
            "summary": "结合 MD 溶剂化采样与结构感知机器学习，预测热构型的 HOMO/LUMO 和能隙。应按配方/化学空间验证；轨道能代理不等于实测电化学稳定窗口或直接计算完整 SEI 反应。",
            "source": "https://pubs.rsc.org/en/content/articlehtml/2026/eb/d6eb00024j",
        },
        "10.1021/acs.jctc.4c00190": {
            "role": "SevenNet 的 GNN 原子势并行 MD 算法；属于可复用方法，不是电池体系性能论证。",
            "systems": ["原子模拟方法基准"],
            "methods": ["GNN", "MLIP", "MD", "SevenNet", "并行计算"],
            "properties": ["MD 计算效率", "模型并行可扩展性"],
            "summary": "提出图神经网络原子势的可扩展并行计算方法。可用于学习 MLIP 与 MD 引擎的接口，但应用到电池仍须额外验证目标化学空间和物性。作者 arXiv 稿与正式 DOI 对应，二者的版本需区分。",
            "source": "https://arxiv.org/abs/2402.03789",
            "resources": [{"label": "作者代码 SevenNet", "url": "https://github.com/MDIL-SNU/SevenNet"},
                          {"label": "作者预印本（非期刊最终版）", "url": "https://arxiv.org/abs/2402.03789"}],
        },
    }.get(norm(record.get("doi", "")))
    if detail:
        record.update({k: v for k, v in detail.items() if k not in {"source", "resources"}})
        record["tags_zh"] = list(dict.fromkeys(record.get("tags_zh", []) + detail["methods"]))
        record["evidence"] = [{"claim": detail["summary"], "basis": detail["source"], "strength": "moderate"}]
        resources = record.setdefault("resources", [])
        for resource in detail.get("resources", []):
            if resource["url"] not in {x.get("url") for x in resources}:
                resources.append(resource)
    for field in ("publication_date", "online_date"):
        raw = str(record.get(field, ""))
        precision = record.get(field + "_precision")
        if raw and precision in {"year", "month", "day"}:
            parts = raw.split("-")[:{"year": 1, "month": 2, "day": 3}[precision]]
            record[field] = "-".join(str(int(x)).zfill(4 if i == 0 else 2) for i, x in enumerate(parts))
    return record

def date_of(msg: dict[str, Any], *keys: str) -> tuple[int, int, int] | None:
    for key in keys:
        parts = (msg.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            p = parts[0]
            return (int(p[0]), int(p[1]) if len(p) > 1 else 1, int(p[2]) if len(p) > 2 else 1)
    return None

def date_precision(msg: dict[str, Any], *keys: str) -> str:
    for key in keys:
        parts = (msg.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            return ("day" if len(parts[0]) >= 3 else "month" if len(parts[0]) == 2 else "year")
    return "unknown"

def tags(title: str, abstract: str) -> list[str]:
    text = f"{title} {abstract}".lower()
    out = []
    for needle, label in (("machine learning", "机器学习"), ("interatomic", "机器学习势"),
        ("molecular dynamics", "MD"), ("density functional", "DFT"), ("electrolyte", "电解液"),
        ("solid-state", "固态电解质"), ("battery", "电池材料"), ("interface", "界面"),
        ("cathode", "正极"), ("anode", "负极"), ("dataset", "数据集"), ("review", "综述")):
        if needle in text and label not in out: out.append(label)
    return out or ["电池材料计算"]

def verify(doi: str) -> dict[str, Any] | None:
    request = Request("https://api.crossref.org/works/" + quote(doi, safe="/"),
        headers={"User-Agent": "BatteryEvidenceLab/2026.10 metadata-verification"})
    with urlopen(request, timeout=35) as response:
        m = json.loads(response.read().decode("utf-8")).get("message", {})
    returned = norm(str(m.get("DOI", "")))
    if returned != norm(doi):
        return None
    online = date_of(m, "published-online", "published")
    printed = date_of(m, "published-print", "issued", "published")
    dates = [x for x in (online, printed) if x]
    if not dates or min(dates) > AS_OF:
        return None
    y = (printed or online)[0]
    title = html.unescape(re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0])).strip()
    if not title:
        return None
    authors = []
    for a in m.get("author", []):
        name = " ".join(x for x in (a.get("given", ""), a.get("family", "")) if x).strip()
        if name: authors.append(name)
    abstract = m.get("abstract", "")
    abstract = " ".join(str(abstract).replace("<jats:p>", "").replace("</jats:p>", "").split())
    ts = tags(title, abstract)
    lower_title = title.lower()
    is_perspective = "perspective" in lower_title or "viewpoint" in lower_title or "opinion" in lower_title
    is_review = "综述" in ts or "review" in lower_title
    slug = "recent_" + norm(doi).replace("/", "_").replace(".", "_")
    record = {"id": slug, "title": title, "authors": authors or ["待补充"], "year": y,
        "journal": (m.get("container-title") or [""])[0], "document_type": "Perspective" if is_perspective else ("Review" if is_review else "Paper"),
        "doi": norm(doi), "url": m.get("URL") or f"https://doi.org/{norm(doi)}",
        "role": "面向电池电解液、固态电解质、正极/界面模拟的可复用计算文献。",
        "systems": [], "methods": ts, "properties": [], "tags_zh": ts,
        "summary": f"基于 Crossref 出版社元数据核验：{title}。摘要/正文参数仍需按来源逐项复核。",
        "scope_note": "DOI、题名、作者、期刊与在线出版年份由 Crossref 记录核验；本条尚未宣称本地全文已核验。",
        "publication_status": "published", "collection": "recent_verified_20261008", "difficulty": "进阶",
        "protocol_steps": [], "evidence": [{"claim": "DOI 与出版社元数据已核验", "basis": m.get("URL") or f"https://doi.org/{norm(doi)}", "strength": "moderate"}],
        "relations": [], "resources": [{"label": "DOI / 出版社记录", "url": m.get("URL") or f"https://doi.org/{norm(doi)}"}], "wos_uid": "",
        "publication_date": "-".join(map(str, printed or online)), "publication_date_precision": date_precision(m, "published-print", "issued", "published"),
        "online_date": "-".join(map(str, online)) if online else "", "online_date_precision": date_precision(m, "published-online", "published"),
        "verification": {"doi": "verified_crossref_2026-10-08", "publisher": "verified_crossref_2026-10-08", "wos": "not_checked", "fulltext": "not_downloaded", "sources": [m.get("URL") or f"https://doi.org/{norm(doi)}"]}}
    specials = {
        "10.1021/acs.chemmater.6c01051": ("固态电池 MLIP 方法与验证；用于训练数据、势函数选择和界面模拟路线比较。", ["固态电池", "正极/固态电解质界面"], ["能量、力、扩散、界面稳定性"], "Perspective"),
        "10.1103/physrevmaterials.8.115407": ("Li6PS5Cl 固态电解质体相与晶界扩散的 MLIP/AIMD 原子模拟。", ["Li6PS5Cl 固态电解质", "晶界"], ["Li+扩散、扩散系数、晶界迁移"], "Paper"),
        "10.1016/j.est.2026.121104": ("钠离子正极/固态电解质界面黏附的 MLIP 原子尺度分析。", ["钠离子电池正极", "固态电解质界面"], ["界面黏附、界面能"], "Paper"),
        "10.1038/s41467-025-62824-5": ("恒电势机器学习框架下锂金属-电解液界面枝晶形成观察。", ["锂金属负极", "液态电解液界面"], ["枝晶、界面反应"], "Paper"),
        "10.1038/s41524-025-01735-x": ("机器学习引导相场模拟金属离子电池电化学设计空间。", ["金属离子电池", "金属负极"], ["沉积形貌、枝晶、界面演化"], "Paper"),
        "10.1016/j.jechem.2025.03.007": ("InterOptimus 用 AI 工作流筛选锂电池异质界面基态结构。", ["锂电池异质界面"], ["界面结构、界面能"], "Paper"),
        "10.1016/j.mtener.2025.101841": ("机器学习分析高镍层状正极结构演化。", ["高镍层状正极"], ["结构演化、容量/电压衰减"], "Paper"),
        "10.1016/j.jpowsour.2025.239008": ("机器学习势分子动力学研究 NCM811 晶体缺陷效应。", ["NCM811 正极"], ["缺陷、扩散、结构稳定性"], "Paper"),
        "10.1021/acsami.5c11818": ("机器学习势解析充电镍氧化物正极表面降解路径。", ["充电镍氧化物正极表面"], ["表面降解、氧迁移"], "Paper"),
        "10.1016/j.cej.2025.163801": ("DFT/AIMD 与机器学习联合预测锂金属电池电解液行为和 SEI 形成。", ["锂金属负极、电解液、SEI"], ["还原电位、吸附能、分解路径"], "Paper"),
        "10.1039/d5cp02726h": ("数据驱动筛选锂离子电池 SEI 候选材料。", ["锂离子电池 SEI"], ["SEI 稳定性、候选排序"], "Paper"),
        "10.1073/pnas.2214357120": ("基于数据驱动与分子描述符设计锂金属负极电解液。", ["锂金属负极、电解液"], ["循环稳定性、电解液性能"], "Paper"),
        "10.1039/d4ta06675h": ("第一性原理预测钙电池电解液溶剂化结构。", ["钙电池电解液"], ["溶剂化结构、离子配位"], "Paper"),
        "10.1038/s41467-025-56322-x": ("无序结构增强 Li3PS4 固态电解质中的锂离子输运。", ["Li3PS4 固态电解质"], ["离子输运、扩散"], "Paper"),
        "10.1021/jacsau.5c00526": ("通用机器学习框架用于离子电池正极材料设计。", ["离子电池正极"], ["结构/性质预测、候选筛选"], "Paper"),
    }
    if norm(doi) in specials:
        role, systems, properties, dtype = specials[norm(doi)]
        record.update(role=role, systems=systems, properties=properties, document_type=dtype)
    return enrich_record(record)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enrich-existing", action="store_true", help="Normalize/enrich the already verified catalog offline, without Crossref requests")
    args = parser.parse_args()
    if args.enrich_existing:
        rows = json.loads(OUT.read_text(encoding="utf-8"))
        rows = [enrich_record(row) for row in rows]
        OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"enriched {len(rows)} existing verified records; no network verification repeated")
        return
    rows, failures = [], []
    for doi in dict.fromkeys(map(norm, CANDIDATES)):
        try:
            row = verify(doi)
            if row: rows.append(row)
            else: failures.append(doi)
        except Exception:
            failures.append(doi)
        time.sleep(0.35)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"verified new records: {len(rows)}; rejected/unavailable: {len(failures)}")
    print("\n".join(f"- {r['doi']} | {r['title']}" for r in rows))
    if failures: print("rejected:", ", ".join(failures))

if __name__ == "__main__":
    main()
