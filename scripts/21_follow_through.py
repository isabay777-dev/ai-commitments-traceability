"""Article 1: track AI promises (PLAN/PILOT) to later LIVE disclosures of the same firm and use-case category.
Usage: python3 scripts/21_follow_through.py data/coding/pilot_coded.csv [data/coding/main_coded.csv ...]"""
import csv, re, sys, collections

H = "fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note".split(";")
CATS = [  # controlled use-case categories (order matters: first match wins)
    ("fraud_security", r"fraud|aml|anti-money|cyber|security|threat|антифрод|мошенн|безопасн"),
    ("credit_risk", r"credit|scoring|underwrit|risk model|loan|скоринг|кредит"),
    ("customer_service", r"chat ?bot|virtual assistant|assistant|call cent|contact cent|customer service|voice bot|чат-?бот|ассистент|колл"),
    ("personalisation_marketing", r"personali|recommend|marketing|pricing|search|customer experience|персонал|рекоменд|маркет"),
    ("process_automation", r"automat|document|process|rpa|back.?office|ocr|workflow|автомат|документ|процесс"),
    ("maintenance_operations", r"maintenan|predictive|equipment|asset|grid|network operat|production|monitor|vision|safety|обслужив|оборудов|мониторинг|произв"),
    ("forecasting_analytics", r"forecast|demand|planning|analytic|prediction|data|прогноз|аналит|данн"),
    ("hr_people", r"\bhr\b|recruit|talent|employee|training|skills|персонал|обучен|компетенц"),
    ("software_dev", r"\bcode\b|coding|software develop|copilot|программирован"),
    ("health_product", r"diagnos|medical|health|clinical|медиц|диагност"),
    ("general_ai", r"general|strategy|ai platform|generative|genai|llm|ai adoption|ai solutions|ии|ai"),
]
def cat(uc):
    u = uc.lower()
    for name, rx in CATS:
        if re.search(rx, u): return name
    return "other"

ALIAS = {"Банк ЦентрКредит": "Bank CenterCredit", "КазМунайГаз": "KazMunayGas", "КазАзот": "KazAzot", "КазТрансОйл": "KazTransOil", "Казатомпром": "Kazatomprom", "Казахтелеком": "Kazakhtelecom"}
def firm_of(fid):
    m = re.match(r"(KZ|PL|NL)_(.+)_(\d{4})#\d+$", fid)
    c, name, y = m.group(1), m.group(2), int(m.group(3))
    name = ALIAS.get(name.replace("_", " "), name)
    return c, re.sub(r"\W+", "_", name).strip("_").lower(), y

rows = []
for fn in sys.argv[1:]:
    for l in open(fn):
        p = l.rstrip("\n").split(";")
        if len(p) < 9 or p[1].strip() != "1": continue
        r = dict(zip(H, p[:9])); r["country"], r["firm"], r["year"] = firm_of(r["fragment_id"]); r["cat"] = cat(r["use_case"])
        rows.append(r)

firm_years = collections.defaultdict(set)      # all usable reports of the firm, with or without AI text
import os, glob
BAD = {"KZ_Air_Astana_2025.txt", "KZ_Национальная_компания_Қазақстан_темір_жолы_2025.txt", "KZ_МФО_Арнур_Кредит_2024.txt", "KZ_КазАгроФинанс_2021.txt"}
for f in glob.glob("data/text/*.txt"):
    b = os.path.basename(f)
    if b in BAD or os.path.getsize(f) < 50000: continue
    c, fi, y = firm_of(b[:-4] + "#0"); firm_years[(c, fi)].add(y)
live = collections.defaultdict(set)            # (country, firm, cat) -> years with LIVE
for r in rows:
    if r["status"] == "LIVE": live[(r["country"], r["firm"], r["cat"])].add(r["year"])

promises = {}
for r in rows:
    if r["promise"] == "yes" and r["status"] in ("PLAN", "PILOT"):
        k = (r["country"], r["firm"], r["cat"], r["year"])
        promises.setdefault(k, r)                # one promise per firm x category x year
out = []
for (c, f, ca, y), r in sorted(promises.items()):
    later_reports = sorted(t for t in firm_years[(c, f)] if t > y)
    done = sorted(t for t in live[(c, f, ca)] if t > y)
    same_year_live = y in live[(c, f, ca)]
    status = ("fulfilled" if done else "not_observed_yet" if not later_reports else "not_fulfilled")
    out.append(dict(country=c, firm=f, year=y, category=ca, use_case=r["use_case"], promise_status=r["status"],
                    specificity=r["specificity"], n_later_reports=len(later_reports),
                    fulfilled=int(bool(done)), first_live_year=(done[0] if done else ""),
                    years_to_live=(done[0] - y if done else ""), live_same_year=int(same_year_live), outcome=status,
                    fragment_id=r["fragment_id"]))
if out:
    with open("data/coding/promises_follow_through.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
print("coded AI fragments", len(rows), "| promises (firm x category x year)", len(out))
for c in ("KZ", "PL", "NL"):
    o = [x for x in out if x["country"] == c]
    obs = [x for x in o if x["outcome"] != "not_observed_yet"]
    if o: print(f"{c}: promises {len(o)}, observable {len(obs)}, fulfilled {sum(x['fulfilled'] for x in obs)}"
                f" ({(sum(x['fulfilled'] for x in obs)/len(obs)*100 if obs else 0):.0f}%)")
print(dict(collections.Counter(x["category"] for x in out)))
