"""
Download SEC 10-K filings from EDGAR as HTML files.
Uses the EDGAR submissions API.

SEC requires a User-Agent header with your name and email.
Update the USER_AGENT below with your details.
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# --- CONFIGURATION ---
# SEC requires identification - update with YOUR details
USER_AGENT = "RAGEvalStudio sarvagya@example.com"

# Companies and their CIK numbers (Central Index Key)
COMPANIES = {
    "AAPL": {"name": "Apple Inc", "cik": "0000320193"},
    "TSLA": {"name": "Tesla Inc", "cik": "0001318605"},
    "JPM":  {"name": "JPMorgan Chase", "cik": "0000019617"},
    "NVDA": {"name": "NVIDIA Corp", "cik": "0001045810"},
}

# Which filings to download per company
FILINGS_TO_DOWNLOAD = [
    {"type": "10-K", "count": 3},  # Last 3 annual reports
]

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sec_filings"


def fetch_json(url: str) -> dict:
    """Fetch JSON from SEC EDGAR API with required headers."""
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
    """Fetch raw bytes from a URL."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code} for {url}")
        return None


def get_filing_urls(cik: str, filing_type: str, count: int) -> list[dict]:
    """Get recent filing URLs from EDGAR for a given CIK and filing type."""
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


def download_filing(url: str, output_path: Path) -> bool:
    """Download a filing document and save it."""
    print(f"  Downloading: {url}")
    content = fetch_bytes(url)
    if content:
        output_path.write_bytes(content)
        size_kb = len(content) / 1024
        print(f"  [OK] Saved: {output_path.name} ({size_kb:.0f} KB)")
        return True
    return False


def main():
    print("=" * 60)
    print("SEC EDGAR Filing Downloader for RAG Eval Studio")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")

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
                filename = f"{ticker}_{filing_type.replace('-', '')}_{year}.htm"
                output_path = OUTPUT_DIR / filename

                if output_path.exists():
                    print(f"  [SKIP] Already exists: {filename}")
                    total_downloaded += 1
                    continue

                success = download_filing(filing["url"], output_path)
                if success:
                    total_downloaded += 1
                else:
                    total_failed += 1

                # SEC rate limit: max 10 requests/sec
                time.sleep(0.5)

        # Be polite to SEC servers
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"Done! Downloaded: {total_downloaded}, Failed: {total_failed}")
    print(f"Files are in: {OUTPUT_DIR}")
    print(f"\nNext step: Upload these to your S3 bucket.")
    print(f"  Run: .venv\\Scripts\\python.exe scripts/upload_to_s3.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
