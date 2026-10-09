"""Usage: 05_download_list.py <codex_csv> <out_csv>. Download PL/KZ reports from Codex-found URLs, extract text, count AI sentences."""
import csv, os, re, subprocess, sys, urllib.request, zipfile, io
sys.path.insert(0, os.path.dirname(__file__))
from textutil import xhtml_to_text, ai_hits

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
import sys as _s
SRC, OUT = _s.argv[1], _s.argv[2]
rows = []
for line in open(SRC):
    p = line.strip().split(";")
    if len(p) >= 9 and p[0] in ("Poland", "Kazakhstan", "PL", "KZ") and p[8] in ("FOUND", "FOUND_INDEXED", "VERIFIED", "VERIFIED_LINK"):
        rows.append(dict(country="Poland" if p[0] in ("Poland", "PL") else "Kazakhstan", company=p[1], year=p[4], lang=p[5], url=p[7]))

def to_text(data, url, fn="x"):
    if data[:4] == b"%PDF":
        tmp = "data/raw/_tmp_" + os.path.basename(fn) + ".pdf"; open(tmp, "wb").write(data)
        return subprocess.run(["pdftotext", "-layout", tmp, "-"], capture_output=True, text=True).stdout
    if data[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(data)); parts = []
        for n in z.namelist():
            if n.lower().endswith((".xhtml", ".html", ".htm")):
                parts.append(xhtml_to_text(z.read(n).decode("utf-8", "ignore")))
            elif n.lower().endswith(".pdf"):
                parts.append(to_text(z.read(n), n, fn + n))
        return "\n".join(parts)
    return xhtml_to_text(data.decode("utf-8", "ignore"))

def work(r):
    code = "PL" if r["country"] == "Poland" else "KZ"
    slug = re.sub(r"\W+", "_", r["company"]).strip("_")
    fn = f"data/text/{code}_{slug}_{r['year']}.txt"
    status = "ok"
    if not os.path.exists(fn):
        try:
            data = urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=45).read()
            t = to_text(data, r["url"], fn)
            if len(t) < 5000: status = f"short({len(t)})"
            open(fn, "w").write(t)
        except Exception as e:
            status = "ERR " + str(e)[:60]
    t = open(fn).read() if os.path.exists(fn) else ""
    h = ai_hits(t)
    print(code, r["company"], r["year"], status, len(t), len(h), file=sys.stderr, flush=True)
    return dict(country=code, company=r["company"], year=r["year"], lang=r["lang"], status=status,
                chars=len(t), ai_sentences=len(h), sample=" || ".join(s[:160] for s in h[:3]), url=r["url"])

import concurrent.futures as cf
with cf.ThreadPoolExecutor(8) as ex:
    out = list(ex.map(work, rows))

with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
