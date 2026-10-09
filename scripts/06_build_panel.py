"""Combine NL/PL/KZ counts into one firm-year panel and print country-year summary."""
import csv, collections, statistics as st

def load(fn):
    return list(csv.DictReader(open(fn)))

ALIAS = {"КазАзот": "KazAzot", "КазТрансОйл": "KazTransOil", "Казатомпром": "Kazatomprom", "Казахтелеком": "Kazakhtelecom"}
panel = {}
for fn in ["data/pl_kz_pilot_counts.csv", "data/pl_full_counts.csv", "data/kz_full_counts.csv", "data/kz_expansion_counts.csv", "data/nl_full_counts.csv"]:
    for x in load(fn):
        if int(x["chars"]) < 50000:
            continue
        name = ALIAS.get(x["company"].strip(), x["company"].strip())
        key = (x["country"], name.lower(), x["year"])
        panel.setdefault(key, dict(country=x["country"], company=name, year=x["year"],
                                   chars=int(x["chars"]), ai_sentences=int(x["ai_sentences"])))

rows = sorted(panel.values(), key=lambda r: (r["country"], r["company"], r["year"]))
for r in rows:
    r["ai_any"] = int(r["ai_sentences"] > 0)
    r["ai_per_100k_chars"] = round(r["ai_sentences"] / r["chars"] * 1e5, 3)
with open("data/panel_ai_disclosure.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print("firm-years", len(rows))
for c in ["KZ", "PL", "NL"]:
    cr = [r for r in rows if r["country"] == c]
    print(f"\n{c}: firm-years {len(cr)}, firms {len({r['company'].lower() for r in cr})}")
    by = collections.defaultdict(list)
    for r in cr: by[r["year"]].append(r)
    for y in sorted(by):
        v = by[y]
        print(f"  {y}: n={len(v):3d}  share_AI={sum(r['ai_any'] for r in v)/len(v):.2f}  "
              f"median_per100k={st.median(r['ai_per_100k_chars'] for r in v):.2f}  "
              f"mean_per100k={st.mean(r['ai_per_100k_chars'] for r in v):.2f}")
