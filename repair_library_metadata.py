"""Repair the DOI/title metadata of the 2026-09-20 expansion batch.

The expansion batch was initially assembled from several discovery results.  A
Crossref/publisher audit found a small set of DOI/title mismatches.  This script
keeps the correction list versioned and applies it consistently to the source
catalogue, the merged library, and the lightweight manifest.  It deliberately
does not touch PDFs or full-text chunks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EXPANSION = ROOT / "data" / "paper_expansion_20260920.json"
PAPERS = ROOT / "data" / "papers.json"
MANIFEST = ROOT / "literature" / "manifest.json"


REPAIRS: dict[str, dict[str, Any]] = {
    "kresse1996_vasp_efficiency": {
        "doi": "10.1016/0927-0256(96)00008-0",
        "journal": "Computational Materials Science",
        "authors": ["G. Kresse", "J. Furthmüller"],
    },
    "dudarev1998_lsda_u": {
        "doi": "10.1103/PhysRevB.57.1505",
        "journal": "Physical Review B",
        "title": "Electron-energy-loss spectra and the structural stability of nickel oxide: An LSDA+U study",
        "authors": ["S. L. Dudarev", "G. A. Botton", "S. Y. Savrasov", "C. J. Humphreys", "A. P. Sutton"],
    },
    "grimme2010_dftd": {
        "doi": "10.1063/1.3382344",
        "journal": "The Journal of Chemical Physics",
        "authors": ["S. Grimme", "J. Antony", "S. Ehrlich", "H. Krieg"],
    },
    "henkelman2000_neb_tangent": {
        "doi": "10.1063/1.1323224",
        "journal": "The Journal of Chemical Physics",
        "title": "Improved tangent estimate in the nudged elastic band method for finding minimum energy paths and saddle points",
        "authors": ["G. Henkelman", "H. Jónsson"],
    },
    "henkelman2006_bader": {
        "doi": "10.1016/j.commatsci.2005.04.010",
        "journal": "Computational Materials Science",
        "authors": ["G. Henkelman", "A. Arnaldsson", "H. Jónsson"],
    },
    "thompson2015_snap": {
        "doi": "10.1016/j.jcp.2014.12.018",
        "journal": "Journal of Computational Physics",
        "authors": ["A. P. Thompson", "L. P. Swiler", "C. R. Trott", "S. M. Foiles", "G. J. Tucker"],
    },
    "podryabinkin2017_active_learning": {
        "doi": "10.1016/j.commatsci.2017.08.031",
        "journal": "Computational Materials Science",
        "authors": ["Evgeny V. Podryabinkin", "Alexander V. Shapeev"],
    },
    "vandermause2020_active_learning": {
        "doi": "10.1038/s41524-020-0283-z",
        "title": "On-the-fly active learning of interpretable Bayesian force fields for atomistic rare events",
        "journal": "npj Computational Materials",
        "authors": [
            "Jonathan Vandermause", "Steven B. Torrisi", "Simon Batzner", "Yu Xie",
            "Lixin Sun", "Alexie M. Kolpak", "Boris Kozinsky",
        ],
    },
    "sendek2017_sse_relationships": {
        "doi": "10.1039/C6EE02697D",
        "title": "Holistic computational structure screening of more than 12,000 candidates for solid lithium-ion conductor materials",
        "journal": "Energy & Environmental Science",
        "authors": ["Austin D. Sendek", "Qian Yang", "Ekin D. Cubuk", "Karel-Alexander N. Duerloo", "Yi Cui", "Evan J. Reed"],
    },
    "muy2015_high_throughput_sse": {
        "doi": "10.1016/j.isci.2019.05.036",
        "title": "High-Throughput Screening of Solid-State Li-Ion Conductors Using Lattice-Dynamics Descriptors",
        "year": 2019,
        "journal": "iScience",
        "authors": ["Sokseiha Muy", "Johannes Voss", "Roman Schlem", "Raimund Koerver", "Stefan J. Sedlmaier", "Filippo Maglia", "Peter Lamp", "Wolfgang G. Zeier", "Yang Shao-Horn"],
    },
    "peled2017_sei_review": {
        "doi": "10.1149/2.1441707jes",
        "journal": "Journal of The Electrochemical Society",
        "authors": ["E. Peled", "S. Menkin"],
    },
    "fireworks2015_workflow": {
        "doi": "10.1002/cpe.3505",
        "journal": "Concurrency and Computation: Practice and Experience",
        "authors": [
            "Anubhav Jain", "Shyue Ping Ong", "Wei Chen", "Bharat Medasani", "Xiaohui Qu",
            "Michael Kocher", "Miriam Brafman", "Guido Petretto", "Gian-Marco Rignanese",
            "Geoffroy Hautier", "Dan Gunter", "Kristin A. Persson",
        ],
    },
    "ward2016_matminer": {
        "doi": "10.1016/j.commatsci.2018.05.018",
        "year": 2018,
        "journal": "Computational Materials Science",
        "authors": [
            "Logan Ward", "Alexander Dunn", "Alireza Faghaninia", "Nils E. R. Zimmermann",
            "Saurabh Bajaj", "Qi Wang", "Joseph Montoya", "Jiming Chen", "Kyle Bystrom",
            "Maxwell Dylla", "Kyle Chard", "Mark Asta", "Kristin A. Persson",
            "G. Jeffrey Snyder", "Ian Foster", "Anubhav Jain",
        ],
    },
    "unke2021_mlff_review": {
        "authors": ["Oliver T. Unke", "Stefan Chmiela", "Huziel E. Sauceda", "Michael Gastegger", "Igor Poltavsky", "Kristof T. Schütt", "Alexandre Tkatchenko", "Klaus-Robert Müller"],
    },
    "swift2019_space_charge": {
        "authors": ["Michael W. Swift", "Yue Qi"],
    },
    "qi2024_lgps_ml_aimd": {
        "authors": ["Changlin Qi", "Yuwei Zhou", "Xiaoze Yuan", "Qing Peng", "Yong Yang", "Yongwang Li", "Xiaodong Wen"],
    },
    "nachimuthu2022_se_doped_lgps": {
        "authors": ["S. Nachimuthu", "H.-J. Cheng", "H.-J. Lai", "Y.-H. Cheng", "Rui-Tong Kuo", "W. G. Zeier", "B. J. Hwang", "J.-C. Jiang"],
    },
    "stottmeister2023_sei_alkali": {
        "authors": ["Daniel Stottmeister", "Axel Groß"],
    },
    "qi2021_electrolyte_dataset": {
        "authors": ["Evan Walter Clark Spotte-Smith", "Samuel M. Blau", "Xiaowei Xie", "Hetal D. Patel", "Mingjian Wen", "Brandon Wood", "Shyam Dwaraknath", "Kristin Aslaug Persson"],
    },
}

# This discovery record duplicates the earlier WOS-verified Sendek record,
# which already has the same corrected DOI and a local PDF.  Keep the richer
# original instead of publishing two DOI-identical records.
DEDUPLICATE_IDS = {"sendek2017_sse_relationships"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_doi(value: str) -> str:
    return value.strip().lower()


def _apply_metadata(row: dict[str, Any], repair: dict[str, Any]) -> None:
    row.update({key: value for key, value in repair.items() if key in {"title", "authors", "year", "journal"}})
    if "doi" in repair:
        row["doi"] = repair["doi"]
        row["url"] = f"https://doi.org/{repair['doi']}"
    if "tags_zh" in row:
        if "url" in row:
            row.setdefault("verification", {})["sources"] = [row["url"]]
        for evidence in row.get("evidence", []):
            if isinstance(evidence, dict) and "basis" in evidence and "url" in row:
                evidence["basis"] = f"出版社/DOI：{row['url']}"
        for resource in row.get("resources", []):
            if isinstance(resource, dict) and resource.get("label") == "DOI / 出版社记录" and "url" in row:
                resource["url"] = row["url"]


def apply(write: bool) -> int:
    expansion = _load(EXPANSION)
    papers = _load(PAPERS)
    manifest = _load(MANIFEST)
    by_id = {row.get("id"): row for row in expansion if isinstance(row, dict)}
    paper_by_id = {row.get("id"): row for row in papers if isinstance(row, dict)}
    changed = 0
    for paper_id, repair in REPAIRS.items():
        if paper_id in by_id:
            _apply_metadata(by_id[paper_id], repair)
        # A prior run may already have removed a DOI-identical duplicate from
        # the merged library; the source expansion record remains the audit
        # trail, so this is intentionally idempotent rather than fatal.
        if paper_id not in paper_by_id:
            continue
        _apply_metadata(paper_by_id[paper_id], repair)
        entry = manifest.get("papers", {}).get(paper_id)
        if isinstance(entry, dict):
            entry["title"] = repair.get("title", entry.get("title"))
            if "doi" in repair:
                entry["doi"] = _canonical_doi(repair["doi"])
        changed += 1
    papers = [row for row in papers if row.get("id") not in DEDUPLICATE_IDS]
    for paper_id in DEDUPLICATE_IDS:
        manifest.get("papers", {}).pop(paper_id, None)
    if not write:
        print(f"metadata repair plan: {changed} records; deduplicate {len(DEDUPLICATE_IDS)} DOI-identical record")
        return 0
    for path, value in ((EXPANSION, expansion), (PAPERS, papers), (MANIFEST, manifest)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"metadata repaired: {changed} records")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair audited DOI/title metadata consistently.")
    parser.add_argument("--apply", action="store_true", help="write the corrected JSON files")
    args = parser.parse_args()
    return 0 if apply(args.apply) == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
