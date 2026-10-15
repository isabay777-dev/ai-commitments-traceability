"""Recover Bank Millennium management report text from locally saved annual ZIPs.

Only the explicitly named PDF members are read. ZIP contents are never extracted
to the filesystem or executed. Run from the PCE_submission directory.
"""

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

import fitz


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "sources_first_followup"
CASES = (
    (
        2023,
        "272336ce80737a24f4bd016f08a757e2dc32ee88370fd2a1c7e82b53fce9f9bb",
        "1_Management Board Report Millennium 2023_pdf.pdf",
        "PL_Bank_Millennium",
    ),
    (
        2024,
        "4abfae8b7a4e938c37575dfd551ea6ef5319f9d2f374275758d632cfb592899d",
        "1_Management Report_Millennium_2024_pdf.pdf",
        "PL_Bank_Millennium",
    ),
    (2021, "47959bb2492341d2740838597833d0912680ba54f059bd828ab88cf59d3a3f40",
     "mBank Group Management Board Report on Performance in 2021.pdf", "PL_mBank"),
    (2022, "74c52fdf81c05e10de149c9113f5b62751effdb1801aa6f16682cbf3d4c42b69",
     "mBank Group Management Board Report on Performance in 2022.pdf", "PL_mBank"),
    (2023, "c986ab31fb52bb545c95f6b1874cb634dca024580dadac87937e14a0df92ec70",
     "mBank Management Board Report on Performance in 2023.pdf", "PL_mBank"),
    (2024, "fe8e1cf2fa9f9a64d87b1c444260f1c4b1da091c188f72d1b6ccf487ff745de2",
     "mBank Management Board Report on Performance in 2024.pdf", "PL_mBank"),
    (2025, "5630a4b9862453d5a28ce44ef969e215d78b9e6114b09b56f74c06e1cfaa77ce",
     "Skonsolidowany EN/mBank Management Board Report on Performance in 2025.pdf", "PL_mBank"),
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_member(info):
    name = info.filename
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or "\\" in name or
            name.startswith("/") or not name or info.file_size > 50_000_000):
        raise ValueError(f"Unsafe ZIP member: {name!r}")
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode):
        raise ValueError(f"Symlink ZIP member: {name!r}")
    if info.flag_bits & 1:
        raise ValueError(f"Encrypted ZIP member: {name!r}")


def recover(year, archive_sha, member_name, series):
    archive_path = SOURCE_DIR / "raw" / f"{archive_sha}.zip"
    archive_bytes = archive_path.read_bytes()
    if sha256(archive_bytes) != archive_sha:
        raise ValueError(f"Archive SHA-256 mismatch: {archive_path}")

    with zipfile.ZipFile(archive_path) as zf:
        infos = zf.infolist()
        for info in infos:
            validate_member(info)
        matches = [i for i in infos if i.filename == member_name]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {member_name!r}")
        selected = matches[0]
        pdf_bytes = zf.read(selected)
        inventory = [
            {"path": i.filename, "uncompressed_bytes": i.file_size,
             "crc32": f"{i.CRC:08x}"}
            for i in infos
        ]

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page = document[0].get_text(sort=True)
    if series == "PL_mBank":
        expected = ["Management Board Report", "mBank S.A. Group", f"in {year}",
                    "including Management Board Report on Performance of mBank S.A.",
                    "translation from the original Polish version"]
        reporting_entity = "mBank S.A. Group (including Management Board Report on Performance of mBank S.A.)"
        report_type = "Management Board Report on Performance"
        caveat = ("English translation and non-official PDF copy of the Polish ESEF management report; "
                  "title page states that the Polish version prevails and this PDF copy was not subject "
                  "to statutory-auditor attestation procedures.")
        policy_ambiguity = ("Archive provides an English translation while naming the Polish ESEF version "
                            "as official. The report explicitly combines group and bank management reporting; "
                            "this one PDF is retained as published, with no merger of separate archive members.")
    else:
        expected = ["Management Board Report", "Bank Millennium", f"in {year}"]
        reporting_entity = "Bank Millennium S.A. and Capital Group of Bank Millennium S.A."
        report_type = "Management Board Report on activity"
        caveat = "English translation; PDF title page states that the Polish ESEF version is official."
        policy_ambiguity = ("Archive provides an English translation while naming the Polish ESEF version "
                            "as official. Management reporting covers both the bank and its capital group.")
    if any(fragment not in first_page for fragment in expected):
        raise ValueError(f"Title-page verification failed for {year}")
    pages = [page.get_text(sort=True).strip() for page in document]
    if sum(len(page) for page in pages) < 50_000:
        raise ValueError(f"Unexpectedly little extracted text for {year}")
    text = "\n\n".join(
        f"=== PDF page {n} ===\n{page}" for n, page in enumerate(pages, 1)
    ) + "\n"
    output_path = SOURCE_DIR / "text" / f"{series}_{year}.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_bytes = text.encode("utf-8")
    output_path.write_bytes(output_bytes)

    return {
        "file": output_path.name,
        "status": "recovered",
        "report_year": year,
        "reporting_entity": reporting_entity,
        "report_type": report_type,
        "archive_path": str(archive_path.relative_to(ROOT)),
        "archive_sha256": archive_sha,
        "archive_bytes": len(archive_bytes),
        "archive_member_inventory": inventory,
        "selected_member_path": member_name,
        "selected_member_sha256": sha256(pdf_bytes),
        "selected_member_bytes": len(pdf_bytes),
        "selected_member_crc32": f"{selected.CRC:08x}",
        "selection_evidence": "PDF title page names the report, reporting entity, and year; management report chosen over separate consolidated financial statements and other attachments.",
        "source_caveat": caveat,
        "source_policy_ambiguity": policy_ambiguity,
        "extraction_method": f"PyMuPDF {fitz.VersionBind}: PDF opened from ZIP member bytes, page.get_text(sort=True), with page markers; no ZIP filesystem extraction",
        "pdf_pages": len(pages),
        "output_path": str(output_path.relative_to(ROOT)),
        "output_bytes": len(output_bytes),
        "output_sha256": sha256(output_bytes),
    }


def main():
    results = [recover(*case) for case in CASES]
    manifest_path = SOURCE_DIR / "archive_recovery_manifest.json"
    manifest_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for item in results:
        print(item["file"], item["pdf_pages"], "pages", item["output_bytes"], "bytes")


if __name__ == "__main__":
    main()
