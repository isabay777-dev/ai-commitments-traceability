"""Promise-level modelling data: verified promise outcomes + firm characteristics at promise year (KZ/PL from panel_kzpl_expanded)."""
import csv, re
ALIAS = {"Банк ЦентрКредит": "Bank CenterCredit", "КазМунайГаз": "KazMunayGas", "КазАзот": "KazAzot",
         "КазТрансОйл": "KazTransOil", "Казатомпром": "Kazatomprom", "Казахтелеком": "Kazakhtelecom"}
norm = lambda s: re.sub(r"\W+", "_", ALIAS.get(s.replace("_", " "), s)).strip("_").lower()
firm = {}
for r in csv.DictReader(open("data/panel_kzpl_expanded.csv")):
    firm[(r["country"], norm(r["firm"]), r["year"])] = r
out = []
for p in csv.DictReader(open("data/promises_verified.csv")):
    if p["verdict"] in ("", "not_a_promise"): continue
    f = firm.get((p["country"], p["firm"], p["year"]), {})
    out.append(dict(promise_id=p["promise_id"], country=p["country"], firm=p["firm"], year=p["year"],
                    category=p["category"], promise_status=p["promise_status"], specificity=p["specificity"],
                    n_later_reports=p["n_later_reports"], verdict=p["verdict"],
                    fulfilled=int(p["verdict"] == "fulfilled"), fulfilled_or_partial=int(p["verdict"] in ("fulfilled", "partial")),
                    dropped=int(p["verdict"] == "dropped"),
                    dig=f.get("dig", ""), dig_narrow=f.get("dig_narrow", ""), state=f.get("state", ""),
                    log_assets=f.get("log_assets", ""), sector_group=f.get("sector_group", ""),
                    board_size=f.get("board_size", ""), n_independent=f.get("n_independent", "")))
with open("data/promise_model.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
print("promises", len(out), "| KZ/PL with firm data", sum(1 for x in out if x["log_assets"]))
