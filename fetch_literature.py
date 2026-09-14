"""Build a lawful, auditable local full-text library for the seed papers.

The script performs read-only network requests.  It never logs in, uploads, saves
cookies, or changes Web of Science/Zotero.  A file is retained only when the
response is a valid PDF; HTML paywall/login pages are recorded as unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
PAPERS_PATH = ROOT / "data" / "papers.json"
LIBRARY_ROOT = ROOT / "literature"
PDF_DIR = LIBRARY_ROOT / "pdfs"
SUPPLEMENTARY_DIR = LIBRARY_ROOT / "supplementary"
TEXT_DIR = LIBRARY_ROOT / "text"
MANIFEST_PATH = LIBRARY_ROOT / "manifest.json"
GLOBAL_INDEX = ROOT / "data" / "fulltext_chunks.jsonl"
MAX_PDF_BYTES = 100 * 1024 * 1024
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# Public copies explicitly exposed by an author, laboratory, university,
# preprint server, or a public host carrying an openly licensed article. These
# are deliberately small and human-vetted: do not add a redistribution copy
# unless the article's open licence is clear and the PDF is independently
# checked against the target title.
PUBLIC_PDF_OVERRIDES: dict[str, list[str]] = {
    "wu2025_spe_aimd_ms": [
        "https://uu.diva-portal.org/smash/get/diva2%3A1959874/FULLTEXT01.pdf",
    ],
    "zhang2025_sei_phasefield_ms": [
        "https://pubs.rsc.org/en/content/articlepdf/2025/ee/d5ee01030f",
    ],
    "chen2025_heteroalkali_ms": [
        "https://www.nature.com/articles/s41467-025-66197-7_reference.pdf",
    ],
    "wang2018_sei_modeling_review": [
        "https://www.nature.com/articles/s41524-018-0064-0.pdf",
    ],
    "batatia2025_mace_mp": ["https://arxiv.org/pdf/2401.00096"],
    "radova2025_frozen_transfer": ["https://www.nature.com/articles/s41524-025-01727-x.pdf"],
    "bilbrey2025_uq": ["https://www.nature.com/articles/s41524-025-01572-y.pdf"],
    "aydinol1997_voltage": [
        "https://ceder.berkeley.edu/publications/prb-56-1354-1997.pdf",
    ],
    "ceder1998_cathode_design": [
        "https://web.mit.edu/dsadoway/www/79.pdf",
    ],
    "vanderven2001_diffusion": [
        "https://ceder.berkeley.edu/publications/prb-64-184307-2001.pdf",
    ],
    "ong2011_li_na": [
        "https://ceder.berkeley.edu/publications/Sodium_Energy_Environment.pdf",
    ],
    "ong2013_lgps": [
        "https://ceder.berkeley.edu/publications/Shyue_2012_Li10MP2X12.pdf",
    ],
    "sendek2017_sse_screening": [
        "https://web.stanford.edu/group/cui_group/papers/Austin_Cui_Reed_EES_2016.pdf",
        "https://drive.usercontent.google.com/download?id=1QysXRQ9tcEOYUyxhfFQNrErNgPgl0Zy8&export=download&confirm=t",
    ],
    "chen2022_m3gnet": [
        "https://arxiv.org/pdf/2202.02450",
    ],
    "henkelman2000_cineb": [
        "https://theory.cm.utexas.edu/henkelman/pubs/henkelman00_9978.pdf",
    ],
    "leung2010_sei_aimd": [
        "https://arxiv.org/pdf/1009.4154",
    ],
    "mo2012_lgps_aimd": [
        "https://ceder.berkeley.edu/publications/YiFei_Lithium_Conductor.pdf",
    ],
    "deng2023_chgnet": [
        "https://arxiv.org/pdf/2302.14231",
    ],
    "wang2021_vaspkit": [
        "https://arxiv.org/pdf/1908.08269",
    ],
    "ong2013_pymatgen": [
        "https://perssongroup.lbl.gov/papers/compmatsci2013-pymatgen.pdf",
        "https://ceder.berkeley.edu/publications/2012_Python_materials_genomics.pdf",
    ],
    "larsen2017_ase": [
        "https://backend.orbit.dtu.dk/ws/portalfiles/portal/130802447/main.pdf",
    ],
    "ganose2025_atomate2": [
        "https://escholarship.org/content/qt9d78f7qc/qt9d78f7qc_noSplash_a24b5abd10df0845fb7110c53fbe8a8f.pdf",
    ],
    "jain2013_materials_project": [
        "https://web.mit.edu/ceder/publications/2013_Jain_Materials_Project.pdf",
        "https://iric.imet-db.ru/PDF/161.pdf",
    ],
    "smidstrup2014_idpp": [
        "https://arxiv.org/pdf/1406.1512",
    ],
    "he2018_aimd_statistics": [
        "https://api.drum.lib.umd.edu/server/api/core/bitstreams/ef25575f-9594-4e80-8543-caaae487c530/content",
    ],
    "zhou2004_dftu_voltage": [
        "https://web.mit.edu/ceder/publications/PhysRevB_70_235121.pdf",
        "https://arxiv.org/pdf/cond-mat/0406382",
    ],
    "jacobs2025_mlip_guide": [
        "https://arxiv.org/pdf/2503.09814",
    ],
    "togo2015_phonopy": [
        "https://arxiv.org/pdf/1506.08498",
    ],
    "ganose2018_sumo": [
        "https://joss.theoj.org/papers/10.21105/joss.00717.pdf",
    ],
    "wang2018_deepmdkit": [
        "https://arxiv.org/pdf/1712.03641",
    ],
    "zhang2020_dpgen": [
        "https://arxiv.org/pdf/1910.12690",
    ],
    "batzner2022_nequip": [
        "https://www.nature.com/articles/s41467-022-29939-5.pdf",
        "https://arxiv.org/pdf/2101.03164",
    ],
    "musaelian2023_allegro": [
        "https://www.nature.com/articles/s41467-023-36329-y.pdf",
        "https://arxiv.org/pdf/2204.05249",
    ],
    "deringer2021_gpr_gap": [
        "https://wrap.warwick.ac.uk/155761/1/WRAP-Gaussian-process-regression-materials-molecules-Bart%C3%B3k-2021.pdf",
    ],
    "thompson2022_lammps": [
        "https://www.osti.gov/servlets/purl/1821775",
        "https://chris256.com/papers/molecular_dynamics/2021-thompson-LAMMPS_particle_based_materials_modeling.pdf",
    ],
    "pizzi2016_aiida": [
        "https://arxiv.org/pdf/1504.01163",
    ],
    "himanen2020_dscribe": [
        "https://arxiv.org/pdf/1904.08875",
    ],
    "xie2018_cgcnn": [
        "https://arxiv.org/pdf/1710.10324",
    ],
    "dunn2020_matbench": [
        "https://www.nature.com/articles/s41524-020-00406-3.pdf",
    ],
    "persson2010_graphite": [
        "https://perssongroup.lbl.gov/papers/physrevb2010-ligraphite.pdf",
    ],
    "shen2024_pymatgen_defects": [
        "https://joss.theoj.org/papers/10.21105/joss.05941.pdf",
    ],
}

OPEN_LICENSED_REDISTRIBUTION_COPIES = {
    "https://iric.imet-db.ru/PDF/161.pdf",
    "https://chris256.com/papers/molecular_dynamics/2021-thompson-LAMMPS_particle_based_materials_modeling.pdf",
}


def looks_like_supplement_url(url: str) -> bool:
    lowered = urllib.parse.unquote(url).lower()
    markers = ("/suppdata/", "/supp/", "/supplement", "/esm/", "moesm", "_si_", "suppl_file")
    return any(marker in lowered for marker in markers)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def request(url: str, accept: str = "*/*", timeout: int = 45):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
    )
    return urllib.request.urlopen(req, timeout=timeout)


def openalex_record(doi: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(doi, safe="")
    url = f"https://api.openalex.org/works/https%3A%2F%2Fdoi.org%2F{encoded}"
    with request(url, "application/json") as response:
        return json.load(response)


META_PDF_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:citation_pdf_url|og:pdf)["\'][^>]+content=["\']([^"\']+)',
    re.I,
)
META_PDF_RE_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\'](?:citation_pdf_url|og:pdf)["\']',
    re.I,
)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def discover_pdf_links(landing_url: str) -> list[str]:
    """Read a landing page and return declared/public PDF links."""
    try:
        with request(landing_url, "text/html,application/xhtml+xml") as response:
            final_url = response.geturl()
            raw = response.read(4 * 1024 * 1024)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return []
    markup = raw.decode("utf-8", "ignore")
    candidates = META_PDF_RE.findall(markup) + META_PDF_RE_REVERSED.findall(markup)
    for href in HREF_RE.findall(markup):
        lowered = href.lower()
        if ".pdf" in lowered or "/download" in lowered or "articlepdf" in lowered:
            candidates.append(href)
    result: list[str] = []
    for candidate in candidates:
        absolute = urllib.parse.urljoin(final_url, html.unescape(candidate))
        if (
            absolute.startswith(("http://", "https://"))
            and not looks_like_supplement_url(absolute)
            and absolute not in result
        ):
            result.append(absolute)
    return result


def publisher_candidates(paper: dict[str, Any]) -> list[str]:
    """Return conservative official PDF candidates; no proxy/paywall bypasses."""
    doi = paper["doi"]
    lowered = doi.lower()
    year = paper.get("year")
    result: list[str] = []
    url = paper.get("url")
    if isinstance(url, str) and url.startswith("http"):
        result.extend(discover_pdf_links(url))
    if lowered.startswith("10.1103/physrevb."):
        result.append(f"https://journals.aps.org/prb/pdf/{doi}")
    elif lowered.startswith("10.1021/"):
        result.append(f"https://pubs.acs.org/doi/pdf/{doi}")
    elif lowered.startswith("10.1039/"):
        code = "cp" if lowered.endswith("b925853a") else "ee"
        result.append(
            f"https://pubs.rsc.org/en/content/articlepdf/{year}/{code}/{doi.split('/')[-1].lower()}"
        )
    elif lowered.startswith("10.1038/s"):
        result.append(f"https://www.nature.com/articles/{doi.split('/')[-1]}.pdf")
    elif lowered == "10.1038/npjcompumats.2016.2":
        result.append("https://www.nature.com/articles/npjcompumats20162.pdf")
    elif lowered == "10.1038/33647":
        result.append("https://www.nature.com/articles/33647.pdf")
    # DOI landing pages sometimes declare citation_pdf_url even when the seed URL does not.
    result.extend(discover_pdf_links(f"https://doi.org/{doi}"))
    return unique(result)


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def candidate_sources(paper: dict[str, Any], allow_publisher: bool) -> tuple[dict[str, Any], list[dict[str, str]]]:
    # OpenAlex is useful for discovery but is not a single point of failure. Its
    # public API can rate-limit a batch, while a vetted repository copy or the
    # official publisher PDF remains independently available.
    oa: dict[str, Any] = {}
    openalex_error: str | None = None
    try:
        oa = openalex_record(paper["doi"])
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        openalex_error = f"{type(exc).__name__}: {exc}"[:400]
    access = oa.get("open_access") or {}
    best = oa.get("best_oa_location") or {}
    locations = oa.get("locations") or []
    candidates: list[dict[str, str]] = []
    for public_url in PUBLIC_PDF_OVERRIDES.get(paper["id"], []):
        basis = (
            "vetted_open_licensed_redistribution_copy"
            if public_url in OPEN_LICENSED_REDISTRIBUTION_COPIES
            else "vetted_public_author_or_repository_copy"
        )
        candidates.append({"url": public_url, "basis": basis})
    if access.get("is_oa"):
        for location in [best, *locations]:
            pdf_url = location.get("pdf_url") if isinstance(location, dict) else None
            if pdf_url and not looks_like_supplement_url(pdf_url):
                candidates.append({"url": pdf_url, "basis": "openalex_open_access_pdf"})
            landing = location.get("landing_page_url") if isinstance(location, dict) else None
            if landing:
                for found in discover_pdf_links(landing):
                    candidates.append({"url": found, "basis": "open_access_landing_page"})
    # Scientific Reports sometimes omits pdf_url in OpenAlex despite gold OA.
    if access.get("is_oa") and paper["doi"].lower().startswith("10.1038/"):
        for found in publisher_candidates(paper):
            candidates.append({"url": found, "basis": "open_access_official_publisher"})
    if allow_publisher:
        for found in publisher_candidates(paper):
            candidates.append({"url": found, "basis": "official_publisher_current_network"})
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in candidates:
        if row["url"] not in seen:
            deduped.append(row)
            seen.add(row["url"])
    summary = {
        "openalex_id": oa.get("id"),
        "is_oa": bool(access.get("is_oa")),
        "oa_status": access.get("oa_status"),
        "oa_url": access.get("oa_url"),
        "best_landing_page": best.get("landing_page_url"),
    }
    if openalex_error:
        summary["discovery_error"] = openalex_error
    return summary, deduped


def download_pdf(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_suffix(".pdf.part")
    if part.exists():
        part.unlink()
    digest = hashlib.sha256()
    size = 0
    try:
        with request(url, "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1") as response:
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            with part.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_PDF_BYTES:
                        raise ValueError("response exceeds 100 MiB safety limit")
                    digest.update(chunk)
                    handle.write(chunk)
        with part.open("rb") as handle:
            magic = handle.read(5)
        if magic != b"%PDF-":
            part.unlink(missing_ok=True)
            return {
                "ok": False,
                "reason": "response_is_not_pdf",
                "content_type": content_type,
                "final_url": final_url,
                "bytes": size,
            }
        part.replace(destination)
        return {
            "ok": True,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": size,
            "sha256": digest.hexdigest(),
        }
    except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        part.unlink(missing_ok=True)
        code = getattr(exc, "code", None)
        return {"ok": False, "reason": type(exc).__name__, "http_status": code, "detail": str(exc)[:300]}


def validate_pdf(path: Path, title: str) -> dict[str, Any]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        preview = " ".join((reader.pages[i].extract_text() or "") for i in range(min(3, pages)))
        title_tokens = [x for x in re.findall(r"[a-z0-9]+", title.lower()) if len(x) >= 4]
        preview_lower = preview.lower()
        matched = sum(token in preview_lower for token in set(title_tokens))
        denominator = max(len(set(title_tokens)), 1)
        first_text = re.sub(r"\s+", " ", preview_lower)[:12000]
        supplementary_signals = sum(
            marker in first_text
            for marker in (
                "supplementary information",
                "supporting information",
                "supplementary figure",
                "supplementary table",
                "in the format provided by the authors and unedited",
            )
        )
        document_kind = (
            "supplementary"
            if supplementary_signals >= 2
            or "in the format provided by the authors and unedited" in first_text
            else "article"
        )
        return {
            "valid_pdf": True,
            "pages": pages,
            "encrypted": bool(reader.is_encrypted),
            "first_pages_text_chars": len(preview),
            "title_token_match": round(matched / denominator, 3),
            "document_kind": document_kind,
            "supplementary_signals": supplementary_signals,
        }
    except Exception as exc:  # damaged/encrypted PDFs should remain visible in the audit
        return {"valid_pdf": False, "validation_error": f"{type(exc).__name__}: {exc}"[:400]}


def chunk_text(text: str, target: int = 1800, overlap: int = 250) -> list[str]:
    cleaned = re.sub(r"[ \t]+", " ", text).replace("\x00", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + target, len(cleaned))
        if end < len(cleaned):
            split = max(cleaned.rfind("\n", start + target // 2, end), cleaned.rfind(". ", start + target // 2, end))
            if split > start:
                end = split + 1
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


def extract_pdf(paper: dict[str, Any], pdf_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    rows: list[dict[str, Any]] = []
    text_chars = 0
    empty_pages: list[int] = []
    in_references = False
    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if re.search(r"(?:^|\n)\s*(?:references|bibliography)\s*(?:\n|$)", text, re.I):
            in_references = True
        text_chars += len(text)
        chunks = chunk_text(text)
        if not chunks:
            empty_pages.append(page_number)
        for chunk_number, chunk in enumerate(chunks, 1):
            rows.append(
                {
                    "paper_id": paper["id"],
                    "doi": paper["doi"],
                    "wos_uid": paper.get("wos_uid"),
                    "title": paper["title"],
                    "page": page_number,
                    "chunk": chunk_number,
                    "section": "references" if in_references else "body",
                    "text": chunk,
                }
            )
    return rows, {
        "pages": len(reader.pages),
        "text_chars": text_chars,
        "chunks": len(rows),
        "empty_text_pages": empty_pages,
        "extractor": "pypdf",
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            # ASCII escaping also protects JSONL record boundaries from PDF text
            # containing Unicode NEL/line-separator characters.
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    temporary.replace(path)


def rebuild_fulltext_index(papers: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    all_rows: list[dict[str, Any]] = []
    by_id = {paper["id"]: paper for paper in papers}
    for paper_id, entry in manifest.get("papers", {}).items():
        pdf_relative = entry.get("local_pdf")
        if not pdf_relative or paper_id not in by_id:
            continue
        path = ROOT / pdf_relative
        if not path.exists():
            continue
        try:
            rows, extraction = extract_pdf(by_id[paper_id], path)
            write_jsonl(TEXT_DIR / f"{paper_id}.jsonl", rows)
            entry["text_extraction"] = {**extraction, "updated_at": utc_now()}
            all_rows.extend(rows)
        except Exception as exc:
            entry["text_extraction"] = {
                "error": f"{type(exc).__name__}: {exc}"[:400],
                "updated_at": utc_now(),
            }
    write_jsonl(GLOBAL_INDEX, all_rows)
    manifest["fulltext_index"] = {
        "path": str(GLOBAL_INDEX.relative_to(ROOT)).replace("\\", "/"),
        "papers": len({row["paper_id"] for row in all_rows}),
        "chunks": len(all_rows),
        "updated_at": utc_now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", action="append", help="only process this seed id; repeatable")
    parser.add_argument(
        "--try-publisher",
        action="store_true",
        help="also try official publisher PDFs available from the current network",
    )
    parser.add_argument("--refresh", action="store_true", help="redownload PDFs already present")
    parser.add_argument("--metadata-only", action="store_true", help="discover sources without downloading")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between papers")
    args = parser.parse_args()

    papers: list[dict[str, Any]] = load_json(PAPERS_PATH, [])
    selected = set(args.paper_id or [])
    if selected:
        papers_to_process = [paper for paper in papers if paper["id"] in selected]
        missing = selected - {paper["id"] for paper in papers_to_process}
        if missing:
            parser.error(f"unknown paper id(s): {', '.join(sorted(missing))}")
    else:
        papers_to_process = papers

    manifest = load_json(
        MANIFEST_PATH,
        {"schema_version": 1, "policy": "read-only retrieval; no paywall bypass", "papers": {}},
    )
    entries = manifest.setdefault("papers", {})
    for index, paper in enumerate(papers_to_process, 1):
        print(f"[{index}/{len(papers_to_process)}] {paper['id']}", flush=True)
        entry = entries.setdefault(paper["id"], {})
        entry.update(
            {
                "title": paper["title"],
                "doi": paper["doi"],
                "wos_uid": paper.get("wos_uid"),
                "checked_at": utc_now(),
            }
        )
        try:
            oa, candidates = candidate_sources(paper, args.try_publisher)
            entry["open_access"] = oa
            entry["candidates"] = candidates
        except Exception as exc:
            entry["discovery_error"] = f"{type(exc).__name__}: {exc}"[:400]
            candidates = []

        destination = PDF_DIR / f"{paper['id']}.pdf"
        if destination.exists() and not args.refresh:
            existing_validation = validate_pdf(destination, paper["title"])
            if existing_validation.get("document_kind") == "supplementary":
                SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
                supplementary = SUPPLEMENTARY_DIR / f"{paper['id']}_supplementary.pdf"
                destination.replace(supplementary)
                entry["supplementary_pdf"] = str(supplementary.relative_to(ROOT)).replace("\\", "/")
                entry.pop("local_pdf", None)
                entry["status"] = "supplementary_only"
        if destination.exists() and not args.refresh:
            entry["status"] = "downloaded"
            entry["local_pdf"] = str(destination.relative_to(ROOT)).replace("\\", "/")
            entry["validation"] = validate_pdf(destination, paper["title"])
        elif not args.metadata_only:
            attempts: list[dict[str, Any]] = []
            for source in candidates:
                result = download_pdf(source["url"], destination)
                attempts.append({**source, **result, "attempted_at": utc_now()})
                if result.get("ok"):
                    validation = validate_pdf(destination, paper["title"])
                    if validation.get("document_kind") == "supplementary":
                        SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
                        supplementary = SUPPLEMENTARY_DIR / f"{paper['id']}_supplementary.pdf"
                        destination.replace(supplementary)
                        entry["supplementary_pdf"] = str(supplementary.relative_to(ROOT)).replace("\\", "/")
                        attempts[-1]["accepted_as_main_text"] = False
                        attempts[-1]["rejection_reason"] = "supplementary_material"
                        continue
                    entry["status"] = "downloaded"
                    entry["access_basis"] = source["basis"]
                    entry["source_url"] = result["final_url"]
                    entry["local_pdf"] = str(destination.relative_to(ROOT)).replace("\\", "/")
                    entry["sha256"] = result["sha256"]
                    entry["bytes"] = result["bytes"]
                    entry["validation"] = validation
                    attempts[-1]["accepted_as_main_text"] = True
                    break
            else:
                entry["status"] = "not_downloaded"
                entry.pop("local_pdf", None)
            entry["attempts"] = attempts
        else:
            entry["status"] = "metadata_only"
        save_json(MANIFEST_PATH, manifest)
        if index < len(papers_to_process):
            time.sleep(max(args.delay, 0))

    rebuild_fulltext_index(papers, manifest)
    manifest["updated_at"] = utc_now()
    save_json(MANIFEST_PATH, manifest)
    downloaded = sum(1 for row in entries.values() if row.get("status") == "downloaded")
    print(f"Downloaded/available PDFs: {downloaded}/{len(papers)}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Full-text index: {GLOBAL_INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
