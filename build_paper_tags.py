"""Build the public, auditable paper-tag map."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from paper_tagging import classify_paper


ROOT = Path(__file__).resolve().parent


def main() -> None:
    papers = json.loads((ROOT / "data/papers.json").read_text(encoding="utf-8"))
    rows = {paper["id"]: classify_paper(paper) for paper in papers}
    counts = Counter(tag for row in rows.values() for tag in row["display_tags"])
    payload = {
        "schema_version": 1,
        "definitions": {
            "MS": "BIOVIA Materials Studio；仅方法或精选标签明确使用时标注",
            "DFT": "包含密度泛函理论或第一性原理计算",
            "MD": "包含经典MD、AIMD、MLMD或LAMMPS分子动力学",
            "VASP": "精选元数据明确使用或教授VASP/VASPKIT",
            "方法论文": "本库starter方法路线集",
            "进展论文": "本库核心电池材料计算研究集",
        },
        "counts": dict(sorted(counts.items())),
        "papers": rows,
    }
    target = ROOT / "data/paper_tags.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Paper tags: {len(rows)} papers; {dict(counts)}")
    print(target)


if __name__ == "__main__":
    main()
