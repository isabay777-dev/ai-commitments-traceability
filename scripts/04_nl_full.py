"""All NL-filed ESEF annual reports 2021-2025 (excl. UK/other PLC/Ltd), text + AI sentence counts."""
import csv, os, re, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from textutil import xhtml_to_text, ai_hits

EXCL = re.compile(r"\b(PLC|Ltd\.?|Limited|Trust)\b", re.I)
rows = [x for x in csv.DictReader(open("data/esef_filings.csv"))
        if x["country"] == "NL" and x["report_url"] and not EXCL.search(x["name"] or "")]
pick = {}
for x in sorted(rows, key=lambda z: int(z["error_count"] or 0)):
    y = x["period_end"][:4]
    if "2021" <= y <= "2025" and x["period_end"][5:] in ("12-31", "06-30", "03-31", "09-30"):
        pick.setdefault((x["lei"], y), x)

def work(item):
    (lei, y), x = item
    fn = f"data/text/NL_{lei}_{y}.txt"
    try:
        if not os.path.exists(fn):
            s = urllib.request.urlopen("https://filings.xbrl.org" + x["report_url"], timeout=300).read().decode("utf-8", "ignore")
            open(fn, "w").write(xhtml_to_text(s))
        t = open(fn).read(); st = "ok"
    except Exception as e:
        t = ""; st = "ERR " + str(e)[:50]
    return dict(country="NL", lei=lei, company=x["name"], year=y, period_end=x["period_end"], status=st,
                chars=len(t), ai_sentences=len(ai_hits(t)) if t else 0)

with cf.ThreadPoolExecutor(6) as ex:
    out = list(ex.map(work, sorted(pick.items())))
with open("data/nl_full_counts.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
ok = [o for o in out if o["status"] == "ok"]
print("firm-years", len(out), "ok", len(ok), "firms", len({o["lei"] for o in ok}))
import collections
print(sorted(collections.Counter(o["year"] for o in ok).items()))
