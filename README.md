# 🎣 Puget Sound Salmon Creel Analytics & Migration Predictor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![WDFW Data](https://img.shields.io/badge/Data-WDFW%20Creel%20Reports-emerald.svg)](https://wdfw.wa.gov/fishing/reports/creel/puget)
[![GitHub Pages](https://img.shields.io/badge/Deployment-GitHub%20Pages-brightgreen.svg)](#-live-dashboard--github-pages)

A real-time analytics dashboard and predictive modeling tool for Puget Sound recreational salmon fishing, built using official **Washington Department of Fish & Wildlife (WDFW)** creel survey data.

---

## 🚀 Live Dashboard & GitHub Pages

The repository contains a standalone, zero-dependency interactive dashboard at **[`index.html`](index.html)** designed for instant hosting on **GitHub Pages**.

To host your own live version:
1. Go to your repository on GitHub: `Settings` ➔ `Pages`
2. Under **Build and deployment**, select **Source**: `Deploy from a branch`
3. Select branch: `main`, folder: `/ (root)`
4. Click **Save** — your live dashboard will be accessible at:
   `https://<your-username>.github.io/<repo-name>/`

---

## 🌟 Key Features

- **Effort Normalization (CPUE):**  
  Raw fish counts are notoriously misleading because angler participation fluctuates by over 80% based on weekend vs. weekday weather and short-lived quota openings. This dashboard calculates true **Catch Per Unit Effort** (**CPUE = Fish / Angler** and **Fish / Boat Trip**) across all sampled ramps.

- **Multi-Area Comparison:**  
  Interactive multi-choice selector allows side-by-side comparison of any combination of marine areas (e.g., comparing **Area 9 (Admiralty)**, **Area 10 (Seattle)**, and **Area 11 (Tacoma)**). Includes one-click quick presets for Central Sound, Outer Straits, and Top Hotspots.

- **Higher-Order Non-Linear Trend Fitting:**  
  Unlike naive linear regressions that fail to capture seasonal migratory bell curves, the dashboard employs a **quadratic polynomial regression model** ($y = ax^2 + bx + c$) with physical boundary clamping.

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
│   └── generate_dashboard.py      # Data processor and dashboard generator script
├── assets/
│   └── coho_full_season_trends.svg # Exported high-resolution SVG trend charts
├── LICENSE                        # MIT License
└── README.md                      # Project documentation
```

---

## 🛠️ Usage & Local Development

### 1. View the Dashboard Locally
No web server or build step required! Simply open `index.html` in any modern web browser:
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

# Scrape the latest 30-day creel reports
python3 scripts/scrape_wdfw_creel.py --days 30

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
