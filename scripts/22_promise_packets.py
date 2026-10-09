"""Build one text packet per observable promise: the promise fragment + all later AI fragments of the same firm."""
import csv, re, os, collections, sys
sys.path.insert(0, "scripts")
H = "fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note".split(";")
codes = {}
for f in ["data/coding/main_coded.csv", "data/coding/pilot_coded.csv"]:
    for l in open(f):
        p = l.rstrip("\n").split(";")
        if len(p) == 9: codes.setdefault(p[0], dict(zip(H, p)))
text = {r["fragment_id"]: r["text"] for r in csv.DictReader(open("data/coding/all_fragments.tsv"), delimiter="\t")}
ft = __import__("21_follow_through") if False else None
ALIAS = {"Банк ЦентрКредит": "Bank CenterCredit", "КазМунайГаз": "KazMunayGas", "КазАзот": "KazAzot",
         "КазТрансОйл": "KazTransOil", "Казатомпром": "Kazatomprom", "Казахтелеком": "Kazakhtelecom"}
def firm_of(fid):
    m = re.match(r"(KZ|PL|NL)_(.+)_(\d{4})#\d+$", fid)
    name = ALIAS.get(m.group(2).replace("_", " "), m.group(2))
    return m.group(1), re.sub(r"\W+", "_", name).strip("_").lower(), int(m.group(3))
byfirm = collections.defaultdict(list)
for fid, c in codes.items():
    if c["is_ai"] == "1": byfirm[firm_of(fid)[:2]].append((firm_of(fid)[2], fid))
prom = [r for r in csv.DictReader(open("data/coding/promises_follow_through.csv")) if r["outcome"] != "not_observed_yet"]
ids = []
for i, p in enumerate(prom):
    pid = f"P{i:04d}"; ids.append(pid)
    later = sorted((y, f) for y, f in byfirm[(p["country"], p["firm"])] if y > int(p["year"]))
    with open(f"data/promise_check/packets/{pid}.txt", "w") as fh:
        fh.write(f"PROMISE_ID: {pid}\nCOMPANY: {p['country']} {p['firm']}\nPROMISE_YEAR: {p['year']}\n"
                 f"LATER_REPORT_YEARS: {p['n_later_reports']} later reports exist\nUSE_CASE_LABEL: {p['use_case']} ({p['category']})\n\n"
                 f"=== PROMISE FRAGMENT ({p['fragment_id']}) ===\n{text.get(p['fragment_id'], '')}\n\n=== LATER AI FRAGMENTS OF THE SAME COMPANY ===\n")
        for y, f in later:
            c = codes[f]
            fh.write(f"\n--- {y} | {f} | status={c['status']} use_case={c['use_case']}\n{text.get(f, '')}\n")
        if not later: fh.write("(no AI fragments in later reports)\n")
for b in range(6):
    open(f"data/promise_check/batch_{b}.txt", "w").write("\n".join(ids[b::6]) + "\n")
print("packets", len(ids))
