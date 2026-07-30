"""
bifurcate_stress.py
===================
Splits the Valorant dataset based on stress_score thresholds and analyzes the differences.
"""

import os, glob, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

# ── config ────────────────────────────────────────────────────
BASE_DIR   = r"p:\IEEE\SUBJECTS"
OUTPUT_DIR = os.path.join(BASE_DIR, "stress_plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# dark theme
BG, PANEL, TEXT, GRID = "#0f172a", "#1e293b", "#e2e8f0", "#334155"
LOW_COLOR, MED_COLOR, HIGH_COLOR = "#34d399", "#facc15", "#f87171" # Green, Yellow, Red

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT,
    "xtick.color": TEXT, "ytick.color": TEXT, "text.color": TEXT,
    "font.family": "sans-serif", "font.size": 11,
    "grid.color": GRID, "grid.alpha": 0.3,
})

# ── load data ────────────────────────────────────────────────
csv_files = sorted(glob.glob(os.path.join(BASE_DIR, "SUB*", "*.csv")))
frames = []
for fpath in csv_files:
    try:
        df = pd.read_csv(fpath, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(fpath, encoding="latin1")
    if "timestamp_ms" not in df.columns or "stress_score" not in df.columns:
        continue
    df["subject"] = os.path.basename(os.path.dirname(fpath))
    frames.append(df)

big = pd.concat(frames, ignore_index=True)

# ── Bifurcation Logic ───────────────────────────────────────
# Define thresholds
def categorize_stress(score):
    if score <= 20:
        return "Low (0-20)"
    elif score <= 60:
        return "Medium (20-60)"
    else:
        return "High (60-100)"

big["stress_tier"] = big["stress_score"].apply(categorize_stress)
# Ensure consistent ordering
tier_order = ["Low (0-20)", "Medium (20-60)", "High (60-100)"]
big["stress_tier"] = pd.Categorical(big["stress_tier"], categories=tier_order, ordered=True)

# Exclude sensor failure subjects for cardiac metrics
valid_bpm_mask = ~big["subject"].isin(["SUB037", "SUB038"])
big_cardiac = big[valid_bpm_mask]

print("=" * 60)
print(" STRESS BIFURCATION ANALYSIS (0-20, 20-60, 60-100)")
print("=" * 60)

# 1. Distribution of Tiers
tier_counts = big["stress_tier"].value_counts(normalize=False).sort_index()
tier_pcts = big["stress_tier"].value_counts(normalize=True).sort_index() * 100
print("\n--- Distribution ---")
for t, c, p in zip(tier_order, tier_counts, tier_pcts):
    print(f"  {t}: {c} events ({p:.1f}%)")

# 2. BPM across Tiers
print("\n--- Average BPM by Stress Tier ---")
bpm_stats = big_cardiac[big_cardiac["bpm"] > 0].groupby("stress_tier")["bpm"].mean()
for t in tier_order:
    print(f"  {t}: {bpm_stats.get(t, 0):.1f} BPM")

# 3. Events across Tiers
print("\n--- Event Types causing High Stress ---")
high_events = big[big["stress_tier"] == "High (60-100)"]["event"].value_counts()
for event, count in high_events.items():
    print(f"  {event}: {count} occurrences")

# 4. Emotions across Tiers
print("\n--- Dominant Emotions in High Stress ---")
high_emotions = big[big["stress_tier"] == "High (60-100)"]["dominant_emotion"].value_counts()
for emotion, count in high_emotions.items():
    print(f"  {emotion}: {count} occurrences")


# ── FIGURE: Bifurcation Dashboard ──────────────────────────────
fig = plt.figure(figsize=(18, 12))
fig.suptitle("Data Bifurcation based on Stress Score", fontsize=20, fontweight="bold", color="white", y=0.96)
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
colors = [LOW_COLOR, MED_COLOR, HIGH_COLOR]

# Panel A: Count of events per tier
ax_a = fig.add_subplot(gs[0, 0])
bars = ax_a.bar(tier_order, tier_counts, color=colors, edgecolor="none", alpha=0.8)
ax_a.set_title("A. Total Events per Stress Tier", fontsize=14, pad=10)
ax_a.set_ylabel("Number of Events")
for bar in bars:
    yval = bar.get_height()
    ax_a.text(bar.get_x() + bar.get_width()/2, yval + 20, int(yval), ha="center", color=TEXT)
ax_a.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel B: Average BPM per tier
ax_b = fig.add_subplot(gs[0, 1])
valid_bpm_df = big_cardiac[big_cardiac["bpm"] > 0]
bpm_means = [valid_bpm_df[valid_bpm_df["stress_tier"] == t]["bpm"].mean() for t in tier_order]
bpm_bars = ax_b.bar(tier_order, bpm_means, color=colors, edgecolor="none", alpha=0.8)
ax_b.set_title("B. Average Heart Rate (BPM) per Stress Tier", fontsize=14, pad=10)
ax_b.set_ylabel("Mean BPM")
# Zoom in on y-axis for better visibility of differences
ax_b.set_ylim(min(bpm_means)-5, max(bpm_means)+5)
for bar in bpm_bars:
    yval = bar.get_height()
    ax_b.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.1f}", ha="center", color=TEXT)
ax_b.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel C: Event types breakdown per tier
ax_c = fig.add_subplot(gs[1, 0])
event_counts = big.groupby(["stress_tier", "event"]).size().unstack(fill_value=0)
# Normalize to percentages for fair comparison
event_pcts = event_counts.div(event_counts.sum(axis=1), axis=0) * 100
event_pcts.plot(kind="bar", stacked=True, ax=ax_c, colormap="tab20", alpha=0.9, edgecolor=PANEL)
ax_c.set_title("C. Event Composition per Stress Tier (%)", fontsize=14, pad=10)
ax_c.set_ylabel("Percentage of Events")
ax_c.set_xlabel("")
ax_c.legend(title="Event Type", bbox_to_anchor=(1.05, 1), loc='upper left', framealpha=0.6)
ax_c.set_xticklabels(tier_order, rotation=0)

# Panel D: Emotion breakdown per tier
ax_d = fig.add_subplot(gs[1, 1])
emo_counts = big.groupby(["stress_tier", "dominant_emotion"]).size().unstack(fill_value=0)
emo_pcts = emo_counts.div(emo_counts.sum(axis=1), axis=0) * 100
emo_colors = {"neutral": "#cbd5e1", "happy": "#4ade80", "fear": "#f87171", 
              "angry": "#facc15", "sad": "#818cf8", "surprise": "#c084fc", "NO_FACE": "#475569"}
# Reorder columns to match colors dictionary keys present in data
cols = [c for c in emo_colors.keys() if c in emo_pcts.columns]
emo_pcts = emo_pcts[cols]
# Create color list matching columns
col_list = [emo_colors[c] for c in emo_pcts.columns]

emo_pcts.plot(kind="bar", stacked=True, ax=ax_d, color=col_list, alpha=0.9, edgecolor=PANEL)
ax_d.set_title("D. Emotional Composition per Stress Tier (%)", fontsize=14, pad=10)
ax_d.set_ylabel("Percentage of Events")
ax_d.set_xlabel("")
ax_d.legend(title="Dominant Emotion", bbox_to_anchor=(1.05, 1), loc='upper left', framealpha=0.6)
ax_d.set_xticklabels(tier_order, rotation=0)

out_path = os.path.join(OUTPUT_DIR, "bifurcation_dashboard.png")
fig.savefig(out_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nSaved dashboard to: {out_path}")
print("-- DONE --")
