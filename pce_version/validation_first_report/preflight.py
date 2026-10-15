#!/usr/bin/env python3
"""Read-only audit of the source-only human first-report templates.

This program only opens files in validation_first_report and source-only FF
packets. It never opens validation/, model rounds, adjudications, or outcome
datasets. JSON goes to stdout; --audit-output writes that JSON in this kit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
PACKETS = ROOT / "first_followup_packets"
FORBIDDEN_CARD_MARKERS = re.compile(r"\b(?:key_hidden|verdict_final|model_outcome|model_round|adjudicated_status)\b", re.I)


def safe_existing(relative: str, prefix: str) -> bool:
    path = Path(relative)
    return relative.startswith(prefix + "/") and ".." not in path.parts and (ROOT / path).is_file()


def audit() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = json.loads((PACKETS / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((KIT / "schema.json").read_text(encoding="utf-8"))
    cards = json.loads((KIT / "cards_manifest.json").read_text(encoding="utf-8"))
    ids = [item["case_id"] for item in manifest]
    if len(ids) != 183 or len(set(ids)) != 183:
        errors.append("Source manifest does not contain 183 unique cases")
    expected_counts = {"KZ": 27, "PL": 29, "NL": 127}
    counts = dict(Counter(item["country"] for item in manifest))
    if counts != expected_counts:
        errors.append(f"Unexpected country counts: {counts}")
    card_ids = [item["case_id"] for item in cards]
    if len(card_ids) != 183 or set(card_ids) != set(ids):
        errors.append("Card manifest coverage differs from source manifest")
    packet_by_id = {}
    for item in manifest:
        case_id = item["case_id"]
        expected_packet_path = f"first_followup_packets/{case_id}.json"
        if item.get("packet_path") != expected_packet_path:
            errors.append(f"Unexpected source packet path: {case_id}")
            continue
        packet_by_id[case_id] = json.loads((PACKETS / f"{case_id}.json").read_text(encoding="utf-8"))
    for item in cards:
        case_id = item["case_id"]
        packet = packet_by_id.get(case_id)
        if not packet:
            errors.append(f"No source-only packet for card: {case_id}")
            continue
        path = KIT / "cards" / f"{case_id}.md"
        if item["card_path"] != f"validation_first_report/cards/{case_id}.md" or not path.is_file():
            errors.append(f"Missing/incorrect card: {case_id}")
            continue
        content = path.read_text(encoding="utf-8")
        if FORBIDDEN_CARD_MARKERS.search(content):
            errors.append(f"Forbidden model/key marker in card: {case_id}")
        if "## Wider original context" not in content or "## Selected first available subsequent report" not in content:
            errors.append(f"Missing required card sections: {case_id}")
        if packet["original_excerpt"][:40] not in content:
            errors.append(f"Original excerpt not preserved: {case_id}")
        for year in (packet["commitment_year"], packet["first_available_report_year"]):
            if str(year) not in content:
                errors.append(f"Report-year metadata missing in card: {case_id}")
        if not content.strip().endswith(f"[FF JSON](../../first_followup_packets/{case_id}.json)"):
            errors.append(f"Missing source packet link: {case_id}")
        if item["context_provenance"] == "excerpt_only_context_not_located_open_full_original":
            warnings.append(f"Only archived excerpt context available: {case_id}")
        for role in ("original_source", "followup_source"):
            source = item[role]
            for key in ("url", "final_url", "text_path", "raw_path"):
                if source.get(key) != packet[role].get(key):
                    errors.append(f"Card manifest differs from supplied packet {role}.{key}: {case_id}")
            for key in ("url", "final_url"):
                url = source.get(key)
                parsed = urlparse(url or "")
                if not url or parsed.scheme not in ("https", "http") or not parsed.netloc or f"<{url}>" not in content:
                    errors.append(f"Missing/invalid provided {role}.{key}: {case_id}")
            for key in ("text_path", "raw_path"):
                value = source.get(key)
                if not value or not safe_existing(value, "sources_first_followup") or f"../../{value}" not in content:
                    errors.append(f"Missing/broken provided {role}.{key}: {case_id}")
    expected_columns = schema["metadata_columns"] + schema["response_columns"]
    sheets = {}
    for name in ("round_A_blank.csv", "round_B_blank.csv"):
        path = KIT / name
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != expected_columns:
                errors.append(f"Schema mismatch: {name}")
            rows = list(reader)
        if len(rows) != 183 or [row.get("case_id") for row in rows] != ids:
            errors.append(f"Case order/coverage mismatch: {name}")
        filled = []
        for row in rows:
            case_id = row.get("case_id", "")
            packet = packet_by_id.get(case_id)
            if packet and (
                row.get("country") != packet["country"]
                or row.get("company_identifier") != str(packet["company_identifier"])
                or row.get("commitment_year") != str(packet["commitment_year"])
                or row.get("selected_report_year") != str(packet["first_available_report_year"])
                or row.get("report_year_gap") != str(packet["first_available_report_year"] - packet["commitment_year"])
            ):
                errors.append(f"Prefilled metadata mismatch in {name}: {case_id}")
            if row.get("case_card") != f"cards/{case_id}.md":
                errors.append(f"Bad card pointer in {name}: {case_id}")
            for col in schema["response_columns"]:
                if row.get(col, "").strip():
                    filled.append(f"{case_id}:{col}")
        if filled:
            errors.append(f"Response fields are not blank in {name}: {', '.join(filled[:12])}")
        sheets[name] = {"rows": len(rows), "filled_response_cells": len(filled)}
    for name, required_ids in (("INDEX_KZ_PL.md", [i for i in ids if next(x for x in manifest if x["case_id"] == i)["country"] in ("KZ", "PL")]),
                               ("INDEX_NL.md", [i for i in ids if next(x for x in manifest if x["case_id"] == i)["country"] == "NL"])):
        content = (KIT / name).read_text(encoding="utf-8")
        linked = re.findall(r"\[FF\d{4}\]\(cards/(FF\d{4})\.md\)", content)
        if linked != required_ids:
            errors.append(f"Index coverage/order mismatch: {name}")
    return {
        "audit": "first_report_human_source_only_preflight_v1",
        "passed": not errors,
        "case_count": len(ids),
        "country_counts": counts,
        "cards_count": len(cards),
        "sheets": sheets,
        "errors": errors,
        "warnings": warnings,
        "limits": [
            "URLs were checked for syntax and preservation in cards; remote availability was not tested.",
            "Local source path existence was checked; report year, publication chronology, entity linkage and source adequacy remain for human review.",
            "No human coding, model comparison, or outcome validation was performed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, help="Write audit JSON inside validation_first_report")
    args = parser.parse_args()
    result = audit()
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.audit_output:
        destination = args.audit_output.resolve()
        if destination.parent != KIT.resolve():
            parser.error("audit output must be directly inside validation_first_report")
        destination.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
