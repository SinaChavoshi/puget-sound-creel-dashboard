# 🎣 Puget Sound Salmon Creel Analytics & Migration Predictor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![WDFW Data](https://img.shields.io/badge/Data-WDFW%20Creel%20Reports-emerald.svg)](https://wdfw.wa.gov/fishing/reports/creel/puget)
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-Open-brightgreen.svg)](https://sinachavoshi.github.io/puget-sound-creel-dashboard/)
[![Refresh creel data](https://github.com/SinaChavoshi/puget-sound-creel-dashboard/actions/workflows/refresh-data.yml/badge.svg)](https://github.com/SinaChavoshi/puget-sound-creel-dashboard/actions/workflows/refresh-data.yml)

### 👉 **[Open the live dashboard](https://sinachavoshi.github.io/puget-sound-creel-dashboard/)** — no download needed

A real-time analytics dashboard and predictive modeling tool for Puget Sound recreational salmon fishing, built using official **Washington Department of Fish & Wildlife (WDFW)** creel survey data.

---

## 🚀 Live Dashboard

**https://sinachavoshi.github.io/puget-sound-creel-dashboard/**

The dashboard is served by GitHub Pages straight from `index.html` on `main`, so it opens in any browser (desktop or phone) without downloading anything. Your chosen areas and settings are saved in the URL, so you can bookmark or share a specific view.

Data refreshes automatically every morning: the [`Refresh creel data`](.github/workflows/refresh-data.yml) GitHub Action scrapes the last 60 days of WDFW reports, rebuilds `index.html`, and commits the result, which GitHub Pages then republishes. You can also run it on demand from the repo's **Actions** tab → *Refresh creel data* → **Run workflow**.

---

## 🌟 Key Features

- **Effort Normalization (CPUE):**  
  Raw fish counts are notoriously misleading because angler participation fluctuates by over 80% based on weekend vs. weekday weather and short-lived quota openings. This dashboard calculates true **Catch Per Unit Effort** (**CPUE = Fish / Angler** and **Fish / Boat Trip**) across all sampled ramps.

- **Multi-Area Comparison:**  
  Interactive multi-choice selector allows side-by-side comparison of any combination of marine areas (e.g., comparing **Area 9 (Admiralty)**, **Area 10 (Seattle)**, and **Area 11 (Tacoma)**). Includes one-click quick presets for Central Sound, Outer Straits, and Top Hotspots.

- **Higher-Order Non-Linear Trend Fitting:**  
  Unlike naive linear regressions that fail to capture seasonal migratory bell curves, the dashboard fits a **quadratic polynomial** ($y = ax^2 + bx + c$) to the most recent 35 days of sampled data, on a true calendar-day axis, with physical boundary clamping.

- **7-Day Smoothing & Hover Readouts:**  
  Optional rolling 7-day pooling (total fish ÷ total anglers) tames weekday/weekend noise; hover the chart for exact values per area.

- **Recent Momentum:**  
  Each area compares the last 7 days of coho per angler against the prior 7 days (flagged "Low sample" when fewer than 20 anglers were interviewed).

- **14-Day Forward Forecast Prediction:**  
  Extrapolates run timing and catch rates 14 days into the future, tracking the progression toward the late-August / mid-September peak.

- **Zero-Effort Day Filtering:**  
  Non-sampled days and zero-effort days are automatically excluded from trend regressions to prevent reporting gaps from skewing trend trajectories downward.

- **King Salmon (Chinook) Open Window Modeling:**  
  Accounts for short 2–3 day retention seasons (such as Area 10's 3-day opener and Area 7's 2-day opener), isolating open-window efficiency from season closures.

- **Instant Creel Search:**  
  Full client-side live search across individual dockside interview records by boat ramp, catch area, or date.

---

## 🌊 The 7-Day Phase-Shifted Ocean Migration Model

Field creel data validates that ocean Coho salmon funnelling into Puget Sound travel sequentially with an approximate **7-day (1-week) travel delay between major marine areas**:

```
                       [ PACIFIC OCEAN ]
                               │
            🔴 [ Area 5: Sekiu / Neah Bay Entrance ]
                 (Wave Origin / Day 0 Lead)
                               │
                               ▼ ~7 Days Swimming Travel Delay
            🟡 [ Area 9: Admiralty Inlet Gateway ]
                 (Wave Destination #1 / Day +7)
                               │
                               ▼ ~7 Days Swimming Travel Delay
            🔵 [ Area 10: Seattle-Bremerton Area ]
                 (Wave Destination #2 / Day +14)
```

1. **Sekiu Pulse (Area 5):** The ocean run enters through the Strait of Juan de Fuca (Sekiu / Pillar Point), surging first.
2. **Admiralty Inlet (Area 9):** Approximately 7 days later, schools pass through the Admiralty Inlet gateway.
3. **Seattle (Area 10):** Approximately 14 days after Sekiu (7 days after Admiralty), the main ocean wave reaches Central Sound (Jeff Head, Kingston, Meadow Point).

---

## 📁 Repository Structure

```
├── index.html                     # Standalone interactive dashboard (GitHub Pages entrypoint)
├── data/
│   └── creel_data_2026_summer.json # Scraped WDFW creel sampling dataset (JSON)
├── scripts/
│   ├── scrape_wdfw_creel.py       # Automated scraper for WDFW Puget Sound creel reports
│   ├── generate_dashboard.py      # Data processor and dashboard generator script
│   └── dashboard_template.html    # HTML/JS template the generator fills with data
├── .github/workflows/
│   └── refresh-data.yml           # Daily scrape + rebuild + commit
├── assets/
│   └── coho_full_season_trends.svg # Exported high-resolution SVG trend charts
├── LICENSE                        # MIT License
└── README.md                      # Project documentation
```

---

## 🛠️ Usage & Local Development

### 1. View the Dashboard Locally
Use the [live link](https://sinachavoshi.github.io/puget-sound-creel-dashboard/), or open `index.html` directly in any modern browser:
```bash
# On Linux
xdg-open index.html

# On macOS
open index.html
```

### 2. Updating Creel Data
To pull fresh creel numbers directly from the WDFW portal and rebuild the dashboard:

```bash
# Install BeautifulSoup if not already present
pip install beautifulsoup4

# Scrape the latest creel reports (60-day window by default; merges into the existing data,
# replacing rows WDFW has since revised)
python3 scripts/scrape_wdfw_creel.py

# Regenerate index.html and charts
python3 scripts/generate_dashboard.py
```

---

## 📊 Data Source & Attribution

Data is sourced from the **Washington Department of Fish & Wildlife (WDFW)** public Puget Sound Creel Reports:
- [WDFW In-Season Creel Reports](https://wdfw.wa.gov/fishing/reports/creel/puget)
- [WDFW Annual Creel Archive](https://wdfw.wa.gov/fishing/reports/creel/puget-annual)

*Disclaimer: This project is an independent open-source analytics tool and is not affiliated with or endorsed by the Washington Department of Fish and Wildlife.*

---

## 📄 License

Distributed under the [MIT License](LICENSE).
