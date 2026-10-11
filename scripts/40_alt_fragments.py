"""Robustness (review A3): list ALL eligible promise fragments per firm x category x year key of the F3 sample,
not only the first processed one. Writes article1/altfrag/alt_fragments.csv and one packet per alternative fragment.
Usage: python3 scripts/40_alt_fragments.py"""
import csv, re, os, glob, collections
src = open("scripts/21_follow_through.py").read().split("rows = []")[0]   # reuse CATS, cat(), firm_of(), H
ns = {}; exec(src, ns)
rows = []
for fn in ("data/coding/pilot_coded.csv", "data/coding/main_coded.csv"):
    for l in open(fn):
        p = l.rstrip("\n").split(";")
        if len(p) < 9 or p[1].strip() != "1": continue
        r = dict(zip(ns["H"], p[:9])); r["country"], r["firm"], r["year"] = ns["firm_of"](r["fragment_id"]); r["cat"] = ns["cat"](r["use_case"])
        if r["promise"] == "yes" and r["status"] in ("PLAN", "PILOT"): rows.append(r)
keys = collections.defaultdict(list)
for r in rows: keys[(r["country"], r["firm"], r["cat"], r["year"])].append(r)
pid_frag = {}
for f in glob.glob("data/promise_check/packets/P*.txt"):
    m = re.search(r"=== PROMISE FRAGMENT \((.+?)\) ===", open(f).read())
    if m: pid_frag[m.group(1)] = os.path.basename(f)[:-4]
f3 = {r["promise_id"]: r for r in csv.DictReader(open("data/promise_model_F3.csv"))}
text = {}
for l in open("data/coding/all_fragments.tsv"):
    p = l.rstrip("\n").split("\t")
    if len(p) >= 5: text[p[0]] = p[4]
os.makedirs("article1/altfrag/packets", exist_ok=True)
out = []; n_multi = 0; n_mixed = 0
for k, rs in sorted(keys.items()):
    retained = rs[0]; pid = pid_frag.get(retained["fragment_id"])
    if pid not in f3: continue
    if len(rs) > 1: n_multi += 1
    if len({r["specificity"] for r in rs}) > 1: n_mixed += 1
    for j, r in enumerate(rs):
        aid = pid if j == 0 else f"{pid}_alt{j}"
        out.append(dict(alt_id=aid, promise_id=pid, retained=int(j == 0), country=k[0], firm=k[1], category=k[2], year=k[3],
                        fragment_id=r["fragment_id"], specificity=r["specificity"], status=r["status"], use_case=r["use_case"]))
        if j:
            open(f"article1/altfrag/packets/{aid}.txt", "w").write(
                f"ALT_ID: {aid}\nRETAINED PROMISE: {pid} (packet data/promise_check/packets/{pid}.txt)\nCOMPANY FILE PREFIX: {r['fragment_id'].split('#')[0].rsplit('_',1)[0]}\nPROMISE_YEAR: {k[3]}\nUSE_CASE_LABEL: {r['use_case']}\n\n=== ALTERNATIVE PROMISE FRAGMENT ({r['fragment_id']}) ===\n{text.get(r['fragment_id'],'NA')}\n")
with open("article1/altfrag/alt_fragments.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
alts = [o["alt_id"] for o in out if not o["retained"]]
open("article1/altfrag/ids.txt", "w").write("\n".join(alts) + "\n")
print("F3 keys matched", len({o['promise_id'] for o in out}), "| multi-fragment keys", n_multi, "| mixed specificity", n_mixed, "| alternative fragments", len(alts))
