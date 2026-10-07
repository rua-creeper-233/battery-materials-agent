"""Generate public release statistics from current files, without private keys."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def dataset_status(path: Path) -> dict:
    if not path.exists():
        return {"rows": 0, "exists": False}
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return {"rows": len(rows), "exists": True, "sha256": hashlib.sha256(raw).hexdigest(),
            "categories": dict(sorted(Counter(row.get("category", "unknown") for row in rows).items()))}


def build_status(date: str) -> dict:
    papers = read_json(ROOT / "data/papers.json", [])
    ids = {paper["id"] for paper in papers}
    dois = {str(paper.get("doi", "")).lower().strip() for paper in papers}
    if len(ids) != len(papers) or len(dois) != len(papers) or "" in dois:
        raise ValueError("The curated catalog must have unique nonempty IDs and DOIs")
    manifest = read_json(ROOT / "literature/manifest.json", {})
    fulltexts = []
    for pid, record in manifest.get("papers", {}).items():
        if pid not in ids or record.get("status") != "downloaded":
            continue
        relative = record.get("local_pdf", "")
        candidate = (ROOT / relative).resolve() if relative else None
        if candidate and candidate.is_relative_to(ROOT) and candidate.is_file() and record.get("validation", {}).get("valid_pdf"):
            fulltexts.append(pid)
    chunks_path = ROOT / "data/fulltext_chunks.jsonl"
    chunk_count = 0
    indexed_ids = set()
    if chunks_path.exists():
        with chunks_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = json.loads(line)
                    if item.get("paper_id") in ids:
                        chunk_count += 1
                        indexed_ids.add(item["paper_id"])
    tags = read_json(ROOT / "data/paper_tags.json", {})
    datasets = {label: dataset_status(ROOT / "finetune/data" / filename) for label, filename in
                (("train", "train.jsonl"), ("validation", "validation.jsonl"), ("test", "test.jsonl"))}
    return {"schema_version": 1, "as_of": date, "papers": len(papers),
            "recent_2023_onward": sum(int(p.get("year", 0)) >= 2023 for p in papers),
            "publication_years": dict(sorted(Counter(str(p.get("year")) for p in papers).items())),
            "publication_types": dict(sorted(Counter(p.get("document_type", "Paper") for p in papers).items())),
            "wos_records": sum(bool(p.get("wos_uid")) for p in papers),
            "local_fulltext_papers": len(fulltexts), "local_fulltext_missing": len(papers) - len(fulltexts),
            "indexed_papers": len(indexed_ids), "indexed_chunks": chunk_count,
            "tags": tags.get("counts", {}), "datasets": datasets,
            "dataset_rows": sum(item["rows"] for item in datasets.values()),
            "model_status": "New datasets prepared; no model retraining performed for this release.",
            "scope": "Counts refer to curated catalog and local evidence library; public site contains metadata, not PDFs or private Zotero keys."}


def render_status(status: dict) -> str:
    train, val, test = (status["datasets"][key]["rows"] for key in ("train", "validation", "test"))
    return (f"# 当前项目状态\n\n统计日期：{status['as_of']}。由 `update_project_status.py` 根据实际库、索引与数据集生成。\n\n"
            f"| 项目 | 实际数量 |\n|---|---:|\n| 公开精选论文（唯一 DOI） | {status['papers']} |\n"
            f"| 2023 年及以后论文 | {status['recent_2023_onward']} |\n| 已有 WOS UT | {status['wos_records']} |\n"
            f"| 本机已校验正文 | {status['local_fulltext_papers']} |\n| 本机尚缺正文 | {status['local_fulltext_missing']} |\n"
            f"| 全文索引论文 | {status['indexed_papers']} |\n| 带页码文本块 | {status['indexed_chunks']} |\n"
            f"| QLoRA 训练样本 | {train} |\n| QLoRA 验证样本 | {val} |\n| QLoRA 测试样本 | {test} |\n\n"
            "当前新增的是可追溯问答数据，本版本没有自动重新训练模型。训练/验证/测试按论文来源分组隔离；验证集用于开发选择，测试集留到方案固定后评估。样本来自元数据与人工简述，不能据其数量判断真实科研问答准确率。\n\n"
            "本机全文覆盖率不等于公开网页全文可访问率，也不代表 Zotero 云同步完成。公开站点保留书目、DOI、方法索引与教学资料；正文和私有条目键仅在本机使用。\n\n"
            "- [AI 实施指南](AI_BATTERY_APPLICATIONS.md)\n- [未来研究方向](BATTERY_COMPUTATION_FUTURE_DIRECTIONS.md)\n"
            "- JSON 统计：`data/project_status.json`；训练来源与文件 SHA-256：`finetune/data/manifest.json`。\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Release date YYYY-MM-DD in the user's timezone")
    args = parser.parse_args()
    status = build_status(args.date)
    (ROOT / "data/project_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "guides/PROJECT_STATUS.md").write_text(render_status(status), encoding="utf-8")
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    start, end = "<!-- CURRENT_STATUS_START -->", "<!-- CURRENT_STATUS_END -->"
    if start in content and end in content:
        prefix, remaining = content.split(start, 1)
        _, suffix = remaining.split(end, 1)
        rows = status["datasets"]
        summary = (f"\n统计日期 **{status['as_of']}**：**{status['papers']} 篇唯一 DOI**；本机已有校验正文 **{status['local_fulltext_papers']} 篇**、页码文本块 **{status['indexed_chunks']} 个**；WOS UT **{status['wos_records']} 条**。\n\n"
                   f"QLoRA 数据：**{rows['train']['rows']} 训练 / {rows['validation']['rows']} 验证 / {rows['test']['rows']} 测试**。新增数据尚未重新训练；数量与哈希详见 [当前状态](guides/PROJECT_STATUS.md)。\n")
        path.write_text(prefix + start + summary + end + suffix, encoding="utf-8")
    print(json.dumps({key: status[key] for key in ("papers", "local_fulltext_papers", "indexed_chunks", "dataset_rows")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
