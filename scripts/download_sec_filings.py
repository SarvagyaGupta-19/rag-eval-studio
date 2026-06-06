"""
Download SEC 10-K and 10-Q filings from EDGAR as HTML, convert to PDF, and save locally.
Uses the EDGAR submissions API.
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
import fitz  # PyMuPDF for HTML to PDF conversion

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# --- CONFIGURATION ---
USER_AGENT = "RAGEvalStudio sarvagya@example.com"

COMPANIES = {
    "AAPL": {"name": "Apple Inc", "cik": "0000320193"},
    "TSLA": {"name": "Tesla Inc", "cik": "0001318605"},
    "JPM":  {"name": "JPMorgan Chase", "cik": "0000019617"},
    "NVDA": {"name": "NVIDIA Corp", "cik": "0001045810"},
}

# Balanced mix of K and Q
FILINGS_TO_DOWNLOAD = [
    {"type": "10-K", "count": 2},
    {"type": "10-Q", "count": 2},
]

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sec_filings"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code} for {url}")
        return {}


def fetch_bytes(url: str) -> bytes | None:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code} for {url}")
        return None


def get_filing_urls(cik: str, filing_type: str, count: int) -> list[dict]:
    cik_padded = cik.lstrip("0").zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    data = fetch_json(url)
    if not data:
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])

    results = []
    for i, form in enumerate(forms):
        if form == filing_type and len(results) < count:
            accession_clean = accessions[i].replace("-", "")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_clean}/{primary_docs[i]}"
            results.append({
                "url": doc_url,
                "date": filing_dates[i],
                "accession": accessions[i],
                "primary_doc": primary_docs[i],
            })

    return results


def download_filing_as_pdf(url: str, output_path: Path) -> bool:
    print(f"  Downloading: {url}")
    content = fetch_bytes(url)
    if content:
        try:
            # Load HTML content and convert to PDF using PyMuPDF
            html_doc = fitz.open(stream=content, filetype="html")
            pdf_bytes = html_doc.convert_to_pdf()
            output_path.write_bytes(pdf_bytes)
            size_kb = len(pdf_bytes) / 1024
            print(f"  [OK] Saved PDF: {output_path.name} ({size_kb:.0f} KB)")
            html_doc.close()
            return True
        except Exception as e:
            print(f"  [FAIL] Conversion to PDF failed: {e}")
            return False
    return False


def main():
    print("=" * 60)
    print("SEC EDGAR PDF Downloader for RAG Eval Studio")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    total_failed = 0

    for ticker, info in COMPANIES.items():
        print(f"\n{'-' * 50}")
        print(f"Company: {info['name']} ({ticker}) -- CIK: {info['cik']}")
        print(f"{'-' * 50}")

        for filing_spec in FILINGS_TO_DOWNLOAD:
            filing_type = filing_spec["type"]
            count = filing_spec["count"]

            print(f"\n  Fetching last {count} {filing_type} filings...")
            filings = get_filing_urls(info["cik"], filing_type, count)

            if not filings:
                print(f"  [FAIL] No {filing_type} filings found!")
                total_failed += count
                continue

            for filing in filings:
                year = filing["date"][:4]
                # Note: Adding accession to filename to avoid overwrites for multiple Qs in same year
                accession_short = filing["accession"].split("-")[-1]
                filename = f"{ticker}_{filing_type.replace('-', '')}_{year}_{accession_short}.pdf"
                output_path = OUTPUT_DIR / filename

                if output_path.exists():
                    print(f"  [SKIP] Already exists: {filename}")
                    total_downloaded += 1
                    continue

                success = download_filing_as_pdf(filing["url"], output_path)
                if success:
                    total_downloaded += 1
                else:
                    total_failed += 1

                time.sleep(0.5)

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"Done! Downloaded: {total_downloaded}, Failed: {total_failed}")
    print(f"Files are in: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
