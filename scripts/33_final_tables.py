"""Article 1 final tables (CSV) and figure: sample, outcomes by country, by sector, by specificity; AI-mention trend."""
import csv, collections
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = "article1/tables/"
F = list(csv.DictReader(open("data/promise_model_final.csv")))
panel = list(csv.DictReader(open("data/panel_ai_disclosure.csv")))
C = ["KZ", "PL", "NL"]; V = ["fulfilled", "partial", "not_fulfilled", "dropped"]
def w(name, rows):
    with open(OUT + name, "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerows(rows)

# T1 sample
frag = collections.Counter(r["fragment_id"][:2] for r in csv.DictReader(open("data/coding/all_fragments.tsv"), delimiter="\t"))
t1 = [["Country", "Annual reports", "Firms", "Share of reports mentioning AI, 2025 (%)", "AI fragments", "Observable promises", "Firms with promises"]]
for c in C:
    p = [x for x in panel if x["country"] == c]; p25 = [x for x in p if x["year"] == "2025"]
    f = [x for x in F if x["country"] == c]
    t1.append([c, len(p), len({x["company"].lower() for x in p}), round(100 * sum(int(x["ai_any"]) for x in p25) / len(p25)),
               frag[c], len(f), len({x["firm"] for x in f})])
w("T1_sample.csv", t1)

# T2 outcomes by country (row level) + t+1 from analysis A + firm-weighted from B
t2 = [["Country", "n"] + [f"{v} (%)" for v in V] + ["Full, t+1 horizon (%)", "Full, equal firm weights (%)"]]
t1h = {r["country"]: r for r in csv.DictReader(open("article1/analysis_A/country_t1.csv"), delimiter=";") if r["outcome"] == "full"}
fw = {r["country"]: r for r in csv.DictReader(open("article1/analysis_B/tables.csv"), delimiter=";")
      if r["sector"] == "all" and r["level"] == "firm" and r["metric"] == "full"}
for c in C + ["All"]:
    f = F if c == "All" else [x for x in F if x["country"] == c]; n = len(f)
    row = [c, n] + [round(100 * sum(x["verdict_final"] == v for x in f) / n) for v in V]
    row += ([f"{t1h[c]['numerator']}/{t1h[c]['denominator_available']} ({100*float(t1h[c]['rate']):.0f})", f"{float(fw[c]['percent']):.0f}"] if c != "All" else ["", ""])
    t2.append(row)
w("T2_outcomes_by_country.csv", t2)

# T3 sector x country (full, full+partial)
sec = lambda x: "Financial" if x.get("sector_group") == "finance" else "Non-financial"
t3 = [["Country", "Sector", "n", "Full (%)", "Full or partial (%)", "Dropped (%)"]]
B = {(r["country"], r["sector"], r["metric"]): r for r in csv.DictReader(open("article1/analysis_B/tables.csv"), delimiter=";") if r["level"] == "row"}
for c in C:
    for s, key in (("Financial", "finance"), ("Non-financial", "nonfinance")):
        full = B[(c, key, "full")]; fp = B[(c, key, "full_or_partial")]
        t3.append([c, s, full["denominator"], f"{full['numerator']}/{full['denominator']} ({float(full['percent']):.0f})", f"{float(fp['percent']):.0f}", ""])
w("T3_outcomes_by_sector.csv", t3)

# T4 specificity
t4 = [["Specificity", "n"] + [f"{v} (%)" for v in V] + ["Measurable target stated"]]
spec_rows = list(csv.reader(open("article1/history/all.csv"), delimiter=";"))
meas = {r[0]: r[4] for r in spec_rows if len(r) > 4 and r[1] == "SPEC"}
for s in ("1", "2"):
    f = [x for x in F if x["specificity"] == s]; n = len(f)
    t4.append([{"1": "General (1)", "2": "Specific (2)"}[s], n] + [f"{sum(x['verdict_final']==v for x in f)} ({100*sum(x['verdict_final']==v for x in f)/n:.0f})" for v in V]
              + [sum(1 for x in f if meas.get(x["promise_id"]) == "1")])
w("T4_outcomes_by_specificity.csv", t4)

# Figure 1: share of reports mentioning AI, by year and country
fig, ax = plt.subplots(figsize=(6.5, 3.8))
for c, ls in zip(C, ["-", "--", ":"]):
    ys = sorted({x["year"] for x in panel if x["country"] == c})
    sh = [100 * sum(int(x["ai_any"]) for x in panel if x["country"] == c and x["year"] == y) / sum(1 for x in panel if x["country"] == c and x["year"] == y) for y in ys]
    ax.plot([int(y) for y in ys], sh, ls, marker="o", color="black", label={"KZ": "Kazakhstan", "PL": "Poland", "NL": "Netherlands"}[c])
ax.set_ylabel("Reports mentioning AI (%)"); ax.set_xticks(range(2021, 2026)); ax.set_ylim(0, 100); ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(OUT + "F1_ai_mentions_trend.png", dpi=300)
for t in ["T1_sample", "T2_outcomes_by_country", "T3_outcomes_by_sector", "T4_outcomes_by_specificity"]:
    print("\n" + t); [print("  " + " | ".join(map(str, r))) for r in csv.reader(open(OUT + t + ".csv"))]
