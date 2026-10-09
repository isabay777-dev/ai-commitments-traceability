"""Download NL pilot ESEF reports (12 firms x 2021/2023/2025), extract text, count AI sentences."""
import csv, json, os, sys, urllib.request, collections
sys.path.insert(0, os.path.dirname(__file__))
from textutil import xhtml_to_text, ai_hits

PILOT = ["ASML Holding N.V.", "ABN AMRO Bank N.V.", "Akzo Nobel N.V.", "Heineken N.V.",
         "Koninklijke KPN N.V.", "Koninklijke Philips N.V.", "PostNL N.V.", "Randstad N.V.",
         "Wolters Kluwer N.V.", "ARCADIS N.V.", "Fugro N.V.", "Nedap N.V."]
YEARS = ["2021", "2023", "2025"]

rows = [x for x in csv.DictReader(open("data/esef_filings.csv")) if x["country"] == "NL" and x["report_url"]]
pick = {}
for x in rows:
    y = x["period_end"][:4]
    if x["name"] in PILOT and y in YEARS:
        pick.setdefault((x["name"], y), x)  # first filing per firm-year

out = []
for (name, y), x in sorted(pick.items()):
    fn = f"data/text/NL_{x['lei']}_{y}.txt"
    if not os.path.exists(fn):
        s = urllib.request.urlopen("https://filings.xbrl.org" + x["report_url"], timeout=300).read().decode("utf-8", "ignore")
        open(fn, "w").write(xhtml_to_text(s))
    t = open(fn).read()
    h = ai_hits(t)
    out.append({"country": "NL", "company": name, "year": y, "chars": len(t), "ai_sentences": len(h),
                "board_expertise_terms": sum(t.lower().count(k) for k in ["supervisory board", "board of directors"]),
                "sample": " || ".join(s[:160] for s in h[:3])})
    print(name, y, len(t), len(h), file=sys.stderr)

with open("data/nl_pilot_counts.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
print("firm-years:", len(out), "of", len(PILOT) * len(YEARS))
