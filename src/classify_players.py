"""
classify_players.py
===================
Estimates player skill tiers (Pro, Veteran, Casual, New Player) based on 
in-game performance metrics (Kills Per Minute) and analyzes their stress responses.
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
COLORS = {"Pro": "#c084fc", "Veteran": "#f87171", "Casual": "#38bdf8", "New": "#34d399"}

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
    
    # Calculate relative time
    ts = df["timestamp_ms"].values.astype(float)
    df["relative_time_s"] = (ts - ts[0]) / 1000.0
    
    frames.append(df)

big = pd.concat(frames, ignore_index=True)

# ── 1. Calculate Performance Metrics per Subject ─────────────
subject_stats = []
for sub in big["subject"].unique():
    sub_df = big[big["subject"] == sub]
    
    kills = len(sub_df[sub_df["event"] == "KILL"])
    deaths = len(sub_df[sub_df["event"] == "DEATH"])
    
    # Session length in minutes
    duration_m = sub_df["relative_time_s"].max() / 60.0
    # Avoid division by zero
    duration_m = max(duration_m, 1.0)
    
    kpm = kills / duration_m
    
    mean_stress = sub_df["stress_score"].mean()
    mean_bpm = sub_df[sub_df["bpm"] > 0]["bpm"].mean()
    
    subject_stats.append({
        "subject": sub,
        "kills": kills,
        "deaths": deaths,
        "duration_m": duration_m,
        "kpm": kpm,
        "mean_stress": mean_stress,
        "mean_bpm": mean_bpm
    })

stats_df = pd.DataFrame(subject_stats)

# ── 2. Categorize Players based on Percentiles of KPM ───────
# We use Kills Per Minute (KPM) as the primary proxy for skill.
# Top 15% -> Pro
# Next 35% -> Veteran
# Next 35% -> Casual
# Bottom 15% -> New Player

p85 = stats_df["kpm"].quantile(0.85)
p50 = stats_df["kpm"].quantile(0.50)
p15 = stats_df["kpm"].quantile(0.15)

def get_tier(kpm):
    if kpm >= p85: return "Pro"
    if kpm >= p50: return "Veteran"
    if kpm >= p15: return "Casual"
    return "New"

stats_df["skill_tier"] = stats_df["kpm"].apply(get_tier)
tier_order = ["Pro", "Veteran", "Casual", "New"]
stats_df["skill_tier"] = pd.Categorical(stats_df["skill_tier"], categories=tier_order, ordered=True)

# Merge back to main dataset
big = big.merge(stats_df[["subject", "skill_tier", "kpm"]], on="subject")

print("=" * 60)
print(" PLAYER SKILL ESTIMATION (Based on Kills Per Minute)")
print("=" * 60)

print("\n--- Cohort Distribution ---")
tier_counts = stats_df["skill_tier"].value_counts().sort_index()
for tier in tier_order:
    sub_count = tier_counts[tier]
    avg_kpm = stats_df[stats_df["skill_tier"] == tier]["kpm"].mean()
    print(f"  {tier}: {sub_count} players (Avg KPM: {avg_kpm:.2f})")

print("\n--- Stress & Heart Rate by Skill Tier ---")
for tier in tier_order:
    tier_data = stats_df[stats_df["skill_tier"] == tier]
    print(f"  {tier}:")
    print(f"    Avg Facial Stress: {tier_data['mean_stress'].mean():.1f}")
    print(f"    Avg Heart Rate:    {tier_data['mean_bpm'].mean():.1f} BPM")

# ── FIGURE: Skill Tier Dashboard ──────────────────────────────
fig = plt.figure(figsize=(18, 12))
fig.suptitle("Estimated Player Skill Tiers & Stress Profiles", fontsize=20, fontweight="bold", color="white", y=0.96)
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

color_list = [COLORS[t] for t in tier_order]

# Panel A: KPM Distribution by Tier
ax_a = fig.add_subplot(gs[0, 0])
bp_data = [stats_df[stats_df["skill_tier"] == t]["kpm"].values for t in tier_order]
bp = ax_a.boxplot(bp_data, patch_artist=True, medianprops=dict(color="white", linewidth=2),
                  whiskerprops=dict(color=TEXT), capprops=dict(color=TEXT),
                  flierprops=dict(marker=".", markerfacecolor="white", alpha=0.5))
for patch, color in zip(bp['boxes'], color_list):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
ax_a.set_xticklabels(tier_order)
ax_a.set_ylabel("Kills Per Minute (KPM)")
ax_a.set_title(f"A. Skill Estimation Metrics (n={len(stats_df)} players)", fontsize=14, pad=10)
ax_a.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel B: Stress Score Distribution by Tier (Violin plot)
ax_b = fig.add_subplot(gs[0, 1])
# We'll plot the distribution of ALL events for each tier to show variance
event_stress_data = [big[big["skill_tier"] == t]["stress_score"].dropna().values for t in tier_order]
parts = ax_b.violinplot(event_stress_data, showmeans=True, showmedians=False, showextrema=False)
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(color_list[i])
    pc.set_edgecolor(PANEL)
    pc.set_alpha(0.7)
parts['cmeans'].set_color('white')
parts['cmeans'].set_linewidth(2)
ax_b.set_xticks(range(1, len(tier_order) + 1))
ax_b.set_xticklabels(tier_order)
ax_b.set_ylabel("Event Stress Score")
ax_b.set_title("B. Facial Stress Distribution during Gameplay", fontsize=14, pad=10)
ax_b.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel C: Average Heart Rate by Tier
ax_c = fig.add_subplot(gs[1, 0])
bpm_means = [stats_df[stats_df["skill_tier"] == t]["mean_bpm"].mean() for t in tier_order]
bars_c = ax_c.bar(tier_order, bpm_means, color=color_list, edgecolor="none", alpha=0.8)
ax_c.set_ylim(min(bpm_means)-10, max(bpm_means)+10)
ax_c.set_ylabel("Mean Heart Rate (BPM)")
ax_c.set_title("C. Average Cardiac Response (BPM)", fontsize=14, pad=10)
for bar in bars_c:
    yval = bar.get_height()
    if not np.isnan(yval):
        ax_c.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval:.1f}", ha="center", color=TEXT)
ax_c.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel D: Emotion profile during KILL events
ax_d = fig.add_subplot(gs[1, 1])
kills_df = big[big["event"] == "KILL"]
emo_counts = kills_df.groupby(["skill_tier", "dominant_emotion"]).size().unstack(fill_value=0)
emo_pcts = emo_counts.div(emo_counts.sum(axis=1), axis=0) * 100
emo_colors = {"neutral": "#cbd5e1", "happy": "#4ade80", "fear": "#f87171", 
              "angry": "#facc15", "sad": "#818cf8", "surprise": "#c084fc", "NO_FACE": "#475569"}
cols = [c for c in emo_colors.keys() if c in emo_pcts.columns]
emo_pcts = emo_pcts[cols]
col_list_d = [emo_colors[c] for c in emo_pcts.columns]

emo_pcts.plot(kind="bar", stacked=True, ax=ax_d, color=col_list_d, alpha=0.9, edgecolor=PANEL)
ax_d.set_title("D. Emotions Expressed while getting KILLS (%)", fontsize=14, pad=10)
ax_d.set_ylabel("Percentage of Kills")
ax_d.set_xlabel("")
ax_d.legend(title="Emotion", bbox_to_anchor=(1.05, 1), loc='upper left', framealpha=0.6)
ax_d.set_xticklabels(tier_order, rotation=0)

out_path = os.path.join(OUTPUT_DIR, "skill_tier_dashboard.png")
fig.savefig(out_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nSaved dashboard to: {out_path}")
print("-- DONE --")
