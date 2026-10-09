"""List ESEF filings for PL and NL from filings.xbrl.org (free JSON API)."""
import json, urllib.request, csv, time, sys

def fetch(url):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except Exception as e:
            time.sleep(3)
    raise RuntimeError(url)

rows = []
for c in ["PL", "NL"]:
    url = f"https://filings.xbrl.org/api/filings?filter[country]={c}&include=entity&page[size]=200"
    while url:
        d = fetch(url)
        ents = {e["id"]: e["attributes"] for e in d.get("included", []) if e["type"] == "entity"}
        for f in d["data"]:
            a = f["attributes"]
            eid = f["relationships"]["entity"]["data"]["id"]
            e = ents.get(eid, {})
            rows.append({"country": c, "lei": e.get("identifier"), "name": e.get("name"),
                         "period_end": a.get("period_end"), "fxo_id": a.get("fxo_id"),
                         "package_url": a.get("package_url"), "report_url": a.get("report_url"),
                         "json_url": a.get("json_url"), "error_count": a.get("error_count")})
        url = d.get("links", {}).get("next")
        print(c, len(rows), file=sys.stderr)

with open("data/esef_filings.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("total", len(rows))
