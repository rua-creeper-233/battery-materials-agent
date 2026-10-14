"""Fail-closed checks for the public GitHub Pages publication bundle."""
from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class PublicationSafetyError(ValueError):
    """Raised when a public artifact cannot be proven safe to publish."""


PUBLIC_ZOTERO_KEYS = {"visibility", "items"}
FORBIDDEN_PATH = re.compile(
    r"(?:^|/)(?:private|literature/(?:pdfs|text)|models?|outputs?|training/(?:checkpoints|output))(?:/|$)|(?:^|/)\.env(?:[./]|$)|(?:^|/)(?:fulltext_chunks\.jsonl|zotero-links\.local\.json|SECURITY_PRIVACY_AUDIT_[^/]+\.md)$|(?:^|/)literature/manifest\.json$|(?:\.(?:pdf|safetensors|gguf|bin|pt|pth|zip|7z|sqlite)(?:-shm|-wal)?$)", re.I
)
CONTENT_RULES = (
    ("credential_format", re.compile(r"(?:AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|Bearer\s+(?!test[-_]|example[-_]|placeholder[-_])[A-Za-z0-9._-]{20,}|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}|\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,})", re.I)),
    ("signed_url", re.compile(r"https?://[^\s\"']+(?:[?&](?:sig|signature|x-amz-signature|token|expires|x-goog-signature)=|drive\.usercontent\.google\.com/download\?id=)[^\s\"']*", re.I)),
    ("zotero_private_key", re.compile(r"zotero://(?:items/|(?:open-pdf|select)/(?:library|groups/\d+)/items/)[A-Z0-9]{8}(?=[/?#\s\"']|$)", re.I)),
    ("windows_user_path", re.compile(r"(?:[A-Za-z]:[\\/]Users[\\/](?![<\[(])[^\\/\s<>'\"]+|/mnt/[a-z]/Users/(?![<\[(])[^/\s<>'\"]+|/home/(?![<\[(])[^/\s<>'\"]+)", re.I)),
    ("email_address", re.compile(r"(?<![A-Za-z0-9._%+:/-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])")),
    ("phone_number", re.compile(r"(?:\+\d[\d ()-]{8,}\d|\b\d{3}[- )]\d{3}[- ]\d{4}\b)")),
    ("fulltext_verification", re.compile(r"verified_local_pdf[_-]\d{4}-\d{2}-\d{2}", re.I)),
    ("personal_access_trace", re.compile(r"verified_institution_session[_-]\d{4}-\d{2}-\d{2}", re.I)),
)
PRIVATE_DATA_FIELDS = {
    "local_pdf_url", "fulltext_paper_ids", "fulltext_paper_count",
    "private_pdf", "restricted_pdf", "model_weights", "attachment_key", "item_key",
    "local_fulltext_papers", "local_fulltext_missing", "indexed_chunks", "indexed_papers",
    "api_key", "apikey", "access_token", "bearer_token", "password", "client_secret", "private_key",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    type: str


def validate_public_zotero_map(value: object) -> dict:
    """Require the intentionally empty public Zotero allowlist."""
    if isinstance(value, (str, Path)):
        import json
        value = json.loads(Path(value).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != PUBLIC_ZOTERO_KEYS:
        raise PublicationSafetyError("public Zotero map must contain exactly visibility and items")
    if value.get("visibility") != "public_sanitized":
        raise PublicationSafetyError("public Zotero map must be public_sanitized")
    if not isinstance(value.get("items"), dict) or value["items"]:
        raise PublicationSafetyError("public Zotero items must be an empty object")
    return value


# Descriptive aliases kept small so callers do not need to depend on the
# implementation name used by the build script.
validate_public_zotero = validate_public_zotero_map


def sanitize_method_evidence(value: dict) -> dict:
    """Return only metadata and short method signals; omit local evidence locators."""
    if not isinstance(value, dict) or not isinstance(value.get("papers"), dict):
        raise PublicationSafetyError("method evidence must contain a papers object")
    # Method extraction is local evidence, not a publication entitlement.  A
    # non-empty map would disclose which papers have private holdings, so the
    # public payload is intentionally empty until a separately reviewed map is
    # designed.
    papers = {}
    return {"schema_version": 1, "review_status": value.get("review_status", ""),
            "notice_zh": value.get("notice_zh", ""), "papers": papers}


def scan_text(text: str, path: str = "<memory>", *, include_structured_fields: bool | None = None) -> list[Finding]:
    if include_structured_fields is None:
        include_structured_fields = path.lower().endswith((".json", ".jsonl"))
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for kind, rule in CONTENT_RULES:
            if rule.search(line):
                findings.append(Finding(path, line_no, kind))
    if include_structured_fields:
        try:
            values = [json.loads(line) for line in text.splitlines() if line.strip()] if path.lower().endswith(".jsonl") else [json.loads(text)]
        except json.JSONDecodeError as exc:
            raise PublicationSafetyError(f"invalid structured publication input: {path}") from exc

        def walk(value, parent_key=""):
            if isinstance(value, dict):
                for key, item in value.items():
                    key_name = str(key).lower()
                    sensitive_fulltext = key_name == "fulltext" and parent_key == "verification"
                    if (key_name in PRIVATE_DATA_FIELDS or sensitive_fulltext) and item not in (None, "", {}, []):
                        key_match = re.search(r'"' + re.escape(str(key)) + r'"\s*:', text)
                        line = text.count("\n", 0, key_match.start()) + 1 if key_match else 1
                        findings.append(Finding(path, line, "private_evidence_value"))
                    walk(item, key_name)
            elif isinstance(value, list):
                for item in value:
                    walk(item, parent_key)

        for value in values:
            walk(value)
        if path.replace("\\", "/").endswith("zotero-links.json"):
            validate_public_zotero_map(values[0])
    return findings


def scan_files(paths: Iterable[Path], root: Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    root = root or Path.cwd()
    for path in paths:
        rel = path.relative_to(root).as_posix() if path.is_absolute() and path.is_relative_to(root) else str(path).replace("\\", "/")
        if FORBIDDEN_PATH.search(rel):
            findings.append(Finding(rel, 0, "forbidden_path"))
            continue
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise PublicationSafetyError(f"unable to decode publication input: {rel}") from exc
            findings.extend(scan_text(content, rel, include_structured_fields=rel.lower().endswith((".json", ".jsonl"))))
    return findings


scan_public_bundle = scan_files


def _git_executable() -> str:
    configured = os.environ.get("PUBLICATION_GIT_EXE", "")
    if configured:
        candidate = Path(configured)
        if not candidate.is_file() or candidate.name.lower() not in {"git", "git.exe"}:
            raise PublicationSafetyError("PUBLICATION_GIT_EXE is not a safe git executable")
        return str(candidate)
    found = shutil.which("git")
    if not found:
        raise PublicationSafetyError("git executable is unavailable")
    return found


def scan_staged_snapshot(root: Path) -> list[Finding]:
    """Scan exactly the complete index snapshot, without printing values."""
    git = _git_executable()
    safe_root = str(root.resolve())
    result = subprocess.run([git, "-c", f"safe.directory={safe_root}", "ls-files", "-s", "-z"], cwd=root, text=False, capture_output=True, check=False)
    if result.returncode:
        raise PublicationSafetyError("unable to enumerate the staged publication snapshot")
    findings: list[Finding] = []
    for record in result.stdout.decode("utf-8").split("\0"):
        if not record:
            continue
        try:
            _, name = record.split("\t", 1)
        except ValueError as exc:
            raise PublicationSafetyError("invalid git index record") from exc
        if FORBIDDEN_PATH.search(name.replace("\\", "/")):
            findings.append(Finding(name, 0, "forbidden_path"))
            continue
        blob = subprocess.run([git, "-c", f"safe.directory={safe_root}", "show", f":{name}"], cwd=root, text=False, capture_output=True, check=False)
        if blob.returncode:
            raise PublicationSafetyError("unable to read a staged publication file")
        try:
            content = blob.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicationSafetyError(f"unable to decode staged publication file: {name}") from exc
        findings.extend(scan_text(content, name, include_structured_fields=name.lower().endswith((".json", ".jsonl"))))
    return findings


def assert_clean(findings: Iterable[Finding]) -> None:
    findings = list(findings)
    if findings:
        summary = ", ".join(f"{f.path}:{f.line}:{f.type}" for f in findings[:20])
        raise PublicationSafetyError(f"publication safety check failed ({summary})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan staged or public publication inputs without printing sensitive values")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--staged", action="store_true", help="scan the complete Git index snapshot")
    parser.add_argument("--public-bundle", action="store_true", help="scan tracked files under docs/")
    args = parser.parse_args()
    if args.staged == args.public_bundle:
        parser.error("choose exactly one of --staged or --public-bundle")
    try:
        findings = scan_staged_snapshot(args.root) if args.staged else scan_files((args.root / "docs").rglob("*"), args.root)
    except PublicationSafetyError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    payload = {"ok": not findings, "findings": [{"path": f.path, "line": f.line, "type": f.type} for f in findings]}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
