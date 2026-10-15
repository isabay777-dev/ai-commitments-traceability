#!/usr/bin/env python3
"""Build source-only first-report human coding materials from FF packets.

Inputs are deliberately limited to first_followup_packets/manifest.json and
the FF*.json files it names. No validation keys, model rounds, or outcome data
are opened. Existing source files are linked, never copied or rewritten.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "first_followup_packets"
OUT = ROOT / "validation_first_report"
CARDS = OUT / "cards"

METADATA_COLUMNS = [
    "case_id", "country", "company_identifier", "commitment_year",
    "selected_report_year", "report_year_gap", "case_card",
]
RESPONSE_COLUMNS = [
    "coder_id", "coding_started_utc", "coding_finished_utc", "minutes_spent",
    "original_language", "followup_language",
    "original_entity", "original_perimeter", "followup_entity", "followup_perimeter",
    "entity_linkage", "entity_linkage_quote", "entity_linkage_locator",
    "eligibility", "eligibility_reason", "source_adequacy", "source_issue_detail",
    "retrieval_attempts", "extraction_quality_checked", "search_audit",
    "original_ai_function_quote", "original_ai_function_locator",
    "original_promise_quote", "original_promise_locator",
    "promised_stage", "promised_scope", "promised_ai_function",
    "initial_maturity", "specificity_process_named", "specificity_specific",
    "specificity_achieved_stage", "specificity_deadline_or_timeframe",
    "specificity_quantitative_target", "specificity_investment_amount",
    "specificity_named_solution_or_partner", "specificity_basis",
    "deadline_original_wording", "deadline_original_locator", "deadline_precision",
    "deadline_reference_date", "deadline_reference_locator",
    "deadline_resolved_date", "deadline_state_at_report",
    "original_period_end_date", "original_period_end_date_state", "original_period_end_locator",
    "original_publication_date", "original_publication_date_state", "original_publication_locator",
    "followup_period_end_date", "followup_period_end_date_state", "followup_period_end_locator",
    "followup_publication_date", "followup_publication_date_state", "followup_publication_locator",
    "object_linkage", "object_linkage_rationale",
    "ai_function_linkage", "ai_function_rationale",
    "status", "followup_ai_function_quote", "followup_ai_function_locator",
    "followup_stage_scope_quote", "followup_stage_scope_locator",
    "followup_event_date", "followup_event_date_state", "followup_event_date_locator",
    "identity_stage_scope_rationale", "cancellation_reported", "uncertainty_notes",
]

ENUMS = {
    "entity_linkage": ["yes", "no", "uncertain"],
    "eligibility": ["eligible", "not_a_promise", "unresolved"],
    "source_adequacy": ["adequate", "source_unavailable", "unreadable", "incomplete_extraction", "incomplete_search", "ambiguous_evidence"],
    "extraction_quality_checked": ["yes", "no", "uncertain"],
    "promised_stage": ["study", "pilot_or_test", "deployment", "other", "unspecified", "source_unavailable"],
    "initial_maturity": ["plan", "development", "test_not_live", "live_pilot", "deployed", "other", "unspecified", "source_unavailable"],
    "specificity_process_named": ["0", "1", "uncertain"],
    "specificity_specific": ["0", "1", "uncertain"],
    "specificity_achieved_stage": ["0", "1", "uncertain"],
    "specificity_deadline_or_timeframe": ["0", "1", "uncertain"],
    "specificity_quantitative_target": ["0", "1", "uncertain"],
    "specificity_investment_amount": ["0", "1", "uncertain"],
    "specificity_named_solution_or_partner": ["0", "1", "uncertain"],
    "deadline_precision": ["day", "month", "quarter", "year", "relative", "vague", "none_stated", "source_unavailable"],
    "deadline_state_at_report": ["elapsed", "not_yet_elapsed", "indeterminate", "no_deadline"],
    "original_period_end_date_state": ["known", "unknown", "unverified"],
    "original_publication_date_state": ["known", "unknown", "unverified"],
    "followup_period_end_date_state": ["known", "unknown", "unverified"],
    "followup_publication_date_state": ["known", "unknown", "unverified"],
    "object_linkage": ["yes", "no", "uncertain"],
    "ai_function_linkage": ["yes", "no", "uncertain"],
    "status": ["fulfilled", "partial", "not_fulfilled", "dropped", "not_a_promise"],
    "followup_event_date_state": ["known", "unknown", "unverified"],
    "cancellation_reported": ["yes", "no", "uncertain"],
}


def load_cases() -> list[dict]:
    manifest = json.loads((PACKETS / "manifest.json").read_text(encoding="utf-8"))
    cases = []
    seen = set()
    for item in manifest:
        case_id = item["case_id"]
        if not re.fullmatch(r"FF\d{4}", case_id) or case_id in seen:
            raise ValueError(f"Bad or duplicate case ID: {case_id}")
        seen.add(case_id)
        expected = f"first_followup_packets/{case_id}.json"
        if item["packet_path"] != expected:
            raise ValueError(f"Unexpected packet path for {case_id}")
        case = json.loads((PACKETS / f"{case_id}.json").read_text(encoding="utf-8"))
        if case["case_id"] != case_id or case["country"] != item["country"]:
            raise ValueError(f"Manifest mismatch: {case_id}")
        cases.append(case)
    if len(cases) != 183 or Counter(c["country"] for c in cases) != {"KZ": 27, "PL": 29, "NL": 127}:
        raise ValueError("Unexpected worklist coverage")
    return cases


def safe_source_path(value: str) -> Path:
    if not value.startswith("sources_first_followup/") or ".." in Path(value).parts:
        raise ValueError(f"Source path is outside allowed source tree: {value}")
    path = ROOT / value
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def recover_context(case: dict) -> tuple[str, str]:
    context = case.get("original_context") or ""
    if context.strip():
        return context, case.get("original_context_retrieval", "packet_context")
    # The old extraction missed a few archived excerpt anchors. Search only
    # alternative extraction of the same original report, using source words.
    words = re.findall(r"[\w’]+", case["original_excerpt"].casefold())
    for supplement in case["original_source"].get("supplementary_sources", []):
        text = safe_source_path(supplement["text_path"]).read_text(encoding="utf-8", errors="replace")
        anchors = []
        for start in range(0, len(words) - 5, 3):
            chunk = words[start:start + 6]
            if len(" ".join(chunk)) < 25:
                continue
            pattern = r"\s+".join(re.escape(word) for word in chunk)
            hit = re.search(pattern, text, re.IGNORECASE)
            if hit:
                anchors.append(hit.start())
        if anchors:
            # A middle anchor gives surrounding context without treating it as
            # a verified quotation or outcome.
            point = anchors[len(anchors) // 2]
            return text[max(0, point - 1800):point + 3700], "supplementary_original_extraction_window_unverified"
    return case["original_excerpt"], "excerpt_only_context_not_located_open_full_original"


def blockquote(text: str) -> str:
    return "\n".join("> " + line for line in text.replace("\r", "").split("\n"))


def source_lines(source: dict) -> list[str]:
    lines = []
    for key, label in (("url", "Original URL"), ("final_url", "Final URL")):
        url = source.get(key)
        if url:
            lines.append(f"- {label}: <{url}>")
    for key, label in (("text_path", "Full extracted text"), ("raw_path", "Raw source")):
        value = source.get(key)
        if value:
            safe_source_path(value)
            lines.append(f"- {label}: [open local file](../../{value}) (`{value}`)")
    if source.get("archive_member_path"):
        lines.append(f"- Archive member: `{source['archive_member_path']}`")
    for extra in source.get("supplementary_sources", []):
        value = extra.get("text_path")
        if value:
            safe_source_path(value)
            lines.append(f"- Supplementary extraction: [open local file](../../{value}) (`{value}`)")
    if source.get("source_caveat"):
        lines.append(f"- Source caveat: {source['source_caveat']}")
    return lines


def write_card(case: dict) -> dict:
    case_id = case["case_id"]
    context, context_provenance = recover_context(case)
    original = case["original_source"]
    followup = case["followup_source"]
    content = [
        f"# {case_id} — source-only first-report case card",
        "",
        f"Country: **{case['country']}** · Company identifier: `{case['company_identifier']}`",
        f"Original reporting year: **{case['commitment_year']}** · Selected first available subsequent reporting year: **{case['first_available_report_year']}**",
        f"Reporting-year gap: **{case['first_available_report_year'] - case['commitment_year']}** (not elapsed time)",
        "",
        "Use only the original report and the selected subsequent report linked below. Do not consult a later report for this case. Confirm report period, entity/perimeter and source adequacy yourself. The selected year and archive URLs are inventory metadata, not independently verified publication chronology.",
        "",
        "## Original excerpt (archived worklist pointer; may start/end mid-sentence)",
        "", blockquote(case["original_excerpt"]), "",
        f"## Wider original context — `{context_provenance}`", "",
        "This extraction window is a navigation aid. Verify wording and location in the full original report; extraction order can be imperfect.",
        "", blockquote(context), "",
        "## Original report", "", *source_lines(original), "",
        "## Selected first available subsequent report", "", *source_lines(followup), "",
        f"Source packet: [FF JSON](../../first_followup_packets/{case_id}.json)",
        "",
    ]
    (CARDS / f"{case_id}.md").write_text("\n".join(content), encoding="utf-8")
    return {
        "case_id": case_id,
        "country": case["country"],
        "card_path": f"validation_first_report/cards/{case_id}.md",
        "context_provenance": context_provenance,
        "original_source": {key: original.get(key) for key in ("url", "final_url", "text_path", "raw_path")},
        "followup_source": {key: followup.get(key) for key in ("url", "final_url", "text_path", "raw_path")},
    }


def write_sheet(cases: list[dict], name: str) -> None:
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS + RESPONSE_COLUMNS)
        writer.writeheader()
        for case in cases:
            writer.writerow({
                "case_id": case["case_id"],
                "country": case["country"],
                "company_identifier": case["company_identifier"],
                "commitment_year": case["commitment_year"],
                "selected_report_year": case["first_available_report_year"],
                "report_year_gap": case["first_available_report_year"] - case["commitment_year"],
                "case_card": f"cards/{case['case_id']}.md",
            })


def main() -> None:
    cases = load_cases()
    OUT.mkdir(exist_ok=True)
    CARDS.mkdir(exist_ok=True)
    cards = [write_card(case) for case in cases]
    schema = {
        "version": "first_report_human_v1",
        "metadata_columns": METADATA_COLUMNS,
        "response_columns": RESPONSE_COLUMNS,
        "enums": ENUMS,
        "row_count": len(cases),
        "country_counts": dict(Counter(case["country"] for case in cases)),
        "note": "All response columns are blank in both templates. No outcome labels are supplied.",
    }
    (OUT / "schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "cards_manifest.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("round_A_blank.csv", "round_B_blank.csv"):
        write_sheet(cases, name)
    for name, selected in (("INDEX_KZ_PL.md", [c for c in cases if c["country"] in ("KZ", "PL")]),
                           ("INDEX_NL.md", [c for c in cases if c["country"] == "NL"])):
        lines = [f"# {name.removeprefix('INDEX_').removesuffix('.md')} case cards", "", "Inventory order; source-only, no human coding is implied.", ""]
        lines.extend(f"- [{c['case_id']}](cards/{c['case_id']}.md) — {c['country']}, {c['commitment_year']} → {c['first_available_report_year']}" for c in selected)
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Built {len(cases)} source-only cards and two blank 183-row sheets in {OUT}")


if __name__ == "__main__":
    main()
