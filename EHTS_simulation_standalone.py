# -*- coding: utf-8 -*-
"""
Standalone EHTS dashboard generator.

This version removes the original project dependencies:
- no MARL package
- no Env.environment / EH_Env
- no torch / tensorboard

It reads a simulation-history CSV and writes the dynamic HTML dashboard.

Usage:
    python EHTS_simulation_standalone.py
    python EHTS_simulation_standalone.py path/to/sim_history.csv

Optional environment variables:
    EHTS_DT_HOURS=0.25
    EHTS_OUTPUT_HTML=path/to/output.html
"""

import os
import sys
import json
import ast
from html import escape
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(THIS_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

# Simulation timestep in hours. Change this if your CSV was recorded with a different dt.
DT_HOURS = float(os.environ.get("EHTS_DT_HOURS", "0.25"))

# ============================================================
# Integrated Energy Station Visualization Dashboard
# ============================================================

DASHBOARD_STORY_HTML = """
    <section class="station-story" aria-label="Multi-energy station concept diagram">
      <button class="station-story__toggle" type="button" aria-expanded="true">Hide station diagram</button>
      <div class="station-story__inner">
        <div class="station-story__copy">
          <h1>CLEETS - EHTS: Electricity- Hydrogen-Transport-System</h1>
          <p>
            Low-energy electric and hydrogen vehicles arrive from the left. The station coordinates grid, PV,
            battery, electrolyzer, hydrogen tank, chargers, and refuelers, then vehicles leave with sufficient energy.
          </p>
        </div>
        <div class="station-story__canvas">
          <svg class="station-story__svg" viewBox="0 0 1180 360" role="img" aria-labelledby="story-title story-desc">
            <title id="story-title">Vehicle energy replenishment flow</title>
            <desc id="story-desc">
              Low-energy electric and hydrogen vehicles enter the multi-energy station, are replenished, and leave
              with sufficient electric charge or hydrogen fuel. A downward arrow links the station to the dashboard.
            </desc>
            <defs>
              <marker id="arrowhead" markerWidth="26" markerHeight="26" refX="24" refY="13" orient="auto" markerUnits="userSpaceOnUse">
                <path d="M 0 0 L 26 13 L 0 26 z" fill="#2f5f8f"></path>
              </marker>
              <marker id="down-arrowhead" markerWidth="24" markerHeight="24" refX="22" refY="12" orient="auto" markerUnits="userSpaceOnUse">
                <path d="M 0 0 L 24 12 L 0 24 z" fill="#315f3d"></path>
              </marker>
              <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="150%">
                <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#1f2937" flood-opacity="0.16"></feDropShadow>
              </filter>
              <linearGradient id="station-gradient" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0" stop-color="#ffffff"></stop>
                <stop offset="1" stop-color="#e7f4ee"></stop>
              </linearGradient>
            </defs>

            <rect x="20" y="42" width="1140" height="220" rx="24" fill="#f8fafc" stroke="#d8e1ea"></rect>
            <line class="flow-line flow-line--incoming" x1="72" y1="178" x2="474" y2="178" marker-end="url(#arrowhead)"></line>
            <line class="flow-line flow-line--station-out" x1="704" y1="178" x2="774" y2="178" marker-end="url(#arrowhead)"></line>
            <line class="flow-line flow-line--departing" x1="914" y1="178" x2="950" y2="178"></line>
            <line class="flow-line flow-line--departing" x1="1100" y1="178" x2="1140" y2="178" marker-end="url(#arrowhead)"></line>
            <line x1="590" y1="248" x2="590" y2="306" stroke="#315f3d" stroke-width="7" stroke-linecap="round" marker-end="url(#down-arrowhead)"></line>

            <text x="185" y="78" text-anchor="middle" class="story-label story-label--muted">Arriving low-energy vehicles</text>
            <text x="990" y="78" text-anchor="middle" class="story-label story-label--muted">Departing energy-sufficient vehicles</text>
            <text x="590" y="348" text-anchor="middle" class="story-label story-label--dashboard">Operational dashboard below</text>

            <g class="vehicle vehicle--incoming" transform="translate(80 112)">
              <animateTransform attributeName="transform" type="translate" additive="sum" values="-8 0; 8 0; -8 0" dur="2.8s" repeatCount="indefinite"></animateTransform>
              <rect x="0" y="30" width="128" height="50" rx="14" fill="#dfe7ef" stroke="#738094" stroke-width="2"></rect>
              <path d="M 24 30 L 48 8 H 87 L 111 30 Z" fill="#eef4f9" stroke="#738094" stroke-width="2"></path>
              <circle cx="32" cy="84" r="12" fill="#273142"></circle>
              <circle cx="98" cy="84" r="12" fill="#273142"></circle>
              <rect x="22" y="48" width="52" height="13" rx="4" fill="#ffffff" stroke="#9aa6b2"></rect>
              <rect x="22" y="48" width="16" height="13" rx="4" fill="#d95745"></rect>
              <text x="64" y="115" text-anchor="middle" class="story-small">EV low SOC</text>
            </g>
            <g class="vehicle vehicle--incoming" transform="translate(250 114)">
              <animateTransform attributeName="transform" type="translate" additive="sum" values="-6 0; 10 0; -6 0" dur="3.1s" repeatCount="indefinite"></animateTransform>
              <rect x="0" y="24" width="138" height="58" rx="16" fill="#e0e8ef" stroke="#738094" stroke-width="2"></rect>
              <rect x="70" y="3" width="44" height="28" rx="8" fill="#eef4f9" stroke="#738094" stroke-width="2"></rect>
              <circle cx="36" cy="86" r="12" fill="#273142"></circle>
              <circle cx="105" cy="86" r="12" fill="#273142"></circle>
              <path d="M 24 52 H 68" stroke="#d95745" stroke-width="8" stroke-linecap="round"></path>
              <text x="70" y="116" text-anchor="middle" class="story-small">HV low H2</text>
            </g>

            <g class="station-node" filter="url(#soft-shadow)">
              <rect x="492" y="72" width="196" height="176" rx="18" fill="url(#station-gradient)" stroke="#5d8a6a" stroke-width="3"></rect>
              <rect x="526" y="126" width="128" height="98" rx="10" fill="#ffffff" stroke="#8eb29a" stroke-width="2"></rect>
              <path d="M 520 126 L 590 88 L 660 126 Z" fill="#6aa77a" stroke="#477653" stroke-width="3"></path>
              <text x="590" y="114" text-anchor="middle" class="station-title">Multi-Energy</text>
              <text x="590" y="135" text-anchor="middle" class="station-title">Station</text>

              <g transform="translate(514 151)">
                <rect x="0" y="0" width="72" height="28" rx="7" fill="#e8f2ff" stroke="#5b8cc0"></rect>
                <text x="36" y="19" text-anchor="middle" class="station-chip">EV charge</text>
              </g>
              <g transform="translate(594 151)">
                <rect x="0" y="0" width="72" height="28" rx="7" fill="#e9f7ef" stroke="#59a86b"></rect>
                <text x="36" y="19" text-anchor="middle" class="station-chip">H2 refuel</text>
              </g>
              <g transform="translate(514 187)">
                <rect x="0" y="0" width="92" height="28" rx="7" fill="#fff4de" stroke="#d59b39"></rect>
                <text x="46" y="19" text-anchor="middle" class="station-chip">PV/Grid/Pipeline</text>
              </g>
              <g transform="translate(614 187)">
                <rect x="0" y="0" width="72" height="28" rx="7" fill="#f0ecff" stroke="#8a73c7"></rect>
                <text x="36" y="19" text-anchor="middle" class="station-chip">Storage</text>
              </g>
            </g>

            <g class="vehicle vehicle--outgoing" transform="translate(790 112)">
              <animateTransform attributeName="transform" type="translate" additive="sum" values="-6 0; 10 0; -6 0" dur="2.7s" repeatCount="indefinite"></animateTransform>
              <rect x="0" y="30" width="128" height="50" rx="14" fill="#dff0e7" stroke="#498760" stroke-width="2"></rect>
              <path d="M 24 30 L 48 8 H 87 L 111 30 Z" fill="#f2fbf5" stroke="#498760" stroke-width="2"></path>
              <circle cx="32" cy="84" r="12" fill="#273142"></circle>
              <circle cx="98" cy="84" r="12" fill="#273142"></circle>
              <rect x="22" y="48" width="52" height="13" rx="4" fill="#ffffff" stroke="#75a985"></rect>
              <rect x="22" y="48" width="52" height="13" rx="4" fill="#2eaf61"></rect>
              <text x="64" y="115" text-anchor="middle" class="story-small">EV charged</text>
            </g>
            <g class="vehicle vehicle--outgoing" transform="translate(960 114)">
              <animateTransform attributeName="transform" type="translate" additive="sum" values="-5 0; 9 0; -5 0" dur="3s" repeatCount="indefinite"></animateTransform>
              <rect x="0" y="24" width="138" height="58" rx="16" fill="#dff0e7" stroke="#498760" stroke-width="2"></rect>
              <rect x="70" y="3" width="44" height="28" rx="8" fill="#f2fbf5" stroke="#498760" stroke-width="2"></rect>
              <circle cx="36" cy="86" r="12" fill="#273142"></circle>
              <circle cx="105" cy="86" r="12" fill="#273142"></circle>
              <path d="M 24 52 H 96" stroke="#2eaf61" stroke-width="8" stroke-linecap="round"></path>
              <text x="70" y="116" text-anchor="middle" class="story-small">HV refueled</text>
            </g>
          </svg>
        </div>
        <div class="station-story__mobile-flow" aria-hidden="true">
          <div class="mobile-flow__node mobile-flow__node--incoming">
            <strong>Arriving low-energy vehicles</strong>
            <span>EV low SOC</span>
            <span>HV low H2</span>
          </div>
          <div class="mobile-flow__arrow">&darr;</div>
          <div class="mobile-flow__node mobile-flow__node--station">
            <strong>Multi-Energy Station</strong>
            <span>EV charge | H2 refuel</span>
            <span>PV/Grid/Pipeline | Storage</span>
          </div>
          <div class="mobile-flow__arrow">&darr;</div>
          <div class="mobile-flow__node mobile-flow__node--outgoing">
            <strong>Departing energy-sufficient vehicles</strong>
            <span>EV charged</span>
            <span>HV refueled</span>
          </div>
          <div class="mobile-flow__arrow mobile-flow__arrow--dashboard">&darr;</div>
          <div class="mobile-flow__dashboard">Operational dashboard below</div>
        </div>
      </div>
    </section>
"""


DASHBOARD_SHELL_CSS = """
html,
body {
  margin: 0;
  background: #f4f7fb;
  color: #172033;
  font-family: Arial, Helvetica, sans-serif;
  overflow-x: hidden;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

.dashboard-page {
  min-height: 100vh;
}

.station-story {
  background: #ffffff;
  border-bottom: 1px solid #dbe4ee;
  padding: 24px 18px 18px;
  position: relative;
}

.station-story__toggle {
  position: absolute;
  top: 16px;
  right: 28px;
  z-index: 2;
  border: 1px solid #b8c6d6;
  border-radius: 6px;
  background: #ffffff;
  color: #253348;
  cursor: pointer;
  font-size: 12px;
  line-height: 1.15;
  padding: 7px 10px;
}

.station-story.is-collapsed {
  padding: 12px 18px;
}

.station-story.is-collapsed .station-story__inner {
  display: none;
}

.station-story__inner {
  max-width: 1560px;
  width: calc(100vw - 72px);
  margin: 0 auto;
}

.station-story__copy {
  display: grid;
  grid-template-columns: minmax(420px, 0.52fr) minmax(340px, 0.48fr);
  gap: 28px;
  align-items: end;
  margin-bottom: 14px;
  padding-right: 180px;
}

.station-story__copy h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.15;
  font-weight: 700;
  letter-spacing: 0;
}

.station-story__copy p {
  margin: 0;
  color: #4b5b6b;
  font-size: 15px;
  line-height: 1.55;
}

.station-story__canvas {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overscroll-behavior-x: contain;
}

.station-story__svg {
  display: block;
  width: 100%;
  min-width: 820px;
  height: auto;
}

.station-story__mobile-flow {
  display: none;
}

.mobile-flow__node {
  border: 1px solid #bfd0dc;
  border-radius: 8px;
  padding: 12px;
  background: #f8fafc;
}

.mobile-flow__node strong,
.mobile-flow__node span,
.mobile-flow__dashboard {
  display: block;
  overflow-wrap: anywhere;
}

.mobile-flow__node strong {
  margin-bottom: 8px;
  color: #243242;
  font-size: 15px;
  line-height: 1.25;
}

.mobile-flow__node span {
  color: #4b5b6b;
  font-size: 13px;
  line-height: 1.35;
}

.mobile-flow__node--incoming {
  border-color: #c8d5e2;
  background: #f4f8fc;
}

.mobile-flow__node--station {
  border-color: #76a683;
  background: #eff8f2;
}

.mobile-flow__node--outgoing {
  border-color: #86b995;
  background: #f0fbf4;
}

.mobile-flow__arrow {
  color: #315f3d;
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}

.mobile-flow__dashboard {
  color: #315f3d;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.3;
  text-align: center;
}

.story-label {
  fill: #253348;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0;
}

.story-label--muted {
  fill: #4b5b6b;
}

.story-label--dashboard {
  fill: #315f3d;
  font-size: 18px;
}

.story-small {
  fill: #253348;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0;
}

.station-title {
  fill: #1f3d2b;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0;
}

.station-chip {
  fill: #243242;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0;
}

.flow-line {
  stroke: #2f5f8f;
  stroke-width: 7;
  stroke-linecap: round;
  stroke-dasharray: 16 13;
  animation: flow-dash 1.2s linear infinite;
}

.flow-line--station-out {
  animation-delay: -0.35s;
}

.flow-line--departing {
  animation-delay: -0.7s;
}

@keyframes flow-dash {
  to {
    stroke-dashoffset: -58;
  }
}

.week-summary {
  background: #ffffff;
  border-bottom: 1px solid #dbe4ee;
  padding: 16px 24px 18px;
}

.week-summary__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
  max-width: 1560px;
  margin: 0 auto;
}

.week-summary__card {
  min-height: 72px;
  border: 1px solid #d8e1ea;
  border-radius: 8px;
  background: #f8fafc;
  padding: 10px 12px;
}

.week-summary__label {
  color: #536172;
  font-size: 12px;
  line-height: 1.25;
}

.week-summary__value {
  margin-top: 7px;
  color: #172033;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.1;
}

.week-summary__sub {
  margin-top: 4px;
  color: #697789;
  font-size: 12px;
  line-height: 1.25;
}

.plot-area {
  max-width: none;
  width: 100%;
  margin: 0 auto;
  padding: 8px 24px 36px;
}

.panel-toggle-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin: 10px auto 8px;
  padding: 0 8px;
  font-family: Arial, sans-serif;
}

.panel-toggle {
  border: 1px solid #b8c6d6;
  border-radius: 6px;
  background: #ffffff;
  color: #253348;
  cursor: pointer;
  font-size: 12px;
  line-height: 1.15;
  padding: 7px 9px;
}

.panel-toggle[aria-pressed="false"] {
  background: #e9eef5;
  color: #697789;
  text-decoration: line-through;
}

@media (max-width: 760px) {
  .station-story {
    padding: 18px 12px 14px;
  }

  .station-story__toggle {
    position: static;
    display: block;
    margin-left: auto;
  }

  .station-story.is-collapsed {
    padding: 10px 12px;
  }

  .station-story__copy {
    grid-template-columns: 1fr;
    gap: 8px;
    padding-right: 0;
  }

  .station-story__inner {
    width: calc(100vw - 24px);
  }

  .station-story__copy h1 {
    font-size: 24px;
  }

  .station-story__copy p {
    font-size: 14px;
    max-width: min(100%, 38ch);
    overflow-wrap: anywhere;
  }

  .station-story__canvas {
    display: none;
  }

  .station-story__mobile-flow {
    display: grid;
    gap: 8px;
    margin-top: 14px;
  }

  .station-story__svg {
    width: 820px;
  }

  .plot-area {
    width: calc(100vw - 8px);
    padding: 4px 4px 28px;
    overflow-x: auto;
  }

  .week-summary {
    padding: 12px 10px 14px;
  }

  .week-summary__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .week-summary__value {
    font-size: 16px;
  }
}
"""


def write_dashboard_html(fig, output_path: str, page_title: str, post_script: str = None):
    """Write a Plotly figure with the station concept diagram above it."""
    plot_html = fig.to_html(
        include_plotlyjs=True,
        full_html=False,
        post_script=post_script,
        config={"responsive": True},
    )
    safe_title = escape(page_title, quote=True)
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
{DASHBOARD_SHELL_CSS}
  </style>
</head>
<body>
  <main class="dashboard-page">
{DASHBOARD_STORY_HTML}
    <section class="week-summary" aria-label="Current week operational summary">
      <div class="week-summary__grid" id="week-summary-grid"></div>
    </section>
    <section class="plot-area" aria-label="{safe_title}">
{plot_html}
    </section>
  </main>
  <script>
    (function () {{
      function bindStationStoryToggle() {{
        var story = document.querySelector('.station-story');
        var toggle = document.querySelector('.station-story__toggle');
        if (!story || !toggle || toggle.dataset.bound === 'true') return;
        toggle.dataset.bound = 'true';
        toggle.addEventListener('click', function () {{
          var collapsed = story.classList.toggle('is-collapsed');
          toggle.setAttribute('aria-expanded', String(!collapsed));
          toggle.textContent = collapsed ? 'Show station diagram' : 'Hide station diagram';
          var plot = document.querySelector('.plotly-graph-div');
          if (window.Plotly && plot) setTimeout(function () {{ Plotly.Plots.resize(plot); }}, 0);
        }});
      }}
      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', bindStationStoryToggle);
      }} else {{
        bindStationStoryToggle();
      }}
    }}());
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_doc)

# ============================================================
# Load environment and history data
# ============================================================

# Load simulation history. By default, expects the CSV under ./runs/.
DEFAULT_SIM_HISTORY_CSV = os.path.join(
    RUNS_DIR,
    "sim_history_exp1_ess_td3_step_real_460800.csv",
)
SIM_HISTORY_CSV = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SIM_HISTORY_CSV

if not os.path.exists(SIM_HISTORY_CSV):
    raise FileNotFoundError(
        f"Simulation CSV not found: {SIM_HISTORY_CSV}\n"
        "Pass the CSV path explicitly, e.g.\n"
        "python EHTS_simulation_standalone.py path/to/your_sim_history.csv"
    )

df = pd.read_csv(SIM_HISTORY_CSV)
print(f"✅ Loaded simulation history: {SIM_HISTORY_CSV}")
print(f"Rows: {len(df):,}; Columns: {len(df.columns):,}; DT_HOURS: {DT_HOURS}")

REQUIRED_COLUMNS = {
    "P_batt_cc", "P_pv_cc", "P_grid_cc", "P_pile_demand",
    "H_tank_rc_rate", "H_pipe_rc_rate", "H_hv_demand_rate",
    "P_pv", "P_pv_bt", "P_pv_el", "P_pv_cur",
    "H_pv_tank_rate", "p_elec", "p_h2", "soc_b", "soc_h",
    "ev_assigned", "ev_arrivals", "ev_waiting",
    "hv_assigned", "hv_arrivals", "hv_waiting",
    "G_t", "T_am",
}
missing = sorted(REQUIRED_COLUMNS - set(df.columns))
if missing:
    raise KeyError(
        "The simulation CSV is missing required dashboard columns:\n"
        + "\n".join(f"- {name}" for name in missing)
    )



def build_dynamic_dashboard(history_df: pd.DataFrame, steps_per_day: int, output_path: str):
    """Build an auto-playing one-week dashboard with hover pause."""
    work = history_df.copy()
    work["Delta_P_elec"] = (
        work["P_batt_cc"] + work["P_pv_cc"] + work["P_grid_cc"] - work["P_pile_demand"]
    )
    work["Delta_H_h2"] = (
        work["H_tank_rc_rate"] + work["H_pipe_rc_rate"] - work["H_hv_demand_rate"]
    )
    work["Delta_PV"] = (
        work["P_pv"]
        - (work["P_pv_cc"] + work["P_pv_bt"] + work["P_pv_el"] + work["P_pv_cur"])
    )
    work["PV_remain"] = np.maximum(0.0, work["P_pv"] - work["P_pile_demand"])
    work["abs_Delta_P_elec"] = work["Delta_P_elec"].abs()
    work["abs_Delta_H_h2"] = work["Delta_H_h2"].abs()
    work["abs_Delta_PV"] = work["Delta_PV"].abs()
    work["threshold_1e_3"] = 1e-3
    work["pv_to_batt_charge"] = -work["P_pv_bt"]
    work["grid_to_batt_charge"] = -work["P_grid_batt"] if "P_grid_batt" in work.columns else -work["P_gd_bt"]
    work["pv_to_tank_charge"] = -work["H_pv_tank_rate"]
    work["pipe_to_tank_charge"] = (
        -work["H_pipe_tank_rate"] if "H_pipe_tank_rate" in work.columns else -work["H_pipe_tk_rate"]
    )

    def minmax01(series):
        values = np.asarray(series, dtype=float)
        vmin = float(np.nanmin(values))
        vmax = float(np.nanmax(values))
        denom = vmax - vmin if vmax - vmin > 1e-9 else 1.0
        return (values - vmin) / denom

    work["G_t_scaled"] = minmax01(work["G_t"])
    work["T_am_scaled"] = minmax01(work["T_am"])

    def parse_list_column(col):
        if col not in work.columns:
            return pd.DataFrame()
        return pd.DataFrame(work[col].apply(ast.literal_eval).to_list())

    util_ev = parse_list_column("ev_utilization")
    for idx in range(util_ev.shape[1]):
        work[f"ev_util_{idx + 1}"] = util_ev[idx]

    util_hv = parse_list_column("hv_utilization")
    for idx in range(util_hv.shape[1]):
        work[f"hv_util_{idx + 1}"] = util_hv[idx]

    steps_per_week = steps_per_day * 7

    def week_slice(week_idx):
        start = week_idx * steps_per_week
        end = min((week_idx + 1) * steps_per_week, len(work))
        return work.iloc[start:end]

    def week_labels(count, week_idx=0):
        labels = []
        for i in range(count):
            absolute_step = week_idx * steps_per_week + i
            day_in_week = (i // steps_per_day) + 1
            step_in_day = absolute_step % steps_per_day
            minutes = int(step_in_day * DT_HOURS * 60)
            labels.append(
                f"D{day_in_week} {minutes // 60:02d}:{minutes % 60:02d}"
            )
        return labels

    first = week_slice(0)
    x0 = week_labels(len(first), 0)
    dt_hours = float(DT_HOURS)

    fig = make_subplots(
        rows=12,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": False}],
            [{"secondary_y": False}],
            [{"secondary_y": False}],
        ],
        subplot_titles=[
            "PV Generation & Weather",
            "PV Utilization Breakdown",
            "Electricity Charge/Discharge (+ Price)",
            "Hydrogen Charge/Discharge (+ Price)",
            "Energy Storage SOC",
            "EV Arrivals / Assigned / Waiting",
            "Charger Utilization",
            "HV Arrivals / Assigned / Waiting",
            "Refueler Utilization",
            "Electric Power Supply-Demand Balance",
            "Hydrogen Supply-Demand Balance",
            "Supply-Demand Mismatch Diagnostics",
        ],
    )

    trace_specs = [
        ("P_pv", "PV Generation (kW)", "scatter", 1, False),
        ("G_t_scaled", "Solar Irradiance (scaled)", "scatter", 1, True),
        ("T_am_scaled", "Ambient Temp (scaled)", "scatter", 1, True),
        ("P_pv_cc", "PV to Charger", "bar", 2, False),
        ("P_pv_bt", "PV to Battery", "bar", 2, False),
        ("P_pv_el", "PV to Electrolyzer", "bar", 2, False),
        ("P_pv_cur", "PV Curtailed", "bar", 2, False),
        # ("PV_remain", "PV remaining (kW)", "scatter", 2, True),
        ("P_batt_cc", "Actual Discharge (kW)", "bar", 3, False),
        ("pv_to_batt_charge", "PV to Battery (Charge)", "bar", 3, False),
        ("grid_to_batt_charge", "Grid to Battery (Charge)", "bar", 3, False),
        ("p_elec", "Electricity Price ($/kWh)", "scatter", 3, True),
        ("H_tank_rc_rate", "Actual Discharge", "bar", 4, False),
        ("pv_to_tank_charge", "PV to Tank (Charge)", "bar", 4, False),
        ("pipe_to_tank_charge", "Pipeline to Tank (Charge)", "bar", 4, False),
        ("p_h2", "Hydrogen Price ($/Nm3)", "scatter", 4, True),
        ("soc_b", "Battery SOC", "bar", 5, False),
        ("soc_h", "H2 Tank SOC", "bar", 5, True),
        # ("ev_candidate", "EV Candidate", "bar", 6, False),
        ("ev_assigned", "EV Assigned", "bar", 6, False),
        ("ev_arrivals", "EV Arrivals", "scatter", 6, False),
        ("ev_waiting", "EV Waiting", "scatter", 6, True),
        # ("ev_candidate", "EV Candidates", "bar", 7, False),
        # ("ev_assigned", "EV Assigned", "bar", 7, False),
        *[(f"ev_util_{i + 1}", f"EV Charger {i + 1} Util (%)", "scatter", 7, True) for i in range(util_ev.shape[1])],
        # ("hv_candidate", "HV Candidate", "bar", 8, False),
        ("hv_assigned", "HV Assigned", "bar", 8, False),
        ("hv_arrivals", "HV Arrivals", "scatter", 8, False),
        ("hv_waiting", "HV Waiting", "scatter", 8, True),
        # ("hv_candidate", "HV Candidates", "bar", 9, False),
        # ("hv_assigned", "HV Assigned", "bar", 9, False),
        *[(f"hv_util_{i + 1}", f"HV Refueler {i + 1} Util (%)", "scatter", 9, True) for i in range(util_hv.shape[1])],
        ("P_pile_demand", "EV Power Demand", "scatter", 10, False),
        ("P_batt_cc", "Battery to Charger", "bar", 10, False),
        ("P_pv_cc", "PV to Charger", "bar", 10, False),
        ("P_grid_cc", "Grid Supply", "bar", 10, False),
        ("H_hv_demand_rate", "HV H2 Demand", "scatter", 11, False),
        ("H_tank_rc_rate", "Tank to Refueler", "bar", 11, False),
        ("H_pipe_rc_rate", "Pipeline to Refueler", "bar", 11, False),
        ("abs_Delta_P_elec", "|Delta P| Electric", "scatter", 12, False),
        ("abs_Delta_H_h2", "|Delta H| Hydrogen", "scatter", 12, False),
        ("threshold_1e_3", "Threshold 1e-3", "scatter", 12, False),
        ("abs_Delta_PV", "|Delta PV| PV Mismatch", "scatter", 12, False),
    ]

    balance_trace_styles = {
        (10, "P_pile_demand"): {"line": dict(color="blue", width=2)},
        (10, "P_batt_cc"): {"marker_color": "deepskyblue"},
        (10, "P_pv_cc"): {"marker_color": "orange"},
        (10, "P_grid_cc"): {"marker_color": "black"},
        (11, "H_hv_demand_rate"): {"line": dict(color="green", width=2)},
        (11, "H_tank_rc_rate"): {"marker_color": "limegreen"},
        (11, "H_pipe_rc_rate"): {"marker_color": "gray"},
    }

    for col, name, kind, row, secondary_y in trace_specs:
        style = balance_trace_styles.get((row, col), {})
        if kind == "bar":
            fig.add_trace(go.Bar(x=x0, y=first[col], name=name, opacity=0.85, **style), row=row, col=1, secondary_y=secondary_y)
        else:
            fig.add_trace(go.Scatter(x=x0, y=first[col], name=name, mode="lines", **style), row=row, col=1, secondary_y=secondary_y)

    def padded_nonnegative_range(*series_list):
        max_value = 0.0
        for series in series_list:
            values = np.asarray(series, dtype=float)
            if values.size:
                max_value = max(max_value, float(np.nanmax(values)))
        return [0, max_value * 1.08 if max_value > 0 else 1]

    fig.update_yaxes(title_text="PV Power (kW)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Irradiance / Temp (scaled)", range=[0, 1], row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="PV Utilization (kW)", row=2, col=1, secondary_y=False)
    # fig.update_yaxes(title_text="PV Remain (kW)", row=2, col=1, secondary_y=True)
    fig.update_yaxes(visible=False, row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Battery Power Flow (+/-kW)", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Price ($/kWh)", row=3, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Hydrogen Flow (+/-Nm3/h)", row=4, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Price ($/Nm3)", row=4, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Battery SOC", range=[0, 1], row=5, col=1, secondary_y=False)
    fig.update_yaxes(title_text="H2 Tank SOC", range=[0, 1], row=5, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Arrivals / Assigned (EV)", row=6, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Waiting EVs", row=6, col=1, secondary_y=True)
    # # fig.update_yaxes(title_text="EV Candidates / Assigned (#)", row=7, col=1, secondary_y=False)
    fig.update_yaxes(visible=False, row=7, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Charger Utilization (%)", range=[0, 100], row=7, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Arrivals / Assigned (HV)", row=8, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Waiting HVs", row=8, col=1, secondary_y=True)
    # # fig.update_yaxes(title_text="HV Candidates / Assigned (#)", row=9, col=1, secondary_y=False)
    fig.update_yaxes(visible=False, row=9, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Refueler Utilization (%)", range=[0, 100], row=9, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Power (kW)", row=10, col=1)
    fig.update_yaxes(title_text="Hydrogen Flow (Nm3/h)", row=11, col=1)
    fig.update_yaxes(title_text="|Mismatch| (log scale)", type="log", row=12, col=1)
    fig.update_xaxes(title_text="Time in current week", row=12, col=1)
    fig.update_yaxes(
        range=padded_nonnegative_range(work["P_pv"]),
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.update_yaxes(
        range=padded_nonnegative_range(work["P_pv_cc"], work["P_pv_bt"], work["P_pv_el"], work["P_pv_cur"]),
        row=2,
        col=1,
        secondary_y=False,
    )
    # fig.update_yaxes(
    #     range=padded_nonnegative_range(work["PV_remain"]),
    #     row=2,
    #     col=1,
    #     secondary_y=True,
    # )

    total_weeks = int(np.ceil(len(work) / steps_per_week))
    display_weeks = 52
    replay_after_week = min(total_weeks, 45)
    plot_title = ""
    page_title = "Week 1 - Integrated Energy Station Dashboard"
    fig.update_layout(
        height=2700,
        barmode="relative",
        bargap=0.08,
        bargroupgap=0.03,
        hovermode="x unified",
        template="plotly_white",
        title=dict(text=plot_title, x=0.5, xanchor="center", y=0.995, yanchor="top"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            traceorder="normal",
            itemsizing="trace",
        ),
        margin=dict(l=60, r=40, t=120, b=100),
    )

    grid_to_batt_raw_col = "P_grid_batt" if "P_grid_batt" in work.columns else "P_gd_bt"
    h_pipe_tank_col = "H_pipe_tank_rate" if "H_pipe_tank_rate" in work.columns else "H_pipe_tk_rate"

    def week_summary(week_idx):
        wk = week_slice(week_idx)
        pv_generated = float(wk["P_pv"].sum() * dt_hours)
        grid_energy = float((wk["P_grid_cc"] + wk[grid_to_batt_raw_col].clip(lower=0)).sum() * dt_hours)
        grid_cost = float(((wk["P_grid_cc"] + wk[grid_to_batt_raw_col].clip(lower=0)) * wk["p_elec"]).sum() * dt_hours)
        pipe_h2 = float((wk["H_pipe_rc_rate"] + wk[h_pipe_tank_col].clip(lower=0)).sum() * dt_hours)
        pipe_cost = float(((wk["H_pipe_rc_rate"] + wk[h_pipe_tank_col].clip(lower=0)) * wk["p_h2"]).sum() * dt_hours)
        pv_curtailed = float(wk["P_pv_cur"].sum() * dt_hours)
        pv_curtail_value = float((wk["P_pv_cur"] * wk["p_elec"]).sum() * dt_hours)
        ev_served = float(wk["ev_assigned"].sum())
        hv_served = float(wk["hv_assigned"].sum())
        return {
            "week": week_idx + 1,
            "pv_generated_kwh": pv_generated,
            "grid_energy_kwh": grid_energy,
            "grid_cost": grid_cost,
            "pipeline_h2_nm3": pipe_h2,
            "pipeline_cost": pipe_cost,
            "pv_curtailed_kwh": pv_curtailed,
            "pv_curtail_value": pv_curtail_value,
            "ev_served": ev_served,
            "hv_served": hv_served,
            "total_served": ev_served + hv_served,
            "peak_ev_waiting": float(wk["ev_waiting"].max()),
            "peak_hv_waiting": float(wk["hv_waiting"].max()),
            "peak_ev_demand_kw": float(wk["P_pile_demand"].max()),
            "peak_hv_demand_nm3h": float(wk["H_hv_demand_rate"].max()),
        }

    weekly_summaries_json = json.dumps([week_summary(i) for i in range(total_weeks)], separators=(",", ":"))
    panel_titles = [
        "PV Generation & Weather",
        "PV Utilization Breakdown",
        "Electricity Charge/Discharge (+ Price)",
        "Hydrogen Charge/Discharge (+ Price)",
        "Energy Storage SOC",
        "EV Arrivals / Assigned / Waiting",
        "Charger Utilization",
        "HV Arrivals / Assigned / Waiting",
        "Refueler Utilization",
        "Electric Power Supply-Demand Balance",
        "Hydrogen Supply-Demand Balance",
        "Supply-Demand Mismatch Diagnostics",
    ]
    data_columns = sorted({col for col, _, _, _, _ in trace_specs})
    payload = {
        col: [None if pd.isna(v) else float(v) for v in work[col].values]
        for col in data_columns
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    trace_columns_json = json.dumps([col for col, _, _, _, _ in trace_specs])
    trace_rows_json = json.dumps([row for _, _, _, row, _ in trace_specs])
    panel_titles_json = json.dumps(panel_titles)

    post_script = f"""
const gd = document.getElementById('{{plot_id}}');
const raw = {payload_json};
const traceColumns = {trace_columns_json};
const traceRows = {trace_rows_json};
const weeklySummaries = {weekly_summaries_json};
const panelTitles = {panel_titles_json};
const stepsPerDay = {steps_per_day};
const stepsPerWeek = {steps_per_week};
const totalRows = {len(work)};
const totalWeeks = {total_weeks};
const displayWeeks = {display_weeks};
const replayAfterWeek = {replay_after_week};
let weekIndex = 0;
let timer = null;
let hoverPaused = false;
const intervalMs = 1100;
let weekSelect = null;
let panelVisible = Array(panelTitles.length).fill(true);
const traceEnabled = traceColumns.map((col, index) => {{
  const row = traceRows[index];
  return !(
    (row === 2 && col === 'PV_remain') ||
    (row === 6 && col === 'ev_candidate') ||
    (row === 7 && (col === 'ev_candidate' || col === 'ev_assigned')) ||
    (row === 8 && col === 'hv_candidate') ||
    (row === 9 && (col === 'hv_candidate' || col === 'hv_assigned'))
  );
}});
const hiddenAxisNumbers = new Set([4, 13, 17]);

function installWeekSelector() {{
  const wrapper = gd.parentElement;
  const controls = document.createElement('div');
  controls.style.display = 'flex';
  controls.style.alignItems = 'center';
  controls.style.justifyContent = 'center';
  controls.style.gap = '10px';
  controls.style.margin = '12px 0 4px';
  controls.style.fontFamily = 'Arial, sans-serif';
  controls.style.fontSize = '15px';

  const label = document.createElement('label');
  label.textContent = 'Jump to week';
  label.setAttribute('for', 'week-selector');

  weekSelect = document.createElement('select');
  weekSelect.id = 'week-selector';
  weekSelect.style.fontSize = '15px';
  weekSelect.style.padding = '4px 10px';
  weekSelect.style.border = '1px solid #9ca3af';
  weekSelect.style.borderRadius = '4px';
  weekSelect.style.background = '#fff';

  for (let i = 0; i < displayWeeks; i++) {{
    const option = document.createElement('option');
    option.value = String(i);
    option.textContent = `Week ${{i + 1}}`;
    weekSelect.appendChild(option);
  }}

  weekSelect.addEventListener('change', () => {{
    pause();
    updateWeek(Number(weekSelect.value));
    if (!hoverPaused) play();
  }});

  controls.appendChild(label);
  controls.appendChild(weekSelect);
  wrapper.insertBefore(controls, gd);
}}

function formatNumber(value, decimals = 0) {{
  if (!Number.isFinite(value)) return '-';
  return value.toLocaleString(undefined, {{maximumFractionDigits: decimals, minimumFractionDigits: decimals}});
}}

function formatMoney(value) {{
  if (!Number.isFinite(value)) return '-';
  return '$' + value.toLocaleString(undefined, {{maximumFractionDigits: 0}});
}}

function formatHalfCount(value) {{
  return formatNumber(Math.round(value / 2));
}}

function sourceWeekFor(displayWeek) {{
  if (totalWeeks <= 0) return 0;
  const normalizedWeek = ((displayWeek % displayWeeks) + displayWeeks) % displayWeeks;
  if (replayAfterWeek > 0 && normalizedWeek >= replayAfterWeek) {{
    return (normalizedWeek - replayAfterWeek) % replayAfterWeek;
  }}
  return normalizedWeek % totalWeeks;
}}

function updateWeekSummary(sourceWeekIndex = sourceWeekFor(weekIndex)) {{
  const grid = document.getElementById('week-summary-grid');
  if (!grid) return;
  const s = weeklySummaries[sourceWeekIndex] || weeklySummaries[0];
  const cards = [
    ['PV generated', formatNumber(s.pv_generated_kwh) + ' kWh', 'Current week'],
    ['Grid purchased', formatNumber(s.grid_energy_kwh) + ' kWh', formatMoney(s.grid_cost)],
    ['Pipeline H2 purchased', formatNumber(s.pipeline_h2_nm3) + ' Nm3', formatMoney(s.pipeline_cost)],
    ['PV curtailed', formatNumber(s.pv_curtailed_kwh) + ' kWh', formatMoney(s.pv_curtail_value) + ' value'],
    ['Peak waiting', 'EV ' + formatNumber(s.peak_ev_waiting) + ' / HV ' + formatNumber(s.peak_hv_waiting), 'vehicles'],
    ['Peak EV demand', formatNumber(s.peak_ev_demand_kw) + ' kW', 'charging demand'],
    ['Peak HV demand', formatNumber(s.peak_hv_demand_nm3h) + ' Nm3/h', 'hydrogen demand']
  ];
  grid.innerHTML = cards.map(([label, value, sub]) => `
    <article class="week-summary__card">
      <div class="week-summary__label">${{label}}</div>
      <div class="week-summary__value">${{value}}</div>
      <div class="week-summary__sub">${{sub}}</div>
    </article>
  `).join('');
}}

function axisLayoutName(prefix, axisNumber) {{
  return prefix + (axisNumber === 1 ? 'axis' : 'axis' + axisNumber);
}}

function rowAxisNumbers(row) {{
  if (row <= 9) return [row * 2 - 1, row * 2];
  return [18 + (row - 9)];
}}

function buildPanelRelayout() {{
  const visibleRows = panelVisible
    .map((visible, index) => visible ? index + 1 : null)
    .filter((row) => row !== null);
  const relayout = {{height: 360 + visibleRows.length * 190}};
  const gap = visibleRows.length > 1 ? 0.022 : 0;
  const titleOffset = visibleRows.length > 1 ? 0.006 : 0.018;
  const domainHeight = visibleRows.length ? (1 - gap * (visibleRows.length - 1)) / visibleRows.length : 1;
  let cursor = 0;
  for (let row = panelTitles.length; row >= 1; row--) {{
    let domain;
    if (panelVisible[row - 1]) {{
      domain = [cursor, cursor + domainHeight];
      cursor += domainHeight + gap;
    }} else {{
      domain = [0, 0.001];
    }}
    for (const axisNumber of rowAxisNumbers(row)) {{
      relayout[axisLayoutName('y', axisNumber) + '.domain'] = domain;
      relayout[axisLayoutName('y', axisNumber) + '.visible'] = panelVisible[row - 1] && !hiddenAxisNumbers.has(axisNumber);
    }}
    relayout[`annotations[${{row - 1}}].visible`] = panelVisible[row - 1];
    relayout[`annotations[${{row - 1}}].y`] = panelVisible[row - 1] ? Math.min(domain[1] + titleOffset, 1.03) : 0;
    relayout[`annotations[${{row - 1}}].yanchor`] = 'bottom';
  }}
  return relayout;
}}

function applyPanelVisibility() {{
  const visible = traceRows.map((row, index) => panelVisible[row - 1] && traceEnabled[index]);
  Plotly.update(gd, {{visible}}, buildPanelRelayout());
}}

function installPanelToggles() {{
  const wrapper = gd.parentElement;
  const bar = document.createElement('div');
  bar.className = 'panel-toggle-bar';
  panelTitles.forEach((title, index) => {{
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'panel-toggle';
    button.textContent = title;
    button.setAttribute('aria-pressed', 'true');
    button.title = 'Show or collapse this panel';
    button.addEventListener('click', () => {{
      panelVisible[index] = !panelVisible[index];
      if (!panelVisible.some(Boolean)) panelVisible[index] = true;
      button.setAttribute('aria-pressed', String(panelVisible[index]));
      applyPanelVisibility();
    }});
    bar.appendChild(button);
  }});
  wrapper.insertBefore(bar, gd);
}}

function installStationStoryToggle() {{
  const story = document.querySelector('.station-story');
  const toggle = document.querySelector('.station-story__toggle');
  if (!story || !toggle || toggle.dataset.bound === 'true') return;
  toggle.dataset.bound = 'true';
  toggle.addEventListener('click', () => {{
    const collapsed = story.classList.toggle('is-collapsed');
    toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.textContent = collapsed ? 'Show station diagram' : 'Hide station diagram';
    setTimeout(() => Plotly.Plots.resize(gd), 0);
  }});
}}

function weekLabels(count, week) {{
  const labels = [];
  for (let i = 0; i < count; i++) {{
    const absoluteStep = week * stepsPerWeek + i;
    const dayInWeek = Math.floor(i / stepsPerDay) + 1;
    const stepInDay = absoluteStep % stepsPerDay;
    const minutes = stepInDay * {int(DT_HOURS * 60)};
    labels.push('D' + dayInWeek + ' ' + String(Math.floor(minutes / 60)).padStart(2, '0') + ':' + String(minutes % 60).padStart(2, '0'));
  }}
  return labels;
}}
function updateWeek(nextWeek) {{
  weekIndex = ((nextWeek % displayWeeks) + displayWeeks) % displayWeeks;
  const sourceWeekIndex = sourceWeekFor(weekIndex);
  const start = sourceWeekIndex * stepsPerWeek;
  const end = Math.min(start + stepsPerWeek, totalRows);
  const count = end - start;
  const x = weekLabels(count, sourceWeekIndex);
  const xs = traceColumns.map(() => x);
  const ys = traceColumns.map((col) => raw[col].slice(start, end));
  Plotly.update(gd, {{x: xs, y: ys}}, {{
    title: {{text: '', x: 0.5, xanchor: 'center', y: 0.995, yanchor: 'top'}},
    margin: {{l: 60, r: 40, t: 120, b: 100}}
  }});
  if (weekSelect) weekSelect.value = String(weekIndex);
  updateWeekSummary(sourceWeekIndex);
}}
function play() {{
  if (timer) return;
  timer = setInterval(() => updateWeek(weekIndex + 1), intervalMs);
}}
function pause() {{
  if (!timer) return;
  clearInterval(timer);
  timer = null;
}}
gd.on('plotly_hover', () => {{ hoverPaused = true; pause(); }});
gd.on('plotly_unhover', () => {{ hoverPaused = false; play(); }});
gd.addEventListener('mouseenter', () => {{ hoverPaused = true; pause(); }});
gd.addEventListener('mouseleave', () => {{ hoverPaused = false; play(); }});
installWeekSelector();
installStationStoryToggle();
installPanelToggles();
applyPanelVisibility();
updateWeekSummary();
play();
"""

    write_dashboard_html(
        fig,
        output_path,
        post_script=post_script,
        page_title=page_title,
    )


steps_per_day_dynamic = int(24 / DT_HOURS)
dynamic_html = os.environ.get(
    "EHTS_OUTPUT_HTML",
    os.path.join(RUNS_DIR, "EH_Dashboard_dynamic_standalone.html"),
)
build_dynamic_dashboard(df, steps_per_day_dynamic, dynamic_html)
print(f"✅ Dynamic dashboard saved: {dynamic_html}")

