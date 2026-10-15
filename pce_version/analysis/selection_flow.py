"""Selection flow by country x commitment year. Run: python3 analysis/selection_flow.py  (from PCE_submission root)
Reads repo/ only; writes analysis/out/T_selection_flow.csv and selection_flow_notes.md."""
import re, os, pandas as pd
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repo")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
P = lambda *a: os.path.join(R, *a)
SLUG = lambda s: re.sub(r"\W+", "_", s).strip("_")

# --- report level
pr = pd.read_csv(P("data/coded/report_panel_ai_mentions.csv"))
pr["ge50k"] = (pr.chars >= 50000).astype(int)
# NL texts are stored under the LEI (scripts/04_nl_full.py); map panel name -> LEI via the ESEF filings index
esef = pd.read_csv(P("data/sources/esef_filings.csv"), dtype=str)
esef["yr"] = esef.period_end.str[:4]
nm2lei = esef.groupby(["name", "yr"]).lei.first().to_dict()   # (name, year) -> LEI
def fname(c, n, y):
    if c == "NL": return f"NL_{nm2lei.get((n, str(y)), 'UNMAPPED_' + SLUG(n))}_{y}.txt"
    return f"{c}_{SLUG(n)}_{y}.txt"
pr["fn"] = [fname(c, n, y) for c, n, y in zip(pr.country, pr.company, pr.year)]

# --- fragments
idx = pd.read_csv(P("data/coded/ai_fragments_index.csv"))
H = "fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note".split(";")
rows = {}
for f in ["main_coded.csv", "pilot_coded.csv"]:
    for l in open(P("data/coded", f), encoding="utf-8"):
        p = l.rstrip("\n").split(";")
        if len(p) >= 9: rows.setdefault(p[0], dict(zip(H, p[:9])))
cod = pd.DataFrame(rows.values())

# --- keys, exactly as scripts/21_follow_through.py (category rules and firm normalisation taken from that file)
src = open(P("scripts/21_follow_through.py"), encoding="utf-8").read()
ns = {}; exec("import re\n" + src[src.index("CATS = ["):src.index("rows = []")], ns)
firm_of, cat = ns["firm_of"], ns["cat"]
q = cod[(cod.is_ai == "1") & (cod.promise == "yes") & cod.status.isin(["PLAN", "PILOT"])].copy()
t = q.fragment_id.map(firm_of)
q["country"], q["firm"], q["year"] = [x[0] for x in t], [x[1] for x in t], [x[2] for x in t]
q["category"] = q.use_case.map(cat)
keys = q.drop_duplicates(["country", "firm", "category", "year"]).copy()   # first processed fragment kept (setdefault)

BAD = {"KZ_Air_Astana_2025.txt", "KZ_Национальная_компания_Қазақстан_темір_жолы_2025.txt", "KZ_МФО_Арнур_Кредит_2024.txt", "KZ_КазАгроФинанс_2021.txt"}
elig = pr[(pr.ge50k == 1) & ~pr.fn.isin(BAD)]
fy = {}
for fn in elig.fn:
    c, f, y = firm_of(fn[:-4] + "#0"); fy.setdefault((c, f), set()).add(y)
keys["n_later_rec"] = [sum(1 for y2 in fy.get((c, f), ()) if y2 > y) for c, f, y in zip(keys.country, keys.firm, keys.year)]
keys["later"] = (keys.n_later_rec > 0).astype(int)

# --- record-level files
f3 = pd.read_csv(P("data/coded/commitments_F3.csv")); f4 = pd.read_csv(P("data/coded/commitments_F4.csv"))
fin = pd.read_csv(P("data/coded/commitments_final.csv"))
uni = pd.read_csv(P("data/coded/unified_recoding.csv"), sep=";", header=None)
uni["promise_id"] = uni[0]
f5 = pd.read_csv(P("data/promise_model_F5.csv"))
assert set(fin.promise_id) == set(f5.promise_id)
# the 190 records: promise_id -> key via F3 file + dropped records
alt = pd.read_csv(P("data/alt_fragments_F5.csv"), dtype=str)
KC = ["country", "firm", "category", "year"]
keys["year"] = keys.year.astype(int)
def mark(df, name):
    d = df[["country", "firm", "category", "year"]].copy(); d["year"] = d.year.astype(int); d[name] = 1
    return keys.merge(d.drop_duplicates(), on=KC, how="left")[name].fillna(0).astype(int).values
keys["f3"] = mark(f3, "f3"); keys["f4"] = mark(f4, "f4"); keys["final"] = mark(fin, "final")


# --- ID mapping: promise_id = rank of the observable key in (country, firm, category, year) order (scripts/22)
k = keys[keys.later == 1].sort_values(["country", "firm", "category", "year"]).reset_index(drop=True)
k["pid"] = [f"P{i:04d}" for i in range(len(k))]
chk = f3.merge(k, left_on="promise_id", right_on="pid", suffixes=("", "_k"))
assert len(chk) == 184 and ((chk.country == chk.country_k) & (chk.firm == chk.firm_k) & (chk.year == chk.year_k) & (chk.category == chk.category_k)).all()
assert set(uni.promise_id) <= set(k.pid) and len(uni) == 190
k["initial190"] = k.pid.isin(set(uni.promise_id)).astype(int)
k["f3"] = k.pid.isin(set(f3.promise_id)).astype(int)
k["final"] = k.pid.isin(set(fin.promise_id)).astype(int)
k["dropped_213_190"] = 1 - k.initial190
k["excluded_nonpromise_190_184"] = k.initial190 - k.f3
k["excluded_nonpromise_184_183"] = k.f3 - k.final
k["year"] = k.year.astype(int)
keys["year"] = keys.year.astype(int)

# --- assemble
pr["year"] = pr.year.astype(int); idx["year"] = idx.year.astype(int)
cod["country"] = cod.fragment_id.str[:2]; cod["year"] = cod.fragment_id.str.extract(r"_(\d{4})#")[0].astype(int)
q["year"] = q.year.astype(int)
def cnt(df, name, filt=None):
    d = df if filt is None else df[filt]
    return d.groupby(["country", "year"]).size().rename(name)
cols = [
 pr.groupby(["country", "year"]).size().rename("reports"),
 cnt(pr, "reports_ge50k_text_extracted", pr.ge50k == 1),
 cnt(pr, "reports_ai_any", pr.ai_any == 1),
 cnt(idx, "fragments_retrieved"),
 cnt(cod, "fragments_coded"),
 cnt(q, "fragments_commitment_PLAN_PILOT"),
 cnt(keys, "keys_firm_category_year"),
 cnt(k, "keys_with_later_report"),
 cnt(k, "records_initial_comparison", k.initial190 == 1),
 cnt(k, "records_F3", k.f3 == 1),
 cnt(k, "records_final_F4_F5", k.final == 1),
 cnt(k, "keys_dropped_213_to_190", k.dropped_213_190 == 1),
 cnt(k, "excluded_nonpromise_190_to_184", k.excluded_nonpromise_190_184 == 1),
 cnt(k, "excluded_nonpromise_184_to_183", k.excluded_nonpromise_184_183 == 1),
]
T = pd.concat(cols, axis=1).fillna(0).astype(int).reset_index().sort_values(["country", "year"])
num = [c for c in T.columns if c not in ("country", "year")]
sub = T.groupby("country")[num].sum().reset_index(); sub["year"] = "all"
tot = T[num].sum().to_frame().T; tot["country"] = "ALL"; tot["year"] = "all"
T["year"] = T.year.astype(str)
out = pd.concat([T, sub, tot], ignore_index=True)[["country", "year"] + num]
out.to_csv(os.path.join(OUT, "T_selection_flow.csv"), index=False)
KNOWN = dict(reports=1098, reports_ge50k_text_extracted=1098, fragments_retrieved=4850, fragments_coded=4672,
             fragments_commitment_PLAN_PILOT=586, keys_firm_category_year=418, keys_with_later_report=213,
             records_initial_comparison=190, records_F3=184, records_final_F4_F5=183)
t = out[out.country == "ALL"].iloc[0]
for kk, v in KNOWN.items(): assert t[kk] == v, (kk, t[kk], v)
yr = out[(out.country != "ALL") & (out.year != "all")]
assert (yr[num].sum().astype(int) == t[num].astype(int)).all()   # year rows sum to the known totals
print(out.to_string(index=False))
print("reports_ai_any total", t.reports_ai_any, "| extra check: promise=yes any status", (cod.promise == "yes").sum())

NOTES = """# Selection flow: notes (generated by analysis/selection_flow.py)

Table: `T_selection_flow.csv`; rows = country x year plus country subtotals ("all") and ALL; year = report year, which is also the commitment year for key-level columns. Year rows sum to the known totals (asserted in the script).

## Reproduced exactly
- Reports 1,098 (KZ 422, PL 135, NL 541) from `report_panel_ai_mentions.csv`; reports with ai_any = 567 (KZ 161, PL 89, NL 317).
- Retrieved fragments 4,850 (`ai_fragments_index.csv`); coded 4,672 = union of `main_coded.csv` + `pilot_coded.csv` (no duplicate IDs). The 178 uncoded fragments are all KZ 2025 (Air Astana 176, Kazakhstan Temir Zholy 2).
- 586 PLAN/PILOT fragments with promise = yes (KZ 157, PL 109, NL 320). Applying the key rule of `scripts/21_follow_through.py` (category regexes, firm normalisation, first fragment kept per country x firm x category x year) gives 418 keys (KZ 99, PL 85, NL 234).
- 213 keys with at least one later report (KZ 33, PL 34, NL 146): same firm, later year, report >= 50,000 characters, excluding the four BAD-list reports of script 21. Firm-years were rebuilt from the report panel (NL texts are named by LEI; mapped via `esef_filings.csv`). The rebuilt later-report count equals `n_later_reports` for all 183 final records.
- Promise IDs are the rank of the 213 keys in (country, firm, category, year) order (script 22). All 184 F3 IDs match their key on country, firm, category, year, so the mapping is exact. All 190 IDs of `unified_recoding.csv` are among the 213.
- 190 -> 184 (F3): six non-promises excluded after two rounds and third adjudication (P0014 KZ 2024, P0026 KZ 2024, P0038 NL 2024, P0081 NL 2023, P0107 NL 2023, P0197 PL 2023; `tables/excluded_nonpromises_F3.csv`).
- 184 -> 183 (F4/F5): one NL 2023 record excluded as not a promise. Final: KZ 27, PL 29, NL 127.

## Unresolved from archived per-key records: why 213 -> 190
The 23 dropped keys are identified exactly by set difference (P0005, P0008, P0021, P0027, P0044, P0061, P0067, P0068, P0072, P0089, P0114, P0135, P0141, P0169, P0170, P0175, P0176, P0177, P0178, P0181, P0187, P0189, P0202; KZ 4, PL 4, NL 15). No file in the package holds their verdicts: the initial verification output (`promises_verified.csv`, `promise_check/promise_verdicts.csv`) is absent from `repo/`. The documented rule: `scripts/23_run_promise_check.sh` allows a `not_a_promise` verdict and `scripts/24_promise_model_data.py` drops `not_a_promise` and empty verdicts; the manuscript says 183 remain "after verification that each candidate is a company undertaking to implement AI". The archived code therefore permits both an explicit non-commitment decision and an empty verdict; neither mechanism can be assigned to an individual missing key without its archived verdict. All 23 reasons remain unresolved, rather than being labelled non-commitments. Duplicates are not a reason: they were collapsed when the 418 keys were built (first fragment per key). `prompts/prompt.txt` and `p_fixer.txt` mention an intermediate 201 (213 -> 201 -> 190); no record explains that step, and 201 also appears as the alternative-fragment sample size in S4, so it is not shown as a stage here.

## Record-level ledger
`analysis/build_selection_ledger.py` writes `selection_ledger_213.csv`, the 23-case unresolved subset, a fragment-link table, country disposition counts and an audit manifest. It preserves historical decisions without re-adjudication: 183 retained, six documented F3 exclusions, one documented F4 exclusion and 23 unresolved pre-coding omissions. See Supplementary S5 Tables S5.11–S5.12.

## Caveats
- Historical script 21 filters text-file size in bytes (>=50,000), whereas this reconstruction uses the report panel character count (>=50,000). These filters are not identical. The reconstructed later-report counts match all 183 final records; this does not independently recover or audit excluded full texts.
- All 1,098 panel reports are >= 50,000 characters (panel built with that filter, `06_build_panel.py`), so reports used for extraction = 1,098; reports under 50k are not in the package. Four reports are on the BAD list and only excluded as later reports.
- The 586 are fragments; 8 further fragments have promise = yes with another status (594 in total).
- Coded fragments include 232 with is_ai = 0.
- 2025 keys cannot have later reports, hence zero.
"""
open(os.path.join(OUT, "selection_flow_notes.md"), "w", encoding="utf-8").write(NOTES)
