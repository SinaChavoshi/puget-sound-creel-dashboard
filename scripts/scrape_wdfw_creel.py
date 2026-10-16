#!/usr/bin/env python3
"""
WDFW Puget Sound Creel Report Scraper
Pulls public recreational fishing creel data from the Washington Department
of Fish & Wildlife (WDFW) Puget Sound creel reporting portal.

Newly scraped rows replace existing rows with the same (date, ramp, catch_area)
key, so WDFW's post-QA/QC revisions within the scrape window are picked up.
"""

import argparse
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BASE_URL = "https://wdfw.wa.gov/fishing/reports/creel/puget"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "..", "data", "creel_data_2026_summer.json")

INT_COLS = ["interviews", "anglers"]
FISH_COLS = ["chinook", "coho", "chum", "pink", "sockeye", "lingcod", "halibut"]


def to_int(s):
    s = s.replace(",", "").strip()
    return int(s) if s.isdigit() else 0


def to_float(s):
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return 0.0


def fetch(url, retries=3):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (puget-sound-creel-dashboard; +https://github.com/SinaChavoshi/puget-sound-creel-dashboard)",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  Retry {attempt + 1} for {url}: {e}")
            time.sleep(3 * (attempt + 1))


def scrape_pages(sample_date=3, max_pages=60):
    records = []
    # WDFW's CDN caches each page URL; a unique query param guarantees fresh pages.
    bust = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"Scraping WDFW creel reports (sample_date={sample_date}, max_pages={max_pages})...")

    for page in range(max_pages):
        url = f"{BASE_URL}?ramp=&sample_date={sample_date}&catch_area=&page={page}&nc={bust}"
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            print(f"  Page {page}: No tables found. Finished pagination.")
            break

        page_rows = 0
        for t in tables:
            caption = t.find("caption")
            date_str = caption.get_text(strip=True) if caption else None
            headers = [th.get_text(strip=True) for th in t.find_all("th")]
            for r in t.find_all("tr"):
                tds = [td.get_text(strip=True) for td in r.find_all("td")]
                if len(tds) == len(headers) and len(tds) >= 12:
                    page_rows += 1
                    rec = {
                        "date": date_str,
                        "ramp": tds[0],
                        "catch_area": tds[1],
                        "interviews": to_int(tds[2]),
                        "anglers": to_int(tds[3]),
                        "chinook_per_angler": to_float(tds[4]),
                    }
                    for i, col in enumerate(FISH_COLS):
                        rec[col] = to_int(tds[5 + i])
                    records.append(rec)
        print(f"  Page {page}: Scraped {page_rows} records.")
        if page_rows == 0:
            break
        time.sleep(0.5)  # be polite to the WDFW server

    return records


def merge_and_save(new_records, output_file):
    existing = []
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    seen = set()
    merged = []
    for r in new_records + existing:  # new rows first, so they win
        key = (r.get("date"), r.get("ramp"), r.get("catch_area"))
        if key not in seen and r.get("date"):
            seen.add(key)
            merged.append(r)

    merged.sort(key=lambda r: (datetime.strptime(r["date"], "%b %d, %Y"), r["ramp"], r["catch_area"]), reverse=True)

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)

    added = len(merged) - len(existing)
    print(f"Saved {len(merged)} total creel records to {output_file} ({added:+d} vs before)")


def main():
    parser = argparse.ArgumentParser(description="Scrape WDFW Puget Sound Creel Reports")
    parser.add_argument("--days", type=int, choices=[15, 30, 60], default=60, help="Window: 15, 30, or 60 days")
    parser.add_argument("--pages", type=int, default=60, help="Max pages to scrape")
    parser.add_argument("--out", type=str, default=DEFAULT_OUT, help="Output JSON path")
    args = parser.parse_args()

    date_map = {15: 1, 30: 2, 60: 3}
    records = scrape_pages(sample_date=date_map[args.days], max_pages=args.pages)
    if not records:
        raise SystemExit("No records scraped; leaving data file unchanged.")
    merge_and_save(records, args.out)


if __name__ == "__main__":
    main()
