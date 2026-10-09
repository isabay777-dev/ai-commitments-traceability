"""Prepare governance/controls batches for new KZ expansion docs (not yet processed)."""
import csv, os, re, glob
done = {x["text_file"] for x in csv.DictReader(open("data/kz_pl_docs_for_governance.csv"))}
new = []
for x in csv.DictReader(open("data/kz_expansion_counts.csv")):
    slug = re.sub(r"\W+", "_", x["company"]).strip("_")
    fn = "KZ_" + slug + "_" + x["year"] + ".txt"
    if int(x["chars"]) > 50000 and fn not in done and os.path.exists("data/text/" + fn):
        new.append(fn)
new = sorted(set(new))
print("new docs", len(new))
# governance snippets (same rules as before)
BOARD = re.compile(r'board of directors|supervisory board|совет\w* директоров|независим\w* директор|independent (?:director|member)|management board|правлени\w*|shareholder|акционер|chief (?:digital|technology|information|data) officer|CDO|CTO|CIO', re.I)
BIO = re.compile(r'experience|education|graduated|опыт|образован|окончил|born in|родил', re.I)
for f in new:
    paras = open("data/text/" + f).read().split("\n")
    keep = []
    for i, p in enumerate(paras):
        if BOARD.search(p):
            win = " ".join(paras[max(0, i - 2):i + 6]); keep.append((2 if BIO.search(win) else 1, i, win))
    keep.sort(key=lambda z: (-z[0], z[1])); out = []; seen = set(); size = 0
    for sc, i, w in keep:
        if i // 4 in seen: continue
        seen.add(i // 4); out.append((i, w)); size += len(w)
        if size > 30000: break
    out.sort()
    open("data/gov_snippets/" + f, "w").write("\n---\n".join(re.sub(r"\s+", " ", w) for i, w in out))
for k in range(8):
    open(f"data/gov/batch_{8 + k}.txt", "w").write("\n".join(new[k::8]) + "\n")
    open(f"data/controls/batch_{6 + k}.txt", "w").write("\n".join(new[k::8]) + "\n")
open("data/kz_expansion_docs.txt", "w").write("\n".join(new) + "\n")
