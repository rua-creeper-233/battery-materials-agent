"""Copy selected existing Zotero PDFs into the ignored local evidence cache.

Read-only towards Zotero: no metadata changes or duplicate import. Select paper
IDs explicitly, match DOI, validate title/body before retaining a local copy.
"""
import argparse
import shutil
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import import_zotero_library as zotero
from fetch_literature import MANIFEST_PATH, PAPERS_PATH, PDF_DIR, load_json, save_json, validate_pdf


def is_matching_main_article(check: dict) -> bool:
    """Accept readable main articles only when the first pages identify the title."""
    return (
        check.get('valid_pdf') is True
        and check.get('document_kind') == 'article'
        and int(check.get('first_pages_text_chars') or 0) >= 500
        and float(check.get('title_token_match') or 0) >= 0.35
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-id', action='append', required=True)
    args = parser.parse_args()
    wanted = set(args.paper_id)
    papers = [p for p in load_json(PAPERS_PATH, []) if p['id'] in wanted]
    if wanted - {p['id'] for p in papers}:
        raise SystemExit('Unknown selected paper IDs')
    items = {zotero._item_doi(i): i for i in zotero.list_top_items()}
    manifest = load_json(MANIFEST_PATH, {'papers': {}})
    copied = 0
    for paper in papers:
        target = PDF_DIR / (paper['id'] + '.pdf')
        if target.exists():
            print(paper['id'], 'cache_exists; unchanged')
            continue
        parent = items.get(paper['doi'].lower())
        if not parent:
            print(paper['id'], 'DOI_not_found')
            continue
        key = parent.get('key') or parent.get('data', {}).get('key')
        for child in zotero.list_children(key):
            link = child.get('links', {}).get('enclosure', {})
            parsed = urlparse(link.get('href', ''))
            if parsed.scheme != 'file' or parsed.netloc not in ('', 'localhost'):
                continue
            source = Path(url2pathname(parsed.path))
            if source.suffix.lower() != '.pdf' or not source.is_file():
                continue
            check = validate_pdf(source, paper['title'])
            if not is_matching_main_article(check):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            manifest.setdefault('papers', {}).setdefault(paper['id'], {}).update({
                'title': paper['title'], 'doi': paper['doi'], 'status': 'downloaded',
                'local_pdf': 'literature/pdfs/' + target.name,
                'access_basis': 'user_existing_Zotero_attachment',
                'validation': check,
            })
            copied += 1
            print(paper['id'], 'copied_validated_existing_attachment')
            break
        else:
            print(paper['id'], 'no_validated_local_main_PDF')
    save_json(MANIFEST_PATH, manifest)
    print('Copied', copied, 'PDFs; run audit_library.py before publication')


if __name__ == '__main__':
    main()
