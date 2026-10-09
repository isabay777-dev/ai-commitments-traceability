"""Narrow definition of board digital expert: explicit CIO/CTO/CDO-type role or IT/CS education in the verified evidence."""
import csv, glob, re, collections
NARROW = re.compile(r"\b(CIO|CTO|CDO|CISO)\b|chief (information|technology|digital|data|technical)|"
                    r"\bIT director|director of (IT|information technolog|digital)|head of (IT|digital|technology)|"
                    r"computer science|informatics|information technolog|software engineer|data scien|cyber|"
                    r"директор\w* по (IT|ИТ|информационн|цифров)|информационн\w* технолог|информатик|программ|"
                    r"cyfryzac|informatyk|technologii informacyjnych", re.I)
cnt = collections.defaultdict(int); tot = collections.Counter()
for f in glob.glob("data/gov_verify/rows_*.csv"):
    for l in open(f):
        p = l.rstrip("\n").split(";")
        if len(p) >= 5 and p[2].strip() == "yes":
            narrow = bool(NARROW.search(p[4]))
            tot[(p[0][:2], narrow)] += 1
            if narrow: cnt[p[0]] += 1
print({f"{c} narrow={n}": v for (c, n), v in sorted(tot.items())})
rows = list(csv.DictReader(open("data/panel_kz_pl_ai_gov.csv")))
docs = {(d["country"], d["company"], d["year"]): d["text_file"] for d in csv.DictReader(open("data/kz_pl_docs_for_governance.csv"))}
for r in rows:
    f = docs.get((r["country"], r["company"], r["year"]), "")
    r["n_digital_expert_narrow"] = "NA" if r["n_digital_expert_verified"] in ("NA", "") else cnt.get(f, 0)
with open("data/panel_kz_pl_ai_gov.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
