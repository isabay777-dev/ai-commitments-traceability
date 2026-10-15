"""Sequential public-report retrieval/extraction with explicit failures and no retries.

Input JSON: list of {file, url, country, role}. Each source URL is fetched once.
The user explicitly authorised sources above 100 MB on 15 October 2026. The
revised working limit is 512 MiB and 180 seconds per response. No credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'sources_first_followup'
MAX_BYTES = 512 * 1024 * 1024


def retrieve(doc):
    record = dict(doc, status='unattempted')
    if not doc.get('url'):
        return dict(record, status='url_unresolved')
    path = BASE / 'text' / doc['file']
    # Manifest entries, not just existing files, authorise reuse below.
    url = urllib.parse.quote(doc['url'], safe=':/?=&%+#@,;~!$\'()*[]')
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research report retrieval)'})
        with urllib.request.urlopen(request, timeout=180) as response:
            content_type = response.headers.get('Content-Type', '')
            chunks = []; size = 0
            while True:
                if time.monotonic() - started > 180:
                    raise TimeoutError('180-second response budget exhausted; not retried')
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Source exceeds authorised working limit 512 MiB; not retried')
                chunks.append(chunk)
            data = b''.join(chunks)
            record.update(final_url=response.geturl(), content_type=content_type,
                          http_status=response.status)
        digest = hashlib.sha256(data).hexdigest()
        if data.startswith(b'%PDF'):
            extension = '.pdf'; kind = 'pdf'
        elif data.startswith(b'PK'):
            extension = '.zip'; kind = 'unsupported_archive'
        elif b'<html' in data[:3000].lower() or b'<?xml' in data[:100].lower() or 'html' in content_type:
            extension = '.html'; kind = 'html'
        else:
            extension = '.bin'; kind = 'unsupported_content'
        raw = BASE / 'raw' / (digest + extension)
        if not raw.exists():
            raw.write_bytes(data)
        record.update(source_sha256=digest, source_bytes=len(data),
                      raw_path=str(raw.relative_to(ROOT)), kind=kind)
        if kind == 'pdf':
            subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(raw), str(path)],
                           check=True, timeout=120, capture_output=True)
            text = path.read_text()
            record['extraction_engine'] = 'Poppler pdftotext -layout'
        elif kind == 'html':
            soup = BeautifulSoup(data, 'lxml')
            record['html_title'] = soup.title.get_text(' ', strip=True) if soup.title else ''
            for tag in list(soup.find_all(['script', 'style', 'head'])):
                tag.decompose()
            for tag in list(soup.find_all(lambda t: t.name and t.name.lower() in ['ix:hidden', 'ix:header'])):
                tag.decompose()
            text = soup.get_text('\n', strip=True)
            path.write_text(text)
            record['extraction_engine'] = 'BeautifulSoup lxml visible body text; ix:hidden/header removed'
        else:
            return dict(record, status=kind, elapsed_seconds=round(time.monotonic()-started, 2))
        record.update(text_path=str(path.relative_to(ROOT)), text_characters=len(text),
                      text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      text_sha256_scope='UTF-8 extracted text after Python universal-newline normalization',
                      text_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      pages=text.count('\f') if kind == 'pdf' else None,
                      status='extracted_unverified' if len(text) >= 1000 else 'extraction_insufficient',
                      elapsed_seconds=round(time.monotonic()-started, 2))
    except Exception as error:
        record.update(status='retrieval_or_extraction_failed', error=str(error)[:500],
                      elapsed_seconds=round(time.monotonic()-started, 2))
    return record


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    for child in ['text', 'raw']:
        (BASE / child).mkdir(parents=True, exist_ok=True)
    output = BASE / 'retrieval_manifest.json'
    old = json.loads(output.read_text()) if output.exists() else []
    indexed = {(r['file'], r.get('url', '')): r for r in old}
    docs = json.loads(args.manifest.read_text())
    results = []
    for i, doc in enumerate(docs):
        assert Path(doc['file']).name == doc['file'] and doc['file'].endswith('.txt')
        key = (doc['file'], doc.get('url', ''))
        if key in indexed:
            record = indexed[key]  # includes failed attempts: never silently retry
        else:
            record = retrieve(doc); indexed[key] = record
        results.append(record)
        output.write_text(json.dumps(list(indexed.values()), ensure_ascii=False, indent=2))
        print(f"{i+1}/{len(docs)} {doc['country']} {doc['file']} {record['status']}", flush=True)
    print('Retrieval complete; extraction is not entity/year verification or outcome coding.', flush=True)


if __name__ == '__main__':
    main()
