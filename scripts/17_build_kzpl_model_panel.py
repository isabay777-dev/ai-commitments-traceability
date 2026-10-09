"""Build expanded KZ+PL firm-year modelling panel keyed by text file (AI counts + governance + verified experts + controls)."""
import csv, glob, re, math, collections, sys, os
sys.path.insert(0, "scripts"); from textutil import ai_hits
from importlib import import_module
NARROW = import_module("11_narrow_expert").NARROW if False else re.compile(
    r"\b(CIO|CTO|CDO|CISO)\b|chief (information|technology|digital|data|technical)|\bIT director|director of (IT|information technolog|digital)|"
    r"head of (IT|digital|technology)|computer science|informatics|information technolog|software engineer|data scien|cyber|"
    r"директор\w* по (IT|ИТ|информационн|цифров)|информационн\w* технолог|информатик|программ|cyfryzac|informatyk|technologii informacyjnych", re.I)

def rows(pattern, n):
    out = {}
    for f in glob.glob(pattern):
        for l in open(f):
            p = l.rstrip("\n").split(";")
            if len(p) >= n: out[p[0]] = p
    return out
GH = "file;board_structure;board_name;board_size;n_independent;n_women_board;n_foreign_board;n_digital_expert_board;digital_expert_names;bios_available;has_cdo_cto_cio_exec;state_owned_major;largest_shareholder;largest_shareholder_pct;foreign_parent;ai_or_digital_committee".split(";")
gov = rows("data/gov/rows_*.csv", 16)
ctl = rows("data/controls/rows_*.csv", 11)
ver, nar = collections.Counter(), collections.Counter()
for f in glob.glob("data/gov_verify/rows_*.csv"):
    for l in open(f):
        p = l.rstrip("\n").split(";")
        if len(p) >= 5 and p[2].strip() == "yes":
            ver[p[0]] += 1; nar[p[0]] += bool(NARROW.search(p[4]))
mult = {"thousand": 1e3, "million": 1e6, "full": 1, "billion": 1e9}
def num(v):
    try: return float(v)
    except: return None
def grp(s):
    s = s.lower()
    if s in ("na", ""): return "NA"
    if re.search(r"bank|insur|financ|leasing|broker|invest|microfin|credit", s): return "finance"
    if re.search(r"oil|gas|mining|utilit|energy|power|coal|metal|uranium", s): return "resources_energy"
    if re.search(r"telecom|\bit\b|software|tech|media|internet|e-commerce|gaming", s): return "tech_telecom"
    return "other"
out = []
for fn, g in gov.items():
    m = re.match(r"(KZ|PL)_(.+)_(\d{4})\.txt$", fn)
    if not m or not os.path.exists("data/text/" + fn): continue
    t = open("data/text/" + fn).read()
    if len(t) < 50000: continue
    G = dict(zip(GH, g[:16])); c = ctl.get(fn, [])
    a = num(c[3]) if c else None; mu = mult.get(c[2].strip().lower()) if c else None
    bios = G["bios_available"].strip().lower()
    out.append(dict(file=fn, country=m.group(1), firm=m.group(2), year=int(m.group(3)), chars=len(t),
                    ai_sentences=len(ai_hits(t)), board_size=G["board_size"], n_independent=G["n_independent"],
                    bios=bios, dig=("NA" if bios == "no" else ver[fn]), dig_narrow=("NA" if bios == "no" else nar[fn]),
                    cdo_exec=G["has_cdo_cto_cio_exec"], state=G["state_owned_major"], foreign_parent=G["foreign_parent"],
                    total_assets_raw=(a * mu if a and mu else ""), currency=(c[1] if c else ""),
                    sector_label=(c[9] if c else "NA"), sector_group=grp(c[9] if c else "NA")))
# dedupe same firm-year reported under two names (identical assets & year & country)
seen, ded = {}, []
for r in sorted(out, key=lambda r: -r["chars"]):
    k = (r["country"], r["year"], r["total_assets_raw"]) if r["total_assets_raw"] else (r["file"],)
    if k in seen: continue
    seen[k] = 1; ded.append(r)
for r in ded:
    r["ai_any"] = int(r["ai_sentences"] > 0)
    r["log_assets"] = round(math.log(r["total_assets_raw"]), 4) if r["total_assets_raw"] else ""
with open("data/panel_kzpl_expanded.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ded[0].keys())); w.writeheader(); w.writerows(ded)
print("rows", len(out), "after dedupe", len(ded))
for c in ("KZ", "PL"):
    r = [x for x in ded if x["country"] == c]
    print(c, "firm-years", len(r), "firms", len({x["firm"] for x in r}),
          "with bios", sum(1 for x in r if x["dig"] != "NA"), "assets", sum(1 for x in r if x["log_assets"] != ""))
