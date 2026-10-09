"""After governance extraction: queue named digital experts from new KZ docs for strict verification."""
import re, glob
new = set(open("data/nl_promise_docs.txt").read().split())
items = []
for f in glob.glob("data/gov/rows_*.csv"):
    for l in open(f):
        p = l.rstrip("\n").split(";")
        if len(p) >= 9 and p[0] in new and p[8].strip() not in ("", "NA", "0", "-"):
            for n in re.split(r"\s*[,|/]\s*|\s+and\s+|\s+и\s+", p[8]):
                if len(n.strip()) > 3: items.append(f"{p[0]}\t{n.strip()}")
print("persons to verify", len(items))
for k in range(4):
    open(f"data/gov_verify/batch_{12 + k}.txt", "w").write("\n".join(items[k::4]) + "\n")
