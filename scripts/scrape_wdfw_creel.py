#!/usr/bin/env python3
"""
WDFW Puget Sound Creel Report Scraper
Pulls public recreational fishing creel data from the Washington Department
of Fish & Wildlife (WDFW) Puget Sound creel reporting portal.
"""

import argparse
import json
import os
import sys
import urllib.request
from bs4 import BeautifulSoup

BASE_URL = "https://wdfw.wa.gov/fishing/reports/creel/puget"

def scrape_pages(sample_date=2, max_pages=30):
    records = []
    print(f"Scraping WDFW creel reports (sample_date={sample_date}, max_pages={max_pages})...")
    
    for page in range(max_pages):
        url = f"{BASE_URL}?ramp=&sample_date={sample_date}&catch_area=&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        try:
            with urllib.request.urlopen(req) as resp:
                html = resp.read().decode("utf-8")
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
                if len(tds) == len(headers) and len(tds) > 0:
                    page_rows += 1
                    records.append({
                        "date": date_str,
                        "ramp": tds[0],
                        "catch_area": tds[1],
                        "interviews": int(tds[2]) if tds[2].isdigit() else 0,
                        "anglers": int(tds[3]) if tds[3].isdigit() else 0,
                        "chinook_per_angler": float(tds[4]) if tds[4].replace(".", "", 1).isdigit() else 0.0,
                        "chinook": int(tds[5]) if tds[5].isdigit() else 0,
                        "coho": int(tds[6]) if tds[6].isdigit() else 0,
                        "chum": int(tds[7]) if tds[7].isdigit() else 0,
                        "pink": int(tds[8]) if tds[8].isdigit() else 0,
                        "sockeye": int(tds[9]) if tds[9].isdigit() else 0,
                        "lingcod": int(tds[10]) if tds[10].isdigit() else 0,
                        "halibut": int(tds[11]) if tds[11].isdigit() else 0,
                    })
        print(f"  Page {page}: Scraped {page_rows} records.")
        
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
    for r in new_records + existing:
        key = (r.get("date"), r.get("ramp"), r.get("catch_area"))
        if key not in seen:
            seen.add(key)
            merged.append(r)
            
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)
        
    print(f"Successfully saved {len(merged)} total creel records to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Scrape WDFW Puget Sound Creel Reports")
    parser.add_argument("--days", type=int, choices=[15, 30, 60], default=30, help="Window: 15, 30, or 60 days")
    parser.add_argument("--pages", type=int, default=30, help="Max pages to scrape")
    parser.add_argument("--out", type=str, default="../data/creel_data_2026_summer.json", help="Output JSON path")
    args = parser.parse_args()
    
    date_map = {15: 1, 30: 2, 60: 3}
    sample_date = date_map.get(args.days, 2)
    
    records = scrape_pages(sample_date=sample_date, max_pages=args.pages)
    merge_and_save(records, args.out)

if __name__ == "__main__":
    main()
