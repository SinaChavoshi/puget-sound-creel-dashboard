#!/usr/bin/env python3
"""
Dashboard Generator Script
Processes scraped creel data and produces a self-contained, responsive
interactive web dashboard (index.html) and SVG trend charts for GitHub Pages.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

def build_dashboard(data_file="../data/creel_data_2026_summer.json", output_html="../index.html", output_svg="../assets/coho_full_season_trends.svg"):
    with open(data_file, "r") as f:
        raw_data = json.load(f)

    def parse_date(d_str):
        return datetime.strptime(d_str, "%b %d, %Y")

    # Filter for the summer salmon season: July 19 to August 31, 2026
    summer_data = [r for r in raw_data if r.get("date") and parse_date(r["date"]) >= datetime(2026, 7, 19)]
    unique_dates_dt = sorted(list(set(parse_date(r["date"]) for r in summer_data)))
    unique_dates_str = [d.strftime("%b %d, %Y") for d in unique_dates_dt]
    factual_date_labels = [d.strftime("%b %d") for d in unique_dates_dt]

    # Generate 14 future dates (Sep 1 to Sep 14)
    last_factual_dt = unique_dates_dt[-1]
    future_dates_dt = [last_factual_dt + timedelta(days=i) for i in range(1, 15)]
    future_date_labels = [d.strftime("%b %d") for d in future_dates_dt]

    all_date_labels = factual_date_labels + future_date_labels
    all_dates_str = unique_dates_str + [d.strftime("%b %d, %Y") for d in future_dates_dt]

    all_catch_areas = sorted(list(set(r["catch_area"] for r in summer_data)))

    # Build structured data matrix: data[date][region]
    matrix = defaultdict(lambda: defaultdict(lambda: {"chinook": 0, "coho": 0, "chum": 0, "pink": 0, "sockeye": 0, "lingcod": 0, "halibut": 0, "anglers": 0, "boats": 0}))

    for r in summer_data:
        d = r["date"]
        ca = r["catch_area"]
        m = matrix[d][ca]
        m["chinook"] += r["chinook"]
        m["coho"] += r["coho"]
        m["chum"] += r["chum"]
        m["pink"] += r["pink"]
        m["sockeye"] += r["sockeye"]
        m["lingcod"] += r["lingcod"]
        m["halibut"] += r["halibut"]
        m["anglers"] += r["anglers"]
        m["boats"] += r["interviews"]

    # Build regional summaries
    region_summaries = {}
    split_idx = 21 # Mid-August split

    for ca in all_catch_areas:
        tot_chinook = sum(matrix[d][ca]["chinook"] for d in unique_dates_str)
        tot_coho = sum(matrix[d][ca]["coho"] for d in unique_dates_str)
        tot_anglers = sum(matrix[d][ca]["anglers"] for d in unique_dates_str)
        tot_boats = sum(matrix[d][ca]["boats"] for d in unique_dates_str)
        
        early_chinook = sum(matrix[d][ca]["chinook"] for d in unique_dates_str[:split_idx])
        late_chinook = sum(matrix[d][ca]["chinook"] for d in unique_dates_str[split_idx:])
        early_coho = sum(matrix[d][ca]["coho"] for d in unique_dates_str[:split_idx])
        late_coho = sum(matrix[d][ca]["coho"] for d in unique_dates_str[split_idx:])
        early_ang = sum(matrix[d][ca]["anglers"] for d in unique_dates_str[:split_idx])
        late_ang = sum(matrix[d][ca]["anglers"] for d in unique_dates_str[split_idx:])
        
        region_summaries[ca] = {
            "total_chinook": tot_chinook,
            "total_coho": tot_coho,
            "total_salmon": tot_chinook + tot_coho,
            "total_anglers": tot_anglers,
            "total_boats": tot_boats,
            "early_chinook": early_chinook,
            "late_chinook": late_chinook,
            "early_coho": early_coho,
            "late_coho": late_coho,
            "early_anglers": early_ang,
            "late_anglers": late_ang,
            "king_cpue": round(tot_chinook / tot_anglers, 2) if tot_anglers > 0 else 0.0,
            "coho_cpue": round(tot_coho / tot_anglers, 2) if tot_anglers > 0 else 0.0,
            "late_king_cpue": round(late_chinook / late_ang, 2) if late_ang > 0 else 0.0,
            "late_coho_cpue": round(late_coho / late_ang, 2) if late_ang > 0 else 0.0,
            "daily_chinook": [matrix[d][ca]["chinook"] for d in unique_dates_str],
            "daily_coho": [matrix[d][ca]["coho"] for d in unique_dates_str],
            "daily_anglers": [matrix[d][ca]["anglers"] for d in unique_dates_str],
            "daily_boats": [matrix[d][ca]["boats"] for d in unique_dates_str]
        }

    sound_totals = {
        "dates": factual_date_labels,
        "full_dates": unique_dates_str,
        "daily_chinook": [sum(matrix[d][ca]["chinook"] for ca in all_catch_areas) for d in unique_dates_str],
        "daily_coho": [sum(matrix[d][ca]["coho"] for ca in all_catch_areas) for d in unique_dates_str],
        "daily_anglers": [sum(matrix[d][ca]["anglers"] for ca in all_catch_areas) for d in unique_dates_str],
        "daily_boats": [sum(matrix[d][ca]["boats"] for ca in all_catch_areas) for d in unique_dates_str],
    }

    payload = {
        "factual_dates": factual_date_labels,
        "all_dates": all_date_labels,
        "num_factual": len(factual_date_labels),
        "num_future": len(future_date_labels),
        "catch_areas": all_catch_areas,
        "sound_totals": sound_totals,
        "region_summaries": region_summaries,
        "raw_records": summer_data
    }

    payload_json_str = json.dumps(payload)

    # HTML Dashboard Source
    html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Puget Sound Salmon Creel Analytics Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --app-background: #0f172a;
      --app-foreground: #f8fafc;
      --app-card: #1e293b;
      --app-card-border: #334155;
      --app-border: #334155;
      --app-muted-foreground: #94a3b8;
    }
  </style>
</head>
<body class="bg-[#0f172a] text-[#f8fafc] font-sans antialiased p-4 space-y-6">

  <!-- Header Card -->
  <div class="bg-[var(--app-card)] border border-[var(--app-border)] rounded-xl p-5 shadow-lg">
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <span>🎣</span> Puget Sound Salmon Creel Analytics
        </h1>
        <p class="text-sm text-[var(--app-muted-foreground)] mt-1">
          Real-time Washington WDFW Creel Analytics • Multi-Area Comparison • Non-Linear Trend Predictions
        </p>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-3">
        <!-- Species Mode Selector -->
        <div>
          <label class="block text-xs font-semibold text-slate-400 mb-1">Species Display</label>
          <select id="speciesModeSelect" class="bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 font-medium">
            <option value="COHO" selected>🐟 Coho Salmon Only</option>
            <option value="CHINOOK">👑 Chinook (King Salmon) Only</option>
            <option value="DUAL">👑 Kings & 🐟 Coho (Dual View)</option>
          </select>
        </div>

        <!-- Metric Mode Selector -->
        <div>
          <label class="block text-xs font-semibold text-slate-400 mb-1">Metric Mode</label>
          <select id="metricModeSelect" class="bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 font-medium">
            <option value="CPUE_ANG" selected>Catch Per Angler (CPUE)</option>
            <option value="RAW">Fish Landed (Raw Count)</option>
            <option value="CPUE_BOAT">Catch Per Boat Trip</option>
            <option value="EFFORT">Angler Effort (Fishermen Count)</option>
          </select>
        </div>

        <!-- View Display Mode (Actual vs Trend vs Both) -->
        <div>
          <label class="block text-xs font-semibold text-slate-400 mb-1">Display Mode</label>
          <select id="displayModeSelect" class="bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-yellow-500 font-medium text-yellow-300">
            <option value="BOTH" selected>✨ Actual Data + Dotted Prediction</option>
            <option value="ACTUAL">Solid Actual Data Only</option>
            <option value="TREND">Dotted Trend Prediction Only</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Multi-Choice Catch Area Filter Bar -->
    <div class="mt-4 pt-4 border-t border-slate-800 space-y-2">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Select Catch Areas to Compare (Multi-Choice):
        </span>
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <button id="btnSelectAll" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition">Select All</button>
          <button id="btnClearAll" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition">Clear All</button>
          <span class="text-slate-600">|</span>
          <span class="text-slate-400 font-medium">Presets:</span>
          <button id="presetCentral" class="px-2.5 py-1 rounded bg-blue-950/60 hover:bg-blue-900/80 text-blue-300 border border-blue-800/60 transition">Central Sound (9, 10, 11)</button>
          <button id="presetStraits" class="px-2.5 py-1 rounded bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-800/60 transition">Straits (5, 6, 7, Bellingham)</button>
          <button id="presetHotspots" class="px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/60 transition">Top Coho (5, 8-2, 9, 10)</button>
        </div>
      </div>

      <!-- Area Checkbox Pills -->
      <div id="areaPillsContainer" class="flex flex-wrap gap-2 pt-1 max-h-36 overflow-y-auto">
        <!-- Populated dynamically -->
      </div>
    </div>
  </div>

  <!-- Key Metric KPI Cards -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="bg-[var(--app-card)] border border-amber-500/30 rounded-xl p-4 shadow-sm bg-gradient-to-br from-slate-900 to-amber-950/20">
      <div class="flex justify-between items-start">
        <span class="text-xs font-bold text-amber-400 uppercase tracking-wider">👑 Kings (Chinook)</span>
        <span id="kingBadge" class="text-xs px-2 py-0.5 rounded bg-amber-400/10 text-amber-400 font-semibold">0.00 CPUE</span>
      </div>
      <div id="statKings" class="text-2xl font-bold text-slate-100 mt-2">0</div>
      <div id="statKingSub" class="text-xs text-slate-400 mt-1">In selected areas</div>
    </div>

    <div class="bg-[var(--app-card)] border border-cyan-500/30 rounded-xl p-4 shadow-sm bg-gradient-to-br from-slate-900 to-cyan-950/20">
      <div class="flex justify-between items-start">
        <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider">🐟 Coho Salmon</span>
        <span id="cohoBadge" class="text-xs px-2 py-0.5 rounded bg-cyan-400/10 text-cyan-400 font-semibold">0.00 CPUE</span>
      </div>
      <div id="statCoho" class="text-2xl font-bold text-slate-100 mt-2">0</div>
      <div id="statCohoSub" class="text-xs text-slate-400 mt-1">In selected areas</div>
    </div>

    <div class="bg-[var(--app-card)] border border-blue-500/30 rounded-xl p-4 shadow-sm bg-gradient-to-br from-slate-900 to-blue-950/20">
      <div class="flex justify-between items-start">
        <span class="text-xs font-bold text-blue-400 uppercase tracking-wider">🎣 Angler Participation</span>
        <span id="boatBadge" class="text-xs px-2 py-0.5 rounded bg-blue-400/10 text-blue-400 font-semibold">0 Boats</span>
      </div>
      <div id="statAnglers" class="text-2xl font-bold text-slate-100 mt-2">0</div>
      <div class="text-xs text-slate-400 mt-1">Total fishermen in selected areas</div>
    </div>

    <div class="bg-[var(--app-card)] border border-yellow-500/30 rounded-xl p-4 shadow-sm bg-gradient-to-br from-slate-900 to-yellow-950/20">
      <div class="flex justify-between items-start">
        <span class="text-xs font-bold text-yellow-400 uppercase tracking-wider">🔮 14-Day Prediction</span>
        <span id="forecastBadge" class="text-xs px-2 py-0.5 rounded bg-yellow-400/10 text-yellow-300 font-semibold">Forward Curve</span>
      </div>
      <div id="statForecastSummary" class="text-lg font-bold text-slate-100 mt-2 truncate">Extrapolating...</div>
      <div id="statForecastSub" class="text-xs text-slate-400 mt-1">Higher-order polynomial curve fit</div>
    </div>
  </div>

  <!-- Main Time Series & Future Forecast Chart Card -->
  <div class="bg-[var(--app-card)] border border-[var(--app-border)] rounded-xl p-5 shadow-lg space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 id="chartTitle" class="text-lg font-semibold text-slate-100">
          Daily Trends &amp; Higher-Order Future Predictions
        </h2>
        <p id="chartSub" class="text-xs text-[var(--app-muted-foreground)]">
          Solid lines = Factual Creel Records • Dotted lines = Higher-Order Trend Curve &amp; 14-Day Forward Forecast
        </p>
      </div>
      <div id="chartLegend" class="flex flex-wrap items-center gap-3 text-xs font-medium">
        <!-- Legend dynamically updated -->
      </div>
    </div>
    <div class="w-full h-84 relative">
      <canvas id="mainChartCanvas" class="w-full h-full block"></canvas>
    </div>
  </div>

  <!-- Regional Summary & Momentum Table Card -->
  <div class="bg-[var(--app-card)] border border-[var(--app-border)] rounded-xl p-5 shadow-lg space-y-4 overflow-hidden">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <h2 class="text-lg font-semibold text-slate-100">Selected Areas Performance &amp; Run Momentum Table</h2>
      <span class="text-xs text-slate-400">Comparing Early Season vs Peak Late Season for checked areas</span>
    </div>
    <div class="overflow-x-auto border border-slate-700/50 rounded-lg">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-900 text-xs font-semibold text-slate-400 uppercase border-b border-slate-700">
          <tr>
            <th class="px-4 py-3">Region / Catch Area</th>
            <th class="px-4 py-3 text-right text-amber-400">Total Kings</th>
            <th class="px-4 py-3 text-right text-cyan-400">Total Coho</th>
            <th class="px-4 py-3 text-right font-bold text-slate-100">Total Salmon</th>
            <th class="px-4 py-3 text-right">Anglers</th>
            <th class="px-4 py-3 text-right text-amber-400 font-bold">King CPUE</th>
            <th class="px-4 py-3 text-right text-cyan-400 font-bold">Coho CPUE</th>
            <th class="px-4 py-3 text-center">Coho Momentum</th>
            <th class="px-4 py-3 text-center">King Status</th>
          </tr>
        </thead>
        <tbody id="regionTableBody" class="divide-y divide-slate-800 font-mono">
          <!-- Populated dynamically -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- Raw Sampling Records Table with Live Search & Area Filter -->
  <div class="bg-[var(--app-card)] border border-[var(--app-border)] rounded-xl p-5 shadow-lg space-y-4 overflow-hidden">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold text-slate-100">Field Sampling Records (Selected Areas)</h2>
        <span id="recordCount" class="text-xs text-slate-400">Showing 0 records</span>
      </div>
      <div class="w-full sm:w-72">
        <input id="searchInput" type="text" placeholder="Filter by ramp, date, or area..." class="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none placeholder-slate-500 font-sans" />
      </div>
    </div>
    <div class="max-h-96 overflow-y-auto border border-slate-700/50 rounded-lg">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-900 sticky top-0 text-xs font-semibold text-slate-400 uppercase border-b border-slate-700">
          <tr>
            <th class="px-4 py-2.5">Date</th>
            <th class="px-4 py-2.5">Ramp / Site</th>
            <th class="px-4 py-2.5">Catch Area</th>
            <th class="px-4 py-2.5 text-right">Anglers</th>
            <th class="px-4 py-2.5 text-right">Boats</th>
            <th class="px-4 py-2.5 text-right text-amber-400">Chinook</th>
            <th class="px-4 py-2.5 text-right text-cyan-400">Coho</th>
            <th class="px-4 py-2.5 text-right text-emerald-400">CPUE</th>
          </tr>
        </thead>
        <tbody id="rawTableBody" class="divide-y divide-slate-800 text-xs">
          <!-- Populated dynamically -->
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const data = DATA_PLACEHOLDER;

    const areaColors = {
      'Area 10, Seattle-Bremerton area': '#3b82f6',
      'Area 11, Tacoma-Vashon Island': '#ec4899',
      'Area 9, Admiralty Inlet': '#f59e0b',
      'Area 5, Sekiu and Pillar Point': '#ef4444',
      'Area 8-2, Ports Susan and Gardner': '#10b981',
      'Area 6, East Juan de Fuca Strait': '#eab308',
      'Bellingham Bay': '#06b6d4',
      'Quilcene, Dabob Bay': '#6366f1',
      'Area 7, San Juan Islands': '#8b5cf6',
      'Area 6-1, Western portion of Area 6': '#64748b',
      'Area 12, Hood Canal': '#14b8a6',
      'Inner Elliot Bay Fishery Area': '#a855f7',
      'Area 4, Eastern portion': '#f97316',
      'Area 13, South Puget Sound': '#84cc16',
      'Area 8-1, Deception Pass, Hope Island, and Skagit Bay': '#d946ef'
    };

    const defaultColors = ['#3b82f6', '#ec4899', '#f59e0b', '#ef4444', '#10b981', '#06b6d4', '#8b5cf6', '#64748b', '#14b8a6', '#f97316'];

    function getAreaColor(ca, idx) {
      return areaColors[ca] || defaultColors[idx % defaultColors.length];
    }

    function getShortName(ca) {
      if (ca.includes(',')) return ca.split(',')[0];
      return ca;
    }

    const selectedAreas = new Set([
      'Area 5, Sekiu and Pillar Point',
      'Area 8-2, Ports Susan and Gardner',
      'Area 9, Admiralty Inlet',
      'Area 10, Seattle-Bremerton area'
    ]);

    const speciesModeSelect = document.getElementById('speciesModeSelect');
    const metricModeSelect = document.getElementById('metricModeSelect');
    const displayModeSelect = document.getElementById('displayModeSelect');
    const searchInput = document.getElementById('searchInput');
    const pillsContainer = document.getElementById('areaPillsContainer');

    function renderAreaPills() {
      pillsContainer.innerHTML = '';
      const sortedAreas = [...data.catch_areas].sort((a,b) => {
        const sa = data.region_summaries[a] ? data.region_summaries[a].total_salmon : 0;
        const sb = data.region_summaries[b] ? data.region_summaries[b].total_salmon : 0;
        return sb - sa;
      });

      sortedAreas.forEach((ca, idx) => {
        const isChecked = selectedAreas.has(ca);
        const clr = getAreaColor(ca, idx);
        const shortName = getShortName(ca);
        const reg = data.region_summaries[ca];
        const tot = reg ? reg.total_salmon : 0;

        const lbl = document.createElement('label');
        lbl.className = `flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium cursor-pointer select-none transition border ${
          isChecked 
            ? 'bg-slate-800 text-slate-100 border-slate-600 shadow-sm' 
            : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:bg-slate-800/50 hover:text-slate-300'
        }`;

        lbl.innerHTML = `
          <input type="checkbox" ${isChecked ? 'checked' : ''} class="rounded bg-slate-950 border-slate-700 text-blue-500 focus:ring-0 cursor-pointer" data-area="${ca}" />
          <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${clr}"></span>
          <span>${shortName}</span>
          <span class="text-[10px] text-slate-500">(${tot.toLocaleString()})</span>
        `;

        lbl.querySelector('input').addEventListener('change', (e) => {
          if (e.target.checked) selectedAreas.add(ca);
          else selectedAreas.delete(ca);
          renderAreaPills();
          updateDashboard();
        });

        pillsContainer.appendChild(lbl);
      });
    }

    document.getElementById('btnSelectAll').addEventListener('click', () => {
      data.catch_areas.forEach(ca => selectedAreas.add(ca));
      renderAreaPills();
      updateDashboard();
    });

    document.getElementById('btnClearAll').addEventListener('click', () => {
      selectedAreas.clear();
      renderAreaPills();
      updateDashboard();
    });

    document.getElementById('presetCentral').addEventListener('click', () => {
      selectedAreas.clear();
      selectedAreas.add('Area 9, Admiralty Inlet');
      selectedAreas.add('Area 10, Seattle-Bremerton area');
      selectedAreas.add('Area 11, Tacoma-Vashon Island');
      renderAreaPills();
      updateDashboard();
    });

    document.getElementById('presetStraits').addEventListener('click', () => {
      selectedAreas.clear();
      selectedAreas.add('Area 5, Sekiu and Pillar Point');
      selectedAreas.add('Area 6, East Juan de Fuca Strait');
      selectedAreas.add('Area 7, San Juan Islands');
      selectedAreas.add('Bellingham Bay');
      renderAreaPills();
      updateDashboard();
    });

    document.getElementById('presetHotspots').addEventListener('click', () => {
      selectedAreas.clear();
      selectedAreas.add('Area 5, Sekiu and Pillar Point');
      selectedAreas.add('Area 8-2, Ports Susan and Gardner');
      selectedAreas.add('Area 9, Admiralty Inlet');
      selectedAreas.add('Area 10, Seattle-Bremerton area');
      renderAreaPills();
      updateDashboard();
    });

    function fitQuadratic(points) {
      if (points.length < 3) {
        if (points.length === 2) {
          const m = (points[1].y - points[0].y) / (points[1].x - points[0].x);
          const b = points[0].y - m * points[0].x;
          return { c: b, b: m, a: 0, n: 2 };
        }
        return null;
      }
      const n = points.length;
      let sx = 0, sx2 = 0, sx3 = 0, sx4 = 0, sy = 0, sxy = 0, sx2y = 0;
      points.forEach(p => {
        const x = p.x, y = p.y;
        sx += x;
        sx2 += x * x;
        sx3 += x * x * x;
        sx4 += x * x * x * x;
        sy += y;
        sxy += x * y;
        sx2y += x * x * y;
      });

      const M = [
        [n, sx, sx2, sy],
        [sx, sx2, sx3, sxy],
        [sx2, sx3, sx4, sx2y]
      ];

      for (let i = 0; i < 3; i++) {
        let maxR = i;
        for (let r = i + 1; r < 3; r++) {
          if (Math.abs(M[r][i]) > Math.abs(M[maxR][i])) maxR = r;
        }
        const temp = M[i]; M[i] = M[maxR]; M[maxR] = temp;
        const pivot = M[i][i];
        if (Math.abs(pivot) < 1e-12) continue;
        for (let c = i; c <= 3; c++) M[i][c] /= pivot;
        for (let r = 0; r < 3; r++) {
          if (r !== i) {
            const factor = M[r][i];
            for (let c = i; c <= 3; c++) M[r][c] -= factor * M[i][c];
          }
        }
      }
      return { c: M[0][3], b: M[1][3], a: M[2][3], n };
    }

    function evalTrend(fit, x, maxCap) {
      if (!fit) return 0;
      let val = fit.c + fit.b * x + fit.a * (x * x);
      if (val < 0) val = 0;
      if (maxCap && val > maxCap) val = maxCap;
      return val;
    }

    function updateDashboard() {
      const speciesMode = speciesModeSelect.value;
      const metricMode = metricModeSelect.value;
      const displayMode = displayModeSelect.value;

      let totKings = 0, totCoho = 0, totAnglers = 0, totBoats = 0;

      selectedAreas.forEach(ca => {
        const reg = data.region_summaries[ca];
        if (reg) {
          totKings += reg.total_chinook;
          totCoho += reg.total_coho;
          totAnglers += reg.total_anglers;
          totBoats += reg.total_boats;
        }
      });

      const kingCpue = totAnglers > 0 ? (totKings / totAnglers).toFixed(2) : '0.00';
      const cohoCpue = totAnglers > 0 ? (totCoho / totAnglers).toFixed(2) : '0.00';

      document.getElementById('statKings').textContent = totKings.toLocaleString();
      document.getElementById('kingBadge').textContent = `${kingCpue} CPUE`;
      document.getElementById('statCoho').textContent = totCoho.toLocaleString();
      document.getElementById('cohoBadge').textContent = `${cohoCpue} CPUE`;
      document.getElementById('statAnglers').textContent = totAnglers.toLocaleString();
      document.getElementById('boatBadge').textContent = `${totBoats.toLocaleString()} Boats`;

      renderMainChart(speciesMode, metricMode, displayMode);
      renderRegionTable();
      renderRawTable();
    }

    function renderMainChart(speciesMode, metricMode, displayMode) {
      const canvas = document.getElementById('mainChartCanvas');
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const w = rect.width;
      const h = rect.height;
      const padL = 55, padR = 25, padT = 25, padB = 40;
      const cw = w - padL - padR;
      const ch = h - padT - padB;

      ctx.clearRect(0, 0, w, h);

      const numFactual = data.num_factual;
      const numTotal = data.all_dates.length;
      const activeAreasList = Array.from(selectedAreas);

      const legendContainer = document.getElementById('chartLegend');
      legendContainer.innerHTML = '';

      if (activeAreasList.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No areas selected. Please check one or more catch areas above.', w/2, h/2);
        document.getElementById('statForecastSummary').textContent = 'No Areas Selected';
        return;
      }

      function getX(i) {
        return padL + (i / (numTotal - 1)) * cw;
      }

      const xBoundary = getX(numFactual - 1);

      ctx.fillStyle = '#1e293b';
      ctx.fillRect(xBoundary, padT, padL + cw - xBoundary, ch);

      ctx.beginPath();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.moveTo(xBoundary, padT);
      ctx.lineTo(xBoundary, padT + ch);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#38bdf8';
      ctx.font = 'bold 10px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('🔮 14-DAY FUTURE FORECAST ➔', xBoundary + 8, padT + 14);

      let areaSeriesList = [];
      let globalMax = 0.1;

      activeAreasList.forEach((ca, idx) => {
        const reg = data.region_summaries[ca];
        if (!reg) return;

        const clr = getAreaColor(ca, idx);
        const shortName = getShortName(ca);

        const processSpecies = (spName, dailyVals, isDashed) => {
          let factualVals = [];
          let validPoints = [];

          for (let i = 0; i < numFactual; i++) {
            const rawVal = dailyVals[i] || 0;
            const a = reg.daily_anglers[i] || 0;
            const b = reg.daily_boats[i] || 0;

            let v = 0;
            if (metricMode === 'RAW') v = rawVal;
            else if (metricMode === 'CPUE_ANG') v = a > 0 ? rawVal / a : 0;
            else if (metricMode === 'CPUE_BOAT') v = b > 0 ? rawVal / b : 0;
            else if (metricMode === 'EFFORT') v = a;

            factualVals.push(v);
            if (a > 0) {
              validPoints.push({ x: i, y: v });
            }
          }

          const fit = fitQuadratic(validPoints);

          let trendVals = [];
          const maxCap = metricMode.startsWith('CPUE') ? (spName === 'Kings' ? 1.5 : 2.5) : null;
          for (let i = 0; i < numTotal; i++) {
            let tVal = evalTrend(fit, i, maxCap);
            trendVals.push(tVal);
          }

          const m = Math.max(...factualVals, ...trendVals);
          if (m > globalMax) globalMax = m;

          areaSeriesList.push({
            name: `${shortName} ${spName}`,
            color: clr,
            factualVals: factualVals,
            trendVals: trendVals,
            fit: fit,
            isDashed: isDashed
          });
        };

        if (speciesMode === 'COHO') {
          processSpecies('Coho', reg.daily_coho, false);
        } else if (speciesMode === 'CHINOOK') {
          processSpecies('Kings', reg.daily_chinook, false);
        } else if (speciesMode === 'DUAL') {
          processSpecies('Kings', reg.daily_chinook, true);
          processSpecies('Coho', reg.daily_coho, false);
        }
      });

      globalMax = globalMax * 1.15;

      function getY(v) {
        return padT + ch - (v / globalMax) * ch;
      }

      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'right';

      for (let i = 0; i <= 4; i++) {
        const val = (globalMax / 4) * i;
        const y = getY(val);
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.moveTo(padL, y);
        ctx.lineTo(w - padR, y);
        ctx.stroke();
        ctx.setLineDash([]);
        const displayVal = metricMode.startsWith('CPUE') ? val.toFixed(2) : Math.round(val);
        ctx.fillText(displayVal, padL - 8, y + 4);
      }

      ctx.textAlign = 'center';
      data.all_dates.forEach((lbl, idx) => {
        if (idx % 4 === 0 || idx === numFactual - 1 || idx === numTotal - 1) {
          const x = getX(idx);
          const isFuture = idx >= numFactual;
          ctx.fillStyle = isFuture ? '#38bdf8' : '#94a3b8';
          ctx.fillText(lbl, x, h - padB + 18);
        }
      });

      areaSeriesList.forEach(s => {
        if (displayMode === 'BOTH' || displayMode === 'TREND') {
          ctx.beginPath();
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = s.color;
          ctx.setLineDash([4, 4]);

          s.trendVals.forEach((v, idx) => {
            const x = getX(idx);
            const y = getY(v);
            if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.stroke();
          ctx.setLineDash([]);

          const xEnd = getX(numTotal - 1);
          const yEnd = getY(s.trendVals[numTotal - 1]);
          ctx.fillStyle = s.color;
          ctx.beginPath();
          ctx.arc(xEnd, yEnd, 4, 0, Math.PI * 2);
          ctx.fill();
        }

        if (displayMode === 'BOTH' || displayMode === 'ACTUAL') {
          ctx.beginPath();
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = s.color;
          if (s.isDashed) ctx.setLineDash([6, 4]); else ctx.setLineDash([]);

          s.factualVals.forEach((v, idx) => {
            const x = getX(idx);
            const y = getY(v);
            if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.stroke();
          ctx.setLineDash([]);

          s.factualVals.forEach((v, idx) => {
            if (v > (metricMode.startsWith('CPUE') ? 0.20 : 25)) {
              const x = getX(idx);
              const y = getY(v);
              ctx.fillStyle = s.color;
              ctx.beginPath();
              ctx.arc(x, y, 3.5, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }
      });

      areaSeriesList.forEach(s => {
        const item = document.createElement('span');
        item.className = 'flex items-center gap-1.5';
        item.innerHTML = `
          <span class="w-3 h-2.5 rounded-sm inline-block" style="background:${s.color}; opacity:${s.isDashed ? '0.7' : '1.0'}; border:${s.isDashed ? '1px dashed #fff' : 'none'}"></span>
          <span class="text-slate-200">${s.name}</span>
          ${displayMode === 'BOTH' ? '<span class="text-[10px] text-yellow-300 font-mono">(dotted = forecast)</span>' : ''}
        `;
        legendContainer.appendChild(item);
      });

      if (areaSeriesList.length > 0) {
        const topSeries = areaSeriesList[0];
        const futurePeakVal = Math.max(...topSeries.trendVals.slice(numFactual));
        document.getElementById('statForecastSummary').textContent = `${topSeries.name} ➔ ${futurePeakVal.toFixed(2)} ${metricMode.startsWith('CPUE') ? 'CPUE' : 'Fish'}`;
      }
    }

    function renderRegionTable() {
      const tbody = document.getElementById('regionTableBody');
      tbody.innerHTML = '';

      const activeList = Array.from(selectedAreas);
      if (activeList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-4 text-center text-slate-500 font-sans">No catch areas selected. Check areas above to view performance.</td></tr>';
        return;
      }

      activeList.forEach(ca => {
        const r = data.region_summaries[ca];
        if (!r) return;

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/50 transition-colors';

        const cohoDiff = r.late_coho - r.early_coho;
        let cohoBadge = '<span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">➡️ Steady</span>';
        if (r.late_coho > 50 && cohoDiff > 50) {
          cohoBadge = '<span class="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">🔥 Surging</span>';
        } else if (r.late_coho < r.early_coho - 20) {
          cohoBadge = '<span class="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-300 font-medium">❄️ Cooling</span>';
        }

        let kingBadge = '<span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">Closed/Steady</span>';
        if (r.late_chinook > 20 && r.late_chinook / r.late_anglers >= 0.15) {
          kingBadge = '<span class="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">👑 Active Open</span>';
        } else if (r.early_chinook > 100 && r.late_chinook < 10) {
          kingBadge = '<span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-500">Closed Season</span>';
        }

        tr.innerHTML = `
          <td class="px-4 py-2.5 font-sans font-semibold text-slate-100 flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${getAreaColor(ca, 0)}"></span>
            ${ca}
          </td>
          <td class="px-4 py-2.5 text-right font-bold text-amber-400">${r.total_chinook.toLocaleString()}</td>
          <td class="px-4 py-2.5 text-right font-bold text-cyan-400">${r.total_coho.toLocaleString()}</td>
          <td class="px-4 py-2.5 text-right font-bold text-slate-100">${r.total_salmon.toLocaleString()}</td>
          <td class="px-4 py-2.5 text-right text-slate-400">${r.total_anglers.toLocaleString()}</td>
          <td class="px-4 py-2.5 text-right font-bold text-amber-400">${r.king_cpue.toFixed(2)}</td>
          <td class="px-4 py-2.5 text-right font-bold text-cyan-400">${r.coho_cpue.toFixed(2)}</td>
          <td class="px-4 py-2.5 text-center font-sans">${cohoBadge}</td>
          <td class="px-4 py-2.5 text-center font-sans">${kingBadge}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function renderRawTable() {
      const tbody = document.getElementById('rawTableBody');
      tbody.innerHTML = '';
      const query = searchInput.value.toLowerCase().trim();

      const filtered = data.raw_records.filter(r => {
        if (selectedAreas.size > 0 && !selectedAreas.has(r.catch_area)) return false;
        if (!query) return true;
        return (r.date && r.date.toLowerCase().includes(query)) ||
               (r.ramp && r.ramp.toLowerCase().includes(query)) ||
               (r.catch_area && r.catch_area.toLowerCase().includes(query));
      });

      document.getElementById('recordCount').textContent = `Showing ${filtered.length} matching sampling records`;

      filtered.slice(0, 100).forEach(r => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/50 transition-colors font-mono';

        const cpue = r.anglers > 0 ? ((r.chinook + r.coho) / r.anglers).toFixed(2) : '0.00';

        tr.innerHTML = `
          <td class="px-4 py-2 text-slate-300 font-sans">${r.date}</td>
          <td class="px-4 py-2 text-slate-200 font-sans">${r.ramp}</td>
          <td class="px-4 py-2 text-slate-400 text-xs font-sans">${r.catch_area}</td>
          <td class="px-4 py-2 text-right text-slate-300">${r.anglers}</td>
          <td class="px-4 py-2 text-right text-slate-400">${r.interviews}</td>
          <td class="px-4 py-2 text-right font-bold text-amber-400">${r.chinook}</td>
          <td class="px-4 py-2 text-right font-bold text-cyan-400">${r.coho}</td>
          <td class="px-4 py-2 text-right font-bold text-emerald-400">${cpue}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    speciesModeSelect.addEventListener('change', updateDashboard);
    metricModeSelect.addEventListener('change', updateDashboard);
    displayModeSelect.addEventListener('change', updateDashboard);
    searchInput.addEventListener('input', renderRawTable);
    window.addEventListener('resize', updateDashboard);

    renderAreaPills();
    updateDashboard();
  </script>
</body>
</html>
"""

    final_html = html_code.replace("DATA_PLACEHOLDER", payload_json_str)

    os.makedirs(os.path.dirname(os.path.abspath(output_html)), exist_ok=True)
    with open(output_html, "w") as f:
        f.write(final_html)

    print(f"Generated {output_html} successfully!")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "../data/creel_data_2026_summer.json")
    html_path = os.path.join(script_dir, "../index.html")
    svg_path = os.path.join(script_dir, "../assets/coho_full_season_trends.svg")
    build_dashboard(data_path, html_path, svg_path)
