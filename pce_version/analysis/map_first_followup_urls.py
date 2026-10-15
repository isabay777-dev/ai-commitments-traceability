"""Map the first-follow-up worklist to URLs in the local replication sources.

Run from any directory with: python3 analysis/map_first_followup_urls.py
This script reads no outcome labels, hidden validation key, or remote resources.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "repo/data/sources"
OUT = ROOT / "analysis/out"
WORKLIST = OUT / "first_followup_worklist_183.csv"
FRAGMENTS = ROOT / "repo/data/coded/ai_fragments_index.csv"
URL_FILES = (
    "kz_report_urls_full.txt",
    "pl_report_urls_full.txt",
    "pl_kz_report_urls_raw.txt",
    "kz_expansion_urls.csv",
)
OK = {"FOUND", "FOUND_INDEXED", "VERIFIED", "VERIFIED_LINK", "PARTIAL", "CHECKED"}
COUNTRY = {"KZ": {"KZ", "KAZAKHSTAN"}, "PL": {"PL", "POLAND"}}
# The sources list both Kazatomprom and Казатомпром for adjacent years.
# No general transliteration or fuzzy company matching is used.
ALIASES = {"KZ": {"kazatomprom": {"казатомпром"}}}


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def norm(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.lower())


def report_parts(filename: str) -> tuple[str, str, str]:
    match = re.fullmatch(r"(KZ|PL|NL)_(.+)_(\d{4})\.txt", filename)
    if not match:
        raise ValueError(f"Unexpected report filename: {filename}")
    return match.groups()


def valid_url(url: str) -> bool:
    return url.startswith(("http://", "https://")) and not re.search(
        r"\.pdf\.pdf(?:[?#]|$)", url, flags=re.I
    )


def translation_key(url: str) -> str:
    """Compare obvious language variants, without treating them as one URL."""
    return re.sub(r"(?i)(?<![a-z])(eng|english|en|rus|russian|ru|pol|polish|pl)(?![a-z])", "LANG", url)


def main() -> None:
    work = read_csv(WORKLIST)
    if len(work) != 183 or len({row["promise_id"] for row in work}) != len(work):
        raise ValueError("Unexpected worklist size or duplicate promise ID")

    fragment_files = defaultdict(set)
    for row in read_csv(FRAGMENTS):
        fragment_files[row["fragment_id"]].add(row["file"])

    url_rows = []
    for source in URL_FILES:
        for lineno, row in enumerate(read_csv(SOURCES / source, ";"), start=2):
            url_rows.append({**row, "source_file": source, "source_line": lineno})
    esef = read_csv(SOURCES / "esef_filings.csv")
    esef_by_key = defaultdict(list)
    for row in esef:
        if row["country"] == "NL":
            esef_by_key[(row["lei"].lower(), row["period_end"][:4])].append(row)

    def map_document(filename: str) -> dict:
        country, stem, year = report_parts(filename)
        flags = []
        if country == "NL":
            candidates = esef_by_key[(stem.lower(), year)]
            usable = [r for r in candidates if r["report_url"].startswith("/")]
            options = sorted({r["report_url"] for r in usable})
            chosen = ""
            method = "missing"
            if len(options) == 1:
                chosen = options[0]
                method = "lei_year_exact"
            elif len(options) > 1:
                flags.append("multiple_esef_revisions")
                # ESEF /0/, /1/, ... denote revisions of one annual filing.
                # Select the highest revision only if the remainder is identical.
                parsed = [re.fullmatch(r"(.*?/ESEF/NL/)(\d+)(/.*)", u) for u in options]
                if all(parsed) and len({(m[1], m[3]) for m in parsed}) == 1:
                    chosen = max(zip(parsed, options), key=lambda pair: int(pair[0][2]))[1]
                    method = "lei_year_latest_esef_revision"
                else:
                    flags.append("unresolved_distinct_esef_filings")
            else:
                flags.append("no_source_url")
            selected = next((r for r in usable if r["report_url"] == chosen), None)
            return {
                "country": country, "year": year, "report_file": filename,
                "url": "https://filings.xbrl.org" + chosen if chosen else "",
                "source_company": selected["name"] if selected else "",
                "match_method": method, "ambiguity_flags": flags,
                "candidate_classification": (
                    "duplicate_revision" if "multiple_esef_revisions" in flags
                    else "single" if chosen else "missing"
                ),
                "candidates": [
                    {"company": r["name"], "url": "https://filings.xbrl.org" + r["report_url"],
                     "fxo_id": r["fxo_id"], "error_count": r["error_count"]}
                    for r in candidates
                ],
            }

        exact = norm(stem)
        aliases = ALIASES.get(country, {}).get(exact, set())
        candidates = [
            r for r in url_rows
            if r["country"].upper() in COUNTRY[country] and r["year"] == year
            and norm(r["company"]) in {exact, *aliases}
        ]
        eligible = [r for r in candidates if r["status"] in OK and valid_url(r["url"])]
        options = sorted({r["url"] for r in eligible})
        if aliases and any(norm(r["company"]) in aliases for r in eligible):
            flags.append("documented_company_alias")
        if any(r["status"] in OK and r["url"].lower().endswith(".pdf.pdf") for r in candidates):
            flags.append("malformed_duplicate_pdf_extension_excluded")
        if len(options) > 1:
            flags.append("multiple_eligible_urls_unresolved")
        elif not options:
            flags.append("no_source_url")
        chosen = options[0] if len(options) == 1 else ""
        selected = next((r for r in eligible if r["url"] == chosen), None)
        method = ("company_alias_year_exact" if norm(selected["company"]) != exact
                  else "file_stem_company_year_exact") if selected else "missing"
        if len(options) > 1:
            classification = ("duplicate_translation" if len({translation_key(u) for u in options}) == 1
                              else "conflict")
        elif "malformed_duplicate_pdf_extension_excluded" in flags:
            classification = "malformed_duplicate"
        else:
            classification = "single" if chosen else "missing"
        return {
            "country": country, "year": year, "report_file": filename,
            "url": chosen, "source_company": selected["company"] if selected else "",
            "match_method": method, "ambiguity_flags": flags,
            "candidate_classification": classification,
            "candidates": [
                {"company": r["company"], "url": r["url"], "status": r["status"],
                 "source_file": r["source_file"], "source_line": r["source_line"]}
                for r in candidates
            ],
        }

    filenames = set()
    original_by_id = {}
    for row in work:
        files = fragment_files[row["retained_fragment_id"]]
        if len(files) != 1:
            raise ValueError(f"Fragment has {len(files)} report files: {row['retained_fragment_id']}")
        original = next(iter(files))
        co, _, year = report_parts(original)
        if (co, year) != (row["country"], row["commitment_year"]):
            raise ValueError(f"Fragment report mismatch: {row['promise_id']}")
        follow = row["first_available_report_file"]
        fco, _, fyear = report_parts(follow)
        if (fco, fyear) != (row["country"], row["first_available_report_year"]):
            raise ValueError(f"Follow-up report mismatch: {row['promise_id']}")
        original_by_id[row["promise_id"]] = original
        filenames.update((original, follow))

    documents = {name: map_document(name) for name in sorted(filenames)}
    output = []
    for row in work:
        original = documents[original_by_id[row["promise_id"]]]
        follow = documents[row["first_available_report_file"]]
        output.append({
            "promise_id": row["promise_id"], "country": row["country"],
            "company": row["firm"], "commitment_year": row["commitment_year"],
            "original_report_file": original["report_file"],
            "original_commitment_report_url": original["url"],
            "original_match_method": original["match_method"],
            "original_ambiguity_flags": "|".join(original["ambiguity_flags"]),
            "original_candidate_classification": original["candidate_classification"],
            "first_available_report_year": row["first_available_report_year"],
            "first_available_report_file": follow["report_file"],
            "first_available_followup_url": follow["url"],
            "followup_match_method": follow["match_method"],
            "followup_ambiguity_flags": "|".join(follow["ambiguity_flags"]),
            "followup_candidate_classification": follow["candidate_classification"],
            "source_url_candidates_json": json.dumps({
                "original": original["candidates"], "followup": follow["candidates"]
            }, ensure_ascii=False, separators=(",", ":")),
        })

    target = OUT / "first_followup_source_urls.csv"
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    follow_files = {r["first_available_report_file"] for r in work}
    original_files = set(original_by_id.values())
    audit = {
        "inputs": [str(WORKLIST.relative_to(ROOT)), str(FRAGMENTS.relative_to(ROOT))]
                  + [str((SOURCES / n).relative_to(ROOT)) for n in URL_FILES]
                  + [str((SOURCES / "esef_filings.csv").relative_to(ROOT))],
        "rules": ["Exact LEI and report year for NL.",
                  "Exact normalized report-file stem, source company and year for KZ/PL; only the explicit Kazatomprom alias is allowed.",
                  "Use statuses in validation/build_kit.py OK set; reject non-HTTP and duplicate .pdf.pdf URLs.",
                  "For otherwise identical NL ESEF filings, choose highest numeric revision; leave other URL conflicts missing."],
        "summary": {
            "cases": len(work),
            "unique_original_reports": len(original_files),
            "original_reports_mapped": sum(bool(documents[f]["url"]) for f in original_files),
            "original_reports_unknown": sum(not documents[f]["url"] for f in original_files),
            "unique_first_followup_reports": len(follow_files),
            "first_followup_reports_mapped": sum(bool(documents[f]["url"]) for f in follow_files),
            "first_followup_reports_unknown": sum(not documents[f]["url"] for f in follow_files),
            "cases_with_both_urls": sum(bool(r["original_commitment_report_url"] and r["first_available_followup_url"]) for r in output),
            "cases_with_missing_original_url": sum(not r["original_commitment_report_url"] for r in output),
            "cases_with_missing_followup_url": sum(not r["first_available_followup_url"] for r in output),
            "flags_by_document": dict(Counter(flag for d in documents.values() for flag in d["ambiguity_flags"])),
        },
        "documents": documents,
    }
    (OUT / "URLmappingaudit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
