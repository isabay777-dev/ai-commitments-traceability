"""Merge verified board digital expertise into governance table and AI panel (KZ, PL)."""
import csv, glob, collections, re, statistics as st

ver = collections.defaultdict(int)
for f in glob.glob("data/gov_verify/rows_*.csv"):
    for l in open(f):
        p = l.rstrip("\n").split(";")
        if len(p) >= 3 and p[2].strip() == "yes":
            ver[p[0]] += 1

gov = list(csv.DictReader(open("data/governance_kz_pl.csv")))
for g in gov:
    if g["bios_available"].strip().lower() == "no":
        g["n_digital_expert_verified"] = "NA"
    else:
        g["n_digital_expert_verified"] = ver.get(g["file"], 0)
with open("data/governance_kz_pl_verified.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(gov[0].keys())); w.writeheader(); w.writerows(gov)

docs = {(d["country"], d["company"], d["year"]): d["text_file"] for d in csv.DictReader(open("data/kz_pl_docs_for_governance.csv"))}
gbyfile = {g["file"]: g for g in gov}
panel = [p for p in csv.DictReader(open("data/panel_ai_disclosure.csv")) if p["country"] in ("KZ", "PL")]
out = []
for p in panel:
    g = gbyfile.get(docs.get((p["country"], p["company"], p["year"]), ""), {})
    p.update({k: g.get(k, "NA") for k in ["board_size", "n_independent", "n_digital_expert_verified",
                                           "has_cdo_cto_cio_exec", "state_owned_major", "foreign_parent", "bios_available"]})
    out.append(p)
with open("data/panel_kz_pl_ai_gov.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

print("panel rows", len(out))
for c in ["KZ", "PL"]:
    r = [x for x in out if x["country"] == c and x["n_digital_expert_verified"] not in ("NA", "")]
    has = [x for x in r if int(x["n_digital_expert_verified"]) > 0]
    no = [x for x in r if int(x["n_digital_expert_verified"]) == 0]
    f = lambda L, k: (sum(int(x["ai_any"]) for x in L) / len(L), st.median(float(x["ai_per_100k_chars"]) for x in L)) if L else (0, 0)
    a1, m1 = f(has, 0); a0, m0 = f(no, 0)
    print(f"{c}: with bios n={len(r)} | digital expert on board: n={len(has)} AI share={a1:.2f} median/100k={m1:.2f} "
          f"| none: n={len(no)} AI share={a0:.2f} median/100k={m0:.2f}")
