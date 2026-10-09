"""Extract AI fragments (hit sentence +/- context window) from all report texts; write pilot sample."""
import os, re, sys, csv, random, glob, collections
sys.path.insert(0, "scripts"); from textutil import AI_RE
W = 350  # chars of context on each side
rows = []
for f in sorted(glob.glob("data/text/*.txt")):
    t = open(f).read()
    if len(t) < 50000: continue
    flat = re.sub(r"\s+", " ", t)
    m = re.match(r"(KZ|PL|NL)_(.+)_(\d{4})\.txt$", os.path.basename(f))
    if not m: continue
    last_end = -1; k = 0
    for h in AI_RE.finditer(flat):
        if h.start() < last_end: continue          # merge overlapping hits into one fragment
        a, b = max(0, h.start() - W), min(len(flat), h.end() + W)
        last_end = b; k += 1
        rows.append(dict(fragment_id=f"{os.path.basename(f)[:-4]}#{k}", file=os.path.basename(f),
                         country=m.group(1), year=m.group(3), text=flat[a:b].replace("\t", " ")))
with open("data/coding/all_fragments.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter="\t"); w.writeheader(); w.writerows(rows)
print("fragments", len(rows), dict(collections.Counter(r["country"] for r in rows)))
random.seed(42)
quota = {"KZ": 40, "PL": 30, "NL": 30}
pilot = []
for c, q in quota.items():
    pool = [r for r in rows if r["country"] == c]
    byyear = collections.defaultdict(list)
    for r in pool: byyear[r["year"]].append(r)
    ys = sorted(byyear)
    for i in range(q):
        y = ys[i % len(ys)]
        if byyear[y]: pilot.append(byyear[y].pop(random.randrange(len(byyear[y]))))
with open("data/coding/pilot_fragments.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter="\t"); w.writeheader(); w.writerows(pilot)
print("pilot", len(pilot))
