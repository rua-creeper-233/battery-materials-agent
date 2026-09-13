"""Local-only paper ingestion and keyword extraction for Battery Evidence Lab.

Uploaded PDFs and user-added metadata are deliberately kept out of the public
GitHub Pages bundle.  The stable HTTP contract lives in ``server.py``:
``POST /api/upload`` and ``POST /api/keywords``.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fetch_literature import rebuild_fulltext_index, save_json, validate_pdf


ROOT = Path(__file__).resolve().parent
SEED_PAPERS = ROOT / "data" / "papers.json"
USER_PAPERS = ROOT / "private" / "user-papers.local.json"
MANIFEST = ROOT / "literature" / "manifest.json"
PDF_DIR = ROOT / "literature" / "pdfs"
MAX_PDF_BYTES = 50 * 1024 * 1024

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]{2,}")

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "have", "has", "into", "using", "used", "study", "results",
    "their", "than", "these", "which", "can", "may", "also", "between",
    "through", "during", "based", "first", "principles", "paper", "figure",
    "table", "supplementary", "copyright", "article", "journal", "abstract",
}

DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "density functional theory": ("density functional theory", "dft"),
    "first-principles calculation": ("first-principles calculation", "first principles calculation", "ab initio calculation"),
    "VASP": ("vasp", "vienna ab initio simulation package"),
    "molecular dynamics": ("molecular dynamics", "aimd", "ab initio molecular dynamics"),
    "machine-learning potential": ("machine learning potential", "machine-learning potential", "neural network potential", "mlip"),
    "nudged elastic band": ("nudged elastic band", "ci-neb", "climbing image"),
    "lithium diffusion": ("lithium diffusion", "li diffusion", "ionic diffusion", "migration barrier"),
    "diffusion coefficient": ("diffusion coefficient", "diffusivity", "mean squared displacement", "mean-squared displacement"),
    "activation energy": ("activation energy", "arrhenius"),
    "solid electrolyte": ("solid electrolyte", "superionic conductor", "ionic conductivity"),
    "electrochemical stability": ("electrochemical stability", "stability window", "phase stability"),
    "electrode interface": ("electrode interface", "electrode-electrolyte interface", "solid electrolyte interphase", "sei"),
    "formation energy": ("formation energy", "defect formation", "energy above hull"),
    "voltage": ("voltage", "open circuit voltage", "intercalation voltage"),
    "lithium-ion battery": ("lithium-ion battery", "lithium ion battery", "li-ion battery"),
    "cathode material": ("cathode material", "cathode", "positive electrode"),
    "layered oxide": ("layered oxide", "layered transition metal oxide"),
    "intercalation": ("intercalation", "deintercalation"),
    "charge density": ("charge density", "charge transfer", "bader charge"),
    "Materials Project": ("materials project",),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_doi(value: str | None) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    return text.rstrip(".,;:) ]}")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_library_papers(
    seed_path: Path = SEED_PAPERS,
    user_path: Path | None = USER_PAPERS,
) -> list[dict[str, Any]]:
    seeds = _read_json(seed_path, [])
    users = _read_json(user_path, []) if user_path else []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for paper in [*seeds, *users]:
        if not isinstance(paper, dict) or not paper.get("id"):
            continue
        key = normalize_doi(paper.get("doi")) or str(paper["id"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(paper)
    return rows


class KeywordExtractor:
    """Dependency-free baseline behind the versioned keyword API."""

    api_version = "v1"
    provider = "builtin-domain-frequency"

    def extract(self, text: str, limit: int = 12) -> list[dict[str, Any]]:
        clean = re.sub(r"\s+", " ", text or "").strip()
        lowered = clean.lower()
        scores: Counter[str] = Counter()
        for label, aliases in DOMAIN_TERMS.items():
            hits = sum(lowered.count(alias.lower()) for alias in aliases)
            if hits:
                scores[label] += 6 + min(hits, 8)

        words = [word.lower() for word in WORD_RE.findall(clean)]
        counts = Counter(word for word in words if word not in STOPWORDS and not word.isdigit())
        for word, count in counts.most_common(limit * 3):
            if len(word) >= 4:
                scores[word] += min(count, 6)

        return [
            {"term": term, "score": int(score), "source": self.provider}
            for term, score in scores.most_common(max(1, min(limit, 30)))
        ]


KEYWORDS = KeywordExtractor()


def _first_pages_text(path: Path, page_limit: int = 5) -> tuple[str, int, dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("缺少 pypdf；请先运行：python -m pip install -r requirements.txt") from exc

    reader = PdfReader(path)
    text = "\n".join(
        reader.pages[index].extract_text() or ""
        for index in range(min(page_limit, len(reader.pages)))
    )
    metadata = dict(reader.metadata or {})
    return text, len(reader.pages), metadata


def _suggest_title(text: str, filename: str, pdf_metadata: dict[str, Any]) -> str:
    metadata_title = str(pdf_metadata.get("/Title") or "").strip()
    if 12 <= len(metadata_title) <= 400 and metadata_title.lower() not in {"untitled", "unknown"}:
        return re.sub(r"\s+", " ", metadata_title)
    for raw in text.splitlines()[:60]:
        line = re.sub(r"\s+", " ", raw).strip(" -")
        if 20 <= len(line) <= 300 and not DOI_RE.search(line) and len(line.split()) >= 4:
            return line
    return re.sub(r"[_-]+", " ", Path(filename).stem).strip()[:300]


def _split_authors(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;；\n]+", value or "") if part.strip()]


def _make_paper_id(title: str, year: int, doi: str, digest: str) -> str:
    source = doi or title or digest
    slug = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")[:34]
    return f"upload_{year}_{slug or digest[:10]}_{digest[:8]}"


def _save_user_paper(paper: dict[str, Any]) -> None:
    rows = _read_json(USER_PAPERS, [])
    by_id = {str(row.get("id")): row for row in rows if isinstance(row, dict)}
    by_id[paper["id"]] = paper
    USER_PAPERS.parent.mkdir(parents=True, exist_ok=True)
    USER_PAPERS.write_text(
        json.dumps(list(by_id.values()), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def ingest_pdf(
    pdf_bytes: bytes,
    filename: str,
    fields: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate, index, and add a PDF to the local private library."""
    fields = fields or {}
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("上传文件不是有效的 PDF。")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("PDF 超过 50 MiB 上限。")

    digest = hashlib.sha256(pdf_bytes).hexdigest()
    stage_dir = ROOT / "private" / "upload-staging"
    stage_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=stage_dir, suffix=".pdf", delete=False) as handle:
        handle.write(pdf_bytes)
        staged = Path(handle.name)

    try:
        text, page_count, pdf_metadata = _first_pages_text(staged)
        doi = normalize_doi(fields.get("doi"))
        if not doi:
            match = DOI_RE.search(text)
            doi = normalize_doi(match.group(0)) if match else ""
        title = re.sub(r"\s+", " ", fields.get("title", "")).strip()
        if not title:
            title = _suggest_title(text, filename, pdf_metadata)
        year_text = (fields.get("year") or "").strip()
        if not year_text:
            match = YEAR_RE.search(str(pdf_metadata.get("/CreationDate", "")) + " " + text[:12000])
            year_text = match.group(0) if match else str(datetime.now().year)
        year = int(year_text)
        if not 1900 <= year <= datetime.now().year + 1:
            raise ValueError("年份不在合理范围内。")

        papers = load_library_papers()
        existing = next(
            (
                row for row in papers
                if (doi and normalize_doi(row.get("doi")) == doi)
                or str(row.get("title", "")).casefold() == title.casefold()
            ),
            None,
        )
        is_new = existing is None
        if existing:
            paper = dict(existing)
        else:
            paper_id = _make_paper_id(title, year, doi, digest)
            summary_text = re.sub(r"\s+", " ", text).strip()[:500]
            keywords = KEYWORDS.extract(f"{title}\n{text[:40000]}")
            tags = [row["term"] for row in keywords[:10]]
            paper = {
                "id": paper_id,
                "title": title,
                "authors": _split_authors(fields.get("authors", "")) or ["待补充"],
                "year": year,
                "journal": fields.get("journal", "").strip() or "用户上传文献",
                "document_type": "Article",
                "doi": doi,
                "url": f"https://doi.org/{doi}" if doi else "",
                "role": "用户上传的电池材料计算文献",
                "systems": [],
                "methods": tags,
                "properties": [],
                "tags_zh": tags,
                "summary": summary_text,
                "evidence": [],
                "relations": [],
                "wos_uid": "",
                "verification": {
                    "source": "user_upload",
                    "doi": "user_supplied_or_pdf_extracted" if doi else "missing",
                    "wos": "not_checked",
                },
            }

        validation = validate_pdf(staged, paper["title"])
        if not validation.get("valid_pdf"):
            raise ValueError(f"PDF 解析失败：{validation.get('validation_error', '未知错误')}")
        if validation.get("document_kind") != "article":
            raise ValueError("检测到的文件更像补充材料，请上传论文正文 PDF。")

        PDF_DIR.mkdir(parents=True, exist_ok=True)
        destination = PDF_DIR / f"{paper['id']}.pdf"
        if destination.exists():
            existing_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
            if existing_digest != digest:
                raise ValueError("该条目已有另一份 PDF；为避免误覆盖，本次未替换。")
            staged.unlink(missing_ok=True)
        else:
            staged.replace(destination)

        if is_new:
            _save_user_paper(paper)

        manifest = _read_json(MANIFEST, {"schema_version": 1, "papers": {}})
        entry = manifest.setdefault("papers", {}).setdefault(paper["id"], {})
        entry.update(
            {
                "title": paper["title"],
                "doi": paper.get("doi", ""),
                "wos_uid": paper.get("wos_uid", ""),
                "status": "downloaded",
                "access_basis": "user_supplied_authorized_copy",
                "local_pdf": str(destination.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest,
                "bytes": destination.stat().st_size,
                "validation": validation,
                "uploaded_at": utc_now(),
                "original_filename": Path(filename).name,
            }
        )
        all_papers = load_library_papers()
        rebuild_fulltext_index(all_papers, manifest)
        manifest["updated_at"] = utc_now()
        save_json(MANIFEST, manifest)

        keywords = KEYWORDS.extract(f"{paper['title']}\n{text[:60000]}")
        return {
            "ok": True,
            "created": is_new,
            "paper": paper,
            "pdf": {
                "pages": page_count,
                "bytes": len(pdf_bytes),
                "sha256": digest,
                "indexed": True,
            },
            "keywords": keywords,
            "keyword_api": {
                "version": KEYWORDS.api_version,
                "provider": KEYWORDS.provider,
                "endpoint": "/api/keywords",
            },
        }
    finally:
        staged.unlink(missing_ok=True)
