"""Download PL/KZ pilot reports from Codex-found URLs, extract text, count AI sentences."""
import csv, os, re, subprocess, sys, urllib.request, zipfile, io
sys.path.insert(0, os.path.dirname(__file__))
from textutil import xhtml_to_text, ai_hits

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
rows = []
for line in open("data/pl_kz_report_urls_raw.txt"):
    p = line.strip().split(";")
    if len(p) >= 7 and p[0] in ("Poland", "Kazakhstan") and p[6] == "FOUND":
        rows.append(dict(country=p[0], company=p[1], year=p[2], lang=p[3], url=p[5]))

def to_text(data, url):
    if data[:4] == b"%PDF":
        tmp = "data/raw/_tmp.pdf"; open(tmp, "wb").write(data)
        return subprocess.run(["pdftotext", "-layout", tmp, "-"], capture_output=True, text=True).stdout
    if data[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(data)); parts = []
        for n in z.namelist():
            if n.lower().endswith((".xhtml", ".html", ".htm")):
                parts.append(xhtml_to_text(z.read(n).decode("utf-8", "ignore")))
            elif n.lower().endswith(".pdf"):
                parts.append(to_text(z.read(n), n))
        return "\n".join(parts)
    return xhtml_to_text(data.decode("utf-8", "ignore"))

out = []
for r in rows:
    code = "PL" if r["country"] == "Poland" else "KZ"
    slug = re.sub(r"\W+", "_", r["company"]).strip("_")
    fn = f"data/text/{code}_{slug}_{r['year']}.txt"
    status = "ok"
    if not os.path.exists(fn):
        try:
            data = urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=180).read()
            t = to_text(data, r["url"])
            if len(t) < 5000: status = f"short({len(t)})"
            open(fn, "w").write(t)
        except Exception as e:
            status = "ERR " + str(e)[:60]; t = ""
    t = open(fn).read() if os.path.exists(fn) else ""
    h = ai_hits(t)
    out.append(dict(country=code, company=r["company"], year=r["year"], lang=r["lang"], status=status,
                    chars=len(t), ai_sentences=len(h), sample=" || ".join(s[:160] for s in h[:3]), url=r["url"]))
    print(code, r["company"], r["year"], status, len(t), len(h), file=sys.stderr)

with open("data/pl_kz_pilot_counts.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
