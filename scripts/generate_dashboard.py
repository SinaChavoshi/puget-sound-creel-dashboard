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
from datetime import datetime, timedelta, timezone

def build_dashboard(data_file="../data/creel_data_2026_summer.json", output_html="../index.html", output_svg="../assets/coho_full_season_trends.svg"):
    with open(data_file, "r") as f:
        raw_data = json.load(f)

    def parse_date(d_str):
        return datetime.strptime(d_str, "%b %d, %Y")

    # Season window starts July 19; x-axis is continuous calendar days so
    # unsampled days don't compress time or distort the trend fit.
    SEASON_START = datetime(2026, 7, 19)
    FORECAST_DAYS = 14
    summer_data = [r for r in raw_data if r.get("date") and parse_date(r["date"]) >= SEASON_START]
    summer_data.sort(key=lambda r: (parse_date(r["date"]), r["ramp"]), reverse=True)
    last_dt = max(parse_date(r["date"]) for r in summer_data)
    cal_days = [SEASON_START + timedelta(days=i) for i in range((last_dt - SEASON_START).days + 1)]
    cal_str = [d.strftime("%b %d, %Y") for d in cal_days]
    future_days = [last_dt + timedelta(days=i) for i in range(1, FORECAST_DAYS + 1)]
    factual_date_labels = [d.strftime("%b %-d") for d in cal_days]
    all_date_labels = factual_date_labels + [d.strftime("%b %-d") for d in future_days]
    all_catch_areas = sorted(set(r["catch_area"] for r in summer_data))

    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    by_date = {}
    for r in summer_data:
        key = parse_date(r["date"]).strftime("%b %d, %Y")
        m = matrix[key][r["catch_area"]]
        for f in ("chinook", "coho", "chum", "pink", "sockeye", "lingcod", "halibut", "anglers"):
            m[f] += r[f]
        m["boats"] += r["interviews"]

    n = len(cal_str)
    def wsum(ca, field, lo, hi):
        return sum(matrix[cal_str[i]][ca][field] for i in range(max(lo, 0), min(hi, n)))
    def cpue(f, a):
        return round(f / a, 3) if a > 0 else None

    region_summaries = {}
    for ca in all_catch_areas:
        tot = {f: wsum(ca, f, 0, n) for f in ("chinook", "coho", "anglers", "boats")}
        r7 = {f: wsum(ca, f, n - 7, n) for f in ("chinook", "coho", "anglers")}
        p7 = {f: wsum(ca, f, n - 14, n - 7) for f in ("chinook", "coho", "anglers")}
        r14 = {f: wsum(ca, f, n - 14, n) for f in ("chinook", "anglers")}
        region_summaries[ca] = {
            "total_chinook": tot["chinook"], "total_coho": tot["coho"],
            "total_salmon": tot["chinook"] + tot["coho"],
            "total_anglers": tot["anglers"], "total_boats": tot["boats"],
            "king_cpue": cpue(tot["chinook"], tot["anglers"]) or 0.0,
            "coho_cpue": cpue(tot["coho"], tot["anglers"]) or 0.0,
            "recent_anglers": r7["anglers"], "prior_anglers": p7["anglers"],
            "recent_coho_cpue": cpue(r7["coho"], r7["anglers"]),
            "prior_coho_cpue": cpue(p7["coho"], p7["anglers"]),
            "recent14_chinook": r14["chinook"], "recent14_anglers": r14["anglers"],
            "recent14_king_cpue": cpue(r14["chinook"], r14["anglers"]),
            "daily_chinook": [matrix[d][ca]["chinook"] for d in cal_str],
            "daily_coho": [matrix[d][ca]["coho"] for d in cal_str],
            "daily_anglers": [matrix[d][ca]["anglers"] for d in cal_str],
            "daily_boats": [matrix[d][ca]["boats"] for d in cal_str],
        }

    payload = {
        "factual_dates": factual_date_labels,
        "all_dates": all_date_labels,
        "num_factual": n,
        "num_future": FORECAST_DAYS,
        "catch_areas": all_catch_areas,
        "region_summaries": region_summaries,
        "raw_records": [{k: r[k] for k in ("date", "ramp", "catch_area", "interviews", "anglers", "chinook", "coho")} for r in summer_data],
        "data_through": last_dt.strftime("%b %-d, %Y"),
        "season_start": SEASON_START.strftime("%b %-d, %Y"),
        "generated_at": datetime.now(timezone.utc).strftime("%b %-d, %Y %H:%M UTC"),
        "num_records": len(summer_data),
    }

    payload_json_str = json.dumps(payload)

    # HTML template lives next to this script for easier editing
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")
    with open(template_path, "r") as f:
        html_code = f.read()

    final_html = html_code.replace("DATA_PLACEHOLDER", payload_json_str)

    os.makedirs(os.path.dirname(os.path.abspath(output_html)), exist_ok=True)
    with open(output_html, "w") as f:
        f.write(final_html)

    print(f"Generated {output_html} successfully!")

    # ----------------------------------------------------
    # Generate Updated SVG Chart (Coho Season Trends)
    # ----------------------------------------------------
    top_coho_regions = [
        'Area 8-2, Ports Susan and Gardner',
        'Area 10, Seattle-Bremerton area',
        'Area 9, Admiralty Inlet',
        'Area 5, Sekiu and Pillar Point',
        'Area 6, East Juan de Fuca Strait',
        'Area 7, San Juan Islands',
        'Area 11, Tacoma-Vashon Island'
    ]

    short_name_map = {
        'Area 8-2, Ports Susan and Gardner': 'Area 8-2 (Ports Susan/Everett)',
        'Area 10, Seattle-Bremerton area': 'Area 10 (Seattle-Bremerton)',
        'Area 9, Admiralty Inlet': 'Area 9 (Admiralty Inlet)',
        'Area 5, Sekiu and Pillar Point': 'Area 5 (Sekiu / Neah Bay)',
        'Area 6, East Juan de Fuca Strait': 'Area 6 (East Juan de Fuca)',
        'Area 7, San Juan Islands': 'Area 7 (San Juan Islands)',
        'Area 11, Tacoma-Vashon Island': 'Area 11 (Tacoma-Vashon)'
    }

    color_map = {
        'Area 8-2, Ports Susan and Gardner': '#10b981',
        'Area 10, Seattle-Bremerton area': '#3b82f6',
        'Area 9, Admiralty Inlet': '#f59e0b',
        'Area 5, Sekiu and Pillar Point': '#ef4444',
        'Area 6, East Juan de Fuca Strait': '#eab308',
        'Area 7, San Juan Islands': '#8b5cf6',
        'Area 11, Tacoma-Vashon Island': '#ec4899'
    }

    svg_w = 980
    svg_h = 490
    margin_l = 65
    margin_r = 240
    margin_t = 65
    margin_b = 60

    cw = svg_w - margin_l - margin_r
    ch = svg_h - margin_t - margin_b

    num_pts = len(factual_date_labels)
    x_step = cw / (num_pts - 1)

    max_val = max([region_summaries[ca]['daily_coho'][i] for ca in top_coho_regions if ca in region_summaries for i in range(num_pts)] + [1])

    def get_x(i):
        return margin_l + i * x_step

    def get_y(v):
        return margin_t + ch - (v / (max_val * 1.15)) * ch

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="background-color: #0f172a; font-family: system-ui, sans-serif;">')

    svg.append(f'<text x="{svg_w/2}" y="26" text-anchor="middle" fill="#f8fafc" font-size="18" font-weight="bold">Puget Sound Coho Salmon Daily Landings ({factual_date_labels[0]} – {factual_date_labels[-1]}, 2026)</text>')
    svg.append(f'<text x="{svg_w/2}" y="45" text-anchor="middle" fill="#38bdf8" font-size="12">WDFW creel data through {factual_date_labels[-1]} • unsampled days skipped</text>')

    # Highlight September data window
    sep_start_idx = next((i for i, lbl in enumerate(factual_date_labels) if 'Sep' in lbl), None)
    if sep_start_idx is not None:
        x_split = get_x(sep_start_idx)
        svg.append(f'<rect x="{x_split}" y="{margin_t}" width="{svg_w - margin_r - x_split}" height="{ch}" fill="#1e293b" opacity="0.6" />')
        svg.append(f'<line x1="{x_split}" y1="{margin_t}" x2="{x_split}" y2="{margin_t + ch}" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4,4" />')
        svg.append(f'<text x="{x_split + 8}" y="{margin_t + 16}" fill="#38bdf8" font-size="10" font-weight="bold">SEPTEMBER</text>')

    # Y-Grid
    for i in range(5):
        v_tick = round((max_val * 1.15 / 4) * i)
        y_pos = get_y(v_tick)
        svg.append(f'<line x1="{margin_l}" y1="{y_pos}" x2="{svg_w - margin_r}" y2="{y_pos}" stroke="#334155" stroke-dasharray="3,3" />')
        svg.append(f'<text x="{margin_l - 8}" y="{y_pos + 4}" text-anchor="end" fill="#94a3b8" font-size="11">{v_tick}</text>')

    # X-Labels
    for i, lbl in enumerate(factual_date_labels):
        if i % 7 == 0 or i == num_pts - 1:
            x_pos = get_x(i)
            svg.append(f'<text x="{x_pos}" y="{svg_h - 20}" text-anchor="middle" fill="{ "#38bdf8" if "Sep" in lbl else "#94a3b8" }" font-size="10">{lbl}</text>')

    # Lines
    for ca in top_coho_regions:
        if ca not in region_summaries:
            continue
        clr = color_map[ca]
        vals = region_summaries[ca]['daily_coho']
        angs = region_summaries[ca]['daily_anglers']
        pts = " ".join([f"{get_x(i):.1f},{get_y(v):.1f}" for i, v in enumerate(vals) if angs[i] > 0])
        svg.append(f'<polyline fill="none" stroke="{clr}" stroke-width="2.5" points="{pts}" />')
        for i, v in enumerate(vals):
            if v >= 100:
                svg.append(f'<circle cx="{get_x(i):.1f}" cy="{get_y(v):.1f}" r="3.5" fill="{clr}" />')

    # Legend
    y_leg_start = 65
    for idx, ca in enumerate(top_coho_regions):
        if ca not in region_summaries:
            continue
        clr = color_map[ca]
        sname = short_name_map[ca]
        tot = region_summaries[ca]['total_coho']
        y_pos = y_leg_start + idx * 24
        svg.append(f'<rect x="{svg_w - margin_r + 15}" y="{y_pos}" width="12" height="12" fill="{clr}" rx="2" />')
        svg.append(f'<text x="{svg_w - margin_r + 32}" y="{y_pos + 10}" fill="#f8fafc" font-size="11">{sname} ({tot:,})</text>')

    svg.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(output_svg)), exist_ok=True)
    with open(output_svg, "w") as f:
        f.write("\n".join(svg))

    print(f"Generated {output_svg} successfully!")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "../data/creel_data_2026_summer.json")
    html_path = os.path.join(script_dir, "../index.html")
    svg_path = os.path.join(script_dir, "../assets/coho_full_season_trends.svg")
    build_dashboard(data_path, html_path, svg_path)
