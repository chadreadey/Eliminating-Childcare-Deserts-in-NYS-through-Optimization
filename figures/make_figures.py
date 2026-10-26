"""Build the README figures from the exported solutions in ../results.

Usage (from the repo root):
    python figures/make_figures.py

Writes a light and a dark PNG of each figure into figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DATA = ROOT / "Optimization project 1" / "ChildCareDeserts_Data"
OUT = ROOT / "figures"

THEMES = {
    "light": {
        "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
        "grid": "#e1e0d9", "existing": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a"],
    },
    "dark": {
        "surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
        "grid": "#2c2c2a", "existing": "#4a4a46",
        "series": ["#3987e5", "#d95926", "#199e70"],
    },
}

SIZES = {"S": (100, "Small"), "M": (200, "Medium"), "L": (400, "Large")}
NYC = {"lon": (-74.27, -73.69), "lat": (40.49, 40.92)}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 11,
})


def style_map_axis(ax, t, lon, lat):
    ax.set_xlim(*lon)
    ax.set_ylim(*lat)
    ax.set_aspect(1 / np.cos(np.radians(np.mean(lat))))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor(t["surface"])


def map_figure(t, new, existing, mode):
    fig, (ax_state, ax_nyc) = plt.subplots(
        1, 2, figsize=(13, 6.4), gridspec_kw={"width_ratios": [1.55, 1]}, facecolor=t["surface"])

    for ax, bounds, dot in [(ax_state, None, 2.5), (ax_nyc, NYC, 4)]:
        ax.scatter(existing.lon, existing.lat, s=dot * 0.5, color=t["existing"], linewidths=0, zorder=1)
        for i, (k, (slots, _)) in enumerate(SIZES.items()):
            pts = new[new["size"] == k]
            ax.scatter(pts.lon, pts.lat, s=dot * slots / 100, color=t["series"][i],
                       edgecolors=t["surface"], linewidths=0.4, zorder=2 + i)
        if bounds is None:
            style_map_axis(ax, t, (-79.8, -71.8), (40.45, 45.05))
        else:
            style_map_axis(ax, t, bounds["lon"], bounds["lat"])
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(t["ink2"])
                spine.set_linewidth(1)

    # Outline the NYC window on the statewide map
    ax_state.add_patch(plt.Rectangle((NYC["lon"][0], NYC["lat"][0]), NYC["lon"][1] - NYC["lon"][0],
                                     NYC["lat"][1] - NYC["lat"][0], fill=False, edgecolor=t["ink2"],
                                     linewidth=1, zorder=5))
    ax_state.text(NYC["lon"][1] + 0.08, NYC["lat"][0] + 0.05, "NYC", color=t["ink2"], fontsize=10, zorder=5)

    in_nyc = new.lon.between(*NYC["lon"]) & new.lat.between(*NYC["lat"])
    fig.text(0.012, 0.79, "New York State", color=t["ink2"], fontsize=11, va="top")
    fig.text(0.625, 0.79, f"New York City  ·  {in_nyc.sum():,} of {len(new):,} new sites",
             color=t["ink2"], fontsize=11, va="top")

    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=6, color=t["existing"])]
    labels = [f"Existing facility ({len(existing):,} mapped)"]
    for i, (k, (slots, name)) in enumerate(SIZES.items()):
        handles.append(plt.Line2D([], [], marker="o", linestyle="", markersize=5 + i * 2.5,
                                  color=t["series"][i], markeredgecolor=t["surface"]))
        labels.append(f"New · {name}, {slots} slots ({(new['size'] == k).sum():,})")
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.012, 0.885), ncol=4, frameon=False,
               labelcolor=t["ink"], fontsize=10.5, handletextpad=0.3, columnspacing=1.6)

    fig.text(0.012, 0.965, "Where the realistic plan builds new child care facilities",
             color=t["ink"], fontsize=17, fontweight="semibold", va="top")
    fig.text(0.012, 0.915, "Optimal Part 2 solution: 3,513 new facilities on candidate sites at least 0.06 mi "
             "from any other facility, plus 2,343 expansions. Total cost $444.9M.",
             color=t["ink2"], fontsize=11, va="top")
    fig.subplots_adjust(left=0.012, right=0.988, top=0.76, bottom=0.02, wspace=0.03)
    fig.savefig(OUT / f"map_{mode}.png", dpi=160, facecolor=t["surface"])
    plt.close(fig)


def cost_figure(t, mode):
    # Totals from the notebook outputs (identical to the re-solve; see results/README.md)
    parts = ["Part 1 · Idealistic", "Part 2 · Realistic"]
    costs = {
        "New construction": [358_540_000, 369_205_000],
        "0–5 equipment": [58_786_200, 58_786_200],
        "Expanding existing": [12_813_250, 16_954_413],
    }
    totals = np.sum(list(costs.values()), axis=0)

    fig, ax = plt.subplots(figsize=(10, 2.9), facecolor=t["surface"])
    ax.set_facecolor(t["surface"])
    y = np.arange(len(parts))[::-1]
    left = np.zeros(len(parts))
    for i, (name, vals) in enumerate(costs.items()):
        vals = np.array(vals) / 1e6
        ax.barh(y, vals, left=left, height=0.3, color=t["series"][i], edgecolor=t["surface"],
                linewidth=2, label=name)
        left += vals
    for yi, total in zip(y, totals):
        ax.text(total / 1e6 + 6, yi, f"${total / 1e6:,.1f}M", va="center", color=t["ink"],
                fontsize=12, fontweight="semibold")

    ax.set_ylim(-0.6, 1.6)
    ax.set_yticks(y, parts, color=t["ink"], fontsize=11)
    ax.set_xlim(0, 500)
    ax.set_xticks(range(0, 501, 100), [f"${v}M" for v in range(0, 501, 100)], color=t["muted"], fontsize=10)
    ax.tick_params(length=0)
    ax.grid(axis="x", color=t["grid"], linewidth=1)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])

    fig.text(0.012, 0.95, "Minimum funding to eliminate every child care desert",
             color=t["ink"], fontsize=15, fontweight="semibold", va="top")
    fig.legend(loc="upper left", bbox_to_anchor=(0.006, 0.84), ncol=3, frameon=False,
               labelcolor=t["ink"], fontsize=10.5, handlelength=1, handleheight=1)
    fig.subplots_adjust(left=0.16, right=0.97, top=0.62, bottom=0.13)
    fig.savefig(OUT / f"costs_{mode}.png", dpi=160, facecolor=t["surface"])
    plt.close(fig)


def main():
    new = pd.read_csv(RESULTS / "part2_new_facilities.csv", dtype={"zipcode": str})
    existing = pd.read_csv(DATA / "child_care_regulated.csv", usecols=["latitude", "longitude"]).dropna()
    existing = existing.rename(columns={"latitude": "lat", "longitude": "lon"})
    for mode, t in THEMES.items():
        map_figure(t, new, existing, mode)
        cost_figure(t, mode)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
