"""
study_data.py
=============
Comprehensive statistical analysis of Valorant stress study data.
Loads all 51 subjects, performs deep analysis, generates publication-quality
multi-panel figures, and prints a full statistical report.
"""

import os, glob, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from scipy import stats

warnings.filterwarnings("ignore")

# ── config ───────────────────────────────────────────────────
BASE_DIR   = r"p:\IEEE\SUBJECTS"
OUTPUT_DIR = os.path.join(BASE_DIR, "stress_plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── dark theme ───────────────────────────────────────────────
BG      = "#0f172a"
PANEL   = "#1e293b"
ACCENT  = "#38bdf8"
ACCENT2 = "#818cf8"
ACCENT3 = "#c084fc"
ORANGE  = "#f97316"
GREEN   = "#34d399"
RED     = "#f87171"
PINK    = "#fb7185"
TEXT    = "#e2e8f0"
GRID    = "#334155"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   PANEL,
    "axes.edgecolor":   GRID,
    "axes.labelcolor":  TEXT,
    "xtick.color":      TEXT,
    "ytick.color":      TEXT,
    "text.color":       TEXT,
    "font.family":      "sans-serif",
    "font.size":        11,
    "grid.color":       GRID,
    "grid.alpha":       0.3,
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
    sub_id = os.path.basename(os.path.dirname(fpath))
    ts = df["timestamp_ms"].values.astype(float)
    df = df.copy()
    df["relative_time_s"] = (ts - ts[0]) / 1000.0
    df["subject"] = sub_id
    frames.append(df)

big = pd.concat(frames, ignore_index=True)
n_sub = big["subject"].nunique()
print(f"Loaded {n_sub} subjects, {len(big)} total data-points.\n")

# ── REPORT: descriptive stats ────────────────────────────────
print("=" * 70)
print("   DESCRIPTIVE STATISTICS")
print("=" * 70)
for col in ["stress_score", "composite_stress", "bpm", "rr_ms"]:
    vals = big[col].dropna()
    print(f"\n--- {col} ---")
    print(f"  Count:    {len(vals)}")
    print(f"  Mean:     {vals.mean():.2f}")
    print(f"  Median:   {vals.median():.2f}")
    print(f"  Std Dev:  {vals.std():.2f}")
    print(f"  Min:      {vals.min():.2f}")
    print(f"  Max:      {vals.max():.2f}")
    print(f"  Skewness: {vals.skew():.3f}")
    print(f"  Kurtosis: {vals.kurtosis():.3f}")
    # normality test
    if len(vals) > 8:
        stat, p = stats.shapiro(vals.sample(min(5000, len(vals)), random_state=42))
        print(f"  Shapiro-Wilk: W={stat:.4f}, p={p:.4e} {'(NOT normal)' if p < 0.05 else '(normal)'}")

# ── REPORT: event breakdown ──────────────────────────────────
print("\n" + "=" * 70)
print("   EVENT TYPE ANALYSIS")
print("=" * 70)
events = big["event"].value_counts()
print(f"\nEvent counts:")
for ev, cnt in events.items():
    sub = big[big["event"] == ev]
    print(f"  {ev:20s}: n={cnt:5d}  |  stress: mean={sub['stress_score'].mean():6.2f}  "
          f"median={sub['stress_score'].median():5.2f}  std={sub['stress_score'].std():6.2f}  "
          f"composite: mean={sub['composite_stress'].mean():6.2f}")

# ANOVA: stress by event type
print("\nOne-way ANOVA (stress_score ~ event):")
groups = [g["stress_score"].dropna().values for _, g in big.groupby("event")]
groups = [g for g in groups if len(g) >= 5]
F, p = stats.f_oneway(*groups)
print(f"  F={F:.3f}, p={p:.4e} {'(SIGNIFICANT)' if p < 0.05 else '(not significant)'}")

# Kruskal-Wallis (non-parametric alternative)
H, p_kw = stats.kruskal(*groups)
print(f"  Kruskal-Wallis: H={H:.3f}, p={p_kw:.4e} {'(SIGNIFICANT)' if p_kw < 0.05 else '(not significant)'}")

# ── REPORT: emotion analysis ─────────────────────────────────
print("\n" + "=" * 70)
print("   EMOTION ANALYSIS")
print("=" * 70)
emotions = big["dominant_emotion"].value_counts()
print(f"\nEmotion counts:")
for em, cnt in emotions.items():
    sub = big[big["dominant_emotion"] == em]
    print(f"  {em:12s}: n={cnt:5d}  |  stress: mean={sub['stress_score'].mean():6.2f}  "
          f"median={sub['stress_score'].median():5.2f}  "
          f"bpm: mean={sub['bpm'].mean():5.1f}")

# ANOVA: stress by emotion
print("\nOne-way ANOVA (stress_score ~ emotion):")
emo_groups = [g["stress_score"].dropna().values for _, g in big.groupby("dominant_emotion")]
emo_groups = [g for g in emo_groups if len(g) >= 5]
F_e, p_e = stats.f_oneway(*emo_groups)
print(f"  F={F_e:.3f}, p={p_e:.4e} {'(SIGNIFICANT)' if p_e < 0.05 else '(not significant)'}")

# ── REPORT: bio status ────────────────────────────────────────
print("\n" + "=" * 70)
print("   BIO STATUS ANALYSIS")
print("=" * 70)
bio = big["bio_status"].value_counts()
for bs, cnt in bio.items():
    sub = big[big["bio_status"] == bs]
    print(f"  {bs:12s}: n={cnt:5d}  |  stress: mean={sub['stress_score'].mean():6.2f}  "
          f"bpm: mean={sub['bpm'].mean():5.1f}  rr_ms: mean={sub['rr_ms'].mean():6.1f}")

# ── REPORT: correlations ─────────────────────────────────────
print("\n" + "=" * 70)
print("   CORRELATIONS")
print("=" * 70)
numeric_cols = ["stress_score", "composite_stress", "bpm", "rr_ms"]
for c1 in numeric_cols:
    for c2 in numeric_cols:
        if c1 >= c2:
            continue
        valid = big[[c1, c2]].dropna()
        r, p = stats.pearsonr(valid[c1], valid[c2])
        rs, ps = stats.spearmanr(valid[c1], valid[c2])
        sig_p = " ***" if p < 0.001 else (" **" if p < 0.01 else (" *" if p < 0.05 else ""))
        sig_s = " ***" if ps < 0.001 else (" **" if ps < 0.01 else (" *" if ps < 0.05 else ""))
        print(f"  {c1:20s} vs {c2:20s}: Pearson r={r:+.4f} (p={p:.2e}){sig_p}  "
              f"Spearman rho={rs:+.4f} (p={ps:.2e}){sig_s}")

# ── REPORT: KILL vs DEATH ────────────────────────────────────
print("\n" + "=" * 70)
print("   KILL vs DEATH COMPARISON")
print("=" * 70)
kills  = big[big["event"] == "KILL"]["stress_score"].dropna()
deaths = big[big["event"] == "DEATH"]["stress_score"].dropna()
t_stat, t_p = stats.ttest_ind(kills, deaths, equal_var=False)
u_stat, u_p = stats.mannwhitneyu(kills, deaths, alternative="two-sided")
print(f"  KILL  (n={len(kills):4d}): mean={kills.mean():.2f}, median={kills.median():.2f}, std={kills.std():.2f}")
print(f"  DEATH (n={len(deaths):4d}): mean={deaths.mean():.2f}, median={deaths.median():.2f}, std={deaths.std():.2f}")
print(f"  Welch's t-test: t={t_stat:.3f}, p={t_p:.4e} {'(SIGNIFICANT)' if t_p < 0.05 else ''}")
print(f"  Mann-Whitney U:  U={u_stat:.1f}, p={u_p:.4e} {'(SIGNIFICANT)' if u_p < 0.05 else ''}")
cohens_d = (kills.mean() - deaths.mean()) / np.sqrt((kills.std()**2 + deaths.std()**2) / 2)
print(f"  Cohen's d: {cohens_d:.3f} ({'small' if abs(cohens_d)<0.5 else ('medium' if abs(cohens_d)<0.8 else 'large')} effect)")

# ── REPORT: per-subject summary ──────────────────────────────
print("\n" + "=" * 70)
print("   PER-SUBJECT SUMMARY")
print("=" * 70)
subj_summary = big.groupby("subject").agg(
    n_events=("stress_score", "count"),
    mean_stress=("stress_score", "mean"),
    median_stress=("stress_score", "median"),
    std_stress=("stress_score", "std"),
    max_stress=("stress_score", "max"),
    mean_bpm=("bpm", "mean"),
    mean_composite=("composite_stress", "mean"),
    session_dur_s=("relative_time_s", "max"),
).sort_values("mean_stress", ascending=False)

for idx, row in subj_summary.iterrows():
    print(f"  {idx}: events={int(row.n_events):3d}  stress(mean={row.mean_stress:5.1f} med={row.median_stress:5.1f} "
          f"max={row.max_stress:5.1f})  bpm={row.mean_bpm:5.1f}  duration={row.session_dur_s:6.0f}s")


# ════════════════════════════════════════════════════════════════
# FIGURE 1 — Event & Emotion Analysis (2x2)
# ════════════════════════════════════════════════════════════════
fig1 = plt.figure(figsize=(20, 14))
fig1.suptitle("Figure 1: Event & Emotion Stress Analysis (n=51 subjects)",
              fontsize=20, fontweight="bold", color="white", y=0.97)
gs1 = fig1.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                        left=0.08, right=0.95, top=0.91, bottom=0.08)

# Panel A — Stress by Event Type (violin + box)
ax1a = fig1.add_subplot(gs1[0, 0])
event_order = ["KILL", "DEATH", "SPIKE_PLANTED", "SPIKE_DEFUSED"]
event_data = [big[big["event"] == e]["stress_score"].dropna().values for e in event_order if e in big["event"].values]
event_labels = [e for e in event_order if e in big["event"].values]
event_colors = [ACCENT, RED, ORANGE, GREEN]

parts = ax1a.violinplot([d for d in event_data], showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(event_colors[i])
    pc.set_alpha(0.4)

bp = ax1a.boxplot(event_data, widths=0.15, patch_artist=True,
                  medianprops=dict(color="white", linewidth=2),
                  whiskerprops=dict(color=TEXT), capprops=dict(color=TEXT),
                  flierprops=dict(marker=".", markerfacecolor=TEXT, markersize=2, alpha=0.3))
for i, patch in enumerate(bp["boxes"]):
    patch.set_facecolor(event_colors[i])
    patch.set_alpha(0.8)

ax1a.set_xticks(range(1, len(event_labels)+1))
ax1a.set_xticklabels(event_labels, fontsize=10)
ax1a.set_ylabel("Stress Score")
ax1a.set_title("A. Stress by Event Type", fontsize=13, fontweight="bold", pad=10)
ax1a.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel B — Stress by Emotion (grouped bar: mean + median)
ax1b = fig1.add_subplot(gs1[0, 1])
emo_order = ["neutral", "fear", "angry", "sad", "happy", "surprise", "disgust", "NO_FACE"]
emo_order = [e for e in emo_order if e in big["dominant_emotion"].values]
emo_means = [big[big["dominant_emotion"]==e]["stress_score"].mean() for e in emo_order]
emo_medians = [big[big["dominant_emotion"]==e]["stress_score"].median() for e in emo_order]
emo_counts = [len(big[big["dominant_emotion"]==e]) for e in emo_order]

x = np.arange(len(emo_order))
w = 0.35
bars1 = ax1b.bar(x - w/2, emo_means, w, color=ACCENT2, alpha=0.85, label="Mean", edgecolor="none")
bars2 = ax1b.bar(x + w/2, emo_medians, w, color=ACCENT3, alpha=0.85, label="Median", edgecolor="none")

# Add count labels on top
for i, (b, cnt) in enumerate(zip(bars1, emo_counts)):
    ax1b.text(b.get_x() + w, b.get_height() + 1, f"n={cnt}", ha="center", fontsize=7, color=TEXT)

ax1b.set_xticks(x)
ax1b.set_xticklabels(emo_order, rotation=30, ha="right", fontsize=9)
ax1b.set_ylabel("Stress Score")
ax1b.set_title("B. Stress by Detected Emotion", fontsize=13, fontweight="bold", pad=10)
ax1b.legend(fontsize=9, framealpha=0.6)
ax1b.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel C — BPM vs Stress scatter with regression
ax1c = fig1.add_subplot(gs1[1, 0])
sample = big[["bpm", "stress_score"]].dropna()
ax1c.scatter(sample["bpm"], sample["stress_score"],
             s=12, alpha=0.35, color=ACCENT, edgecolors="none")

# regression line
slope, intercept, r, p, se = stats.linregress(sample["bpm"], sample["stress_score"])
bpm_range = np.linspace(sample["bpm"].min(), sample["bpm"].max(), 100)
ax1c.plot(bpm_range, slope * bpm_range + intercept, color=ORANGE, linewidth=2.5,
          label=f"r={r:.3f}, p={p:.2e}")

ax1c.set_xlabel("Heart Rate (BPM)")
ax1c.set_ylabel("Stress Score")
ax1c.set_title("C. BPM vs Stress Score", fontsize=13, fontweight="bold", pad=10)
ax1c.legend(fontsize=10, framealpha=0.6)
ax1c.grid(True, linestyle="--", alpha=0.3)

# Panel D — Composite stress vs Stress score scatter
ax1d = fig1.add_subplot(gs1[1, 1])
sample2 = big[["composite_stress", "stress_score"]].dropna()
ax1d.scatter(sample2["stress_score"], sample2["composite_stress"],
             s=12, alpha=0.35, color=GREEN, edgecolors="none")

slope2, intercept2, r2, p2, se2 = stats.linregress(sample2["stress_score"], sample2["composite_stress"])
ss_range = np.linspace(0, 100, 100)
ax1d.plot(ss_range, slope2 * ss_range + intercept2, color=PINK, linewidth=2.5,
          label=f"r={r2:.3f}, p={p2:.2e}")

ax1d.set_xlabel("Stress Score (facial)")
ax1d.set_ylabel("Composite Stress")
ax1d.set_title("D. Stress Score vs Composite Stress", fontsize=13, fontweight="bold", pad=10)
ax1d.legend(fontsize=10, framealpha=0.6)
ax1d.grid(True, linestyle="--", alpha=0.3)

fig1.savefig(os.path.join(OUTPUT_DIR, "study_fig1_event_emotion.png"), dpi=200, bbox_inches="tight")
plt.close(fig1)
print("\nSaved: study_fig1_event_emotion.png")


# ════════════════════════════════════════════════════════════════
# FIGURE 2 — Temporal & Bio Analysis (2x2)
# ════════════════════════════════════════════════════════════════
fig2 = plt.figure(figsize=(20, 14))
fig2.suptitle("Figure 2: Temporal & Physiological Patterns (n=51 subjects)",
              fontsize=20, fontweight="bold", color="white", y=0.97)
gs2 = fig2.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                        left=0.08, right=0.95, top=0.91, bottom=0.08)

# Panel A — Stress by Bio Status
ax2a = fig2.add_subplot(gs2[0, 0])
bio_order = ["NORMAL", "ELEVATED", "RECOVERY"]
bio_order = [b for b in bio_order if b in big["bio_status"].values]
bio_data = [big[big["bio_status"]==b]["stress_score"].dropna().values for b in bio_order]
bio_colors = [ACCENT, RED, GREEN]

parts2 = ax2a.violinplot(bio_data, showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts2["bodies"]):
    pc.set_facecolor(bio_colors[i])
    pc.set_alpha(0.4)

bp2 = ax2a.boxplot(bio_data, widths=0.2, patch_artist=True,
                   medianprops=dict(color="white", linewidth=2),
                   whiskerprops=dict(color=TEXT), capprops=dict(color=TEXT),
                   flierprops=dict(marker=".", markerfacecolor=TEXT, markersize=2, alpha=0.3))
for i, patch in enumerate(bp2["boxes"]):
    patch.set_facecolor(bio_colors[i])
    patch.set_alpha(0.8)

ax2a.set_xticks(range(1, len(bio_order)+1))
ax2a.set_xticklabels([f"{b}\n(n={len(bio_data[i])})" for i, b in enumerate(bio_order)], fontsize=10)
ax2a.set_ylabel("Stress Score")
ax2a.set_title("A. Stress by Bio Status", fontsize=13, fontweight="bold", pad=10)
ax2a.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel B — BPM distribution by Bio Status
ax2b = fig2.add_subplot(gs2[0, 1])
for i, b in enumerate(bio_order):
    bpm_vals = big[big["bio_status"]==b]["bpm"].dropna().values
    ax2b.hist(bpm_vals, bins=30, alpha=0.5, color=bio_colors[i],
              label=f"{b} (mean={np.mean(bpm_vals):.1f})", density=True, edgecolor="none")
ax2b.set_xlabel("Heart Rate (BPM)")
ax2b.set_ylabel("Density")
ax2b.set_title("B. BPM Distribution by Bio Status", fontsize=13, fontweight="bold", pad=10)
ax2b.legend(fontsize=9, framealpha=0.6)
ax2b.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel C — Stress over session time (mean per quartile of session)
ax2c = fig2.add_subplot(gs2[1, 0])
# Normalize each subject's session to 0-100% progress
big_copy = big.copy()
max_times = big_copy.groupby("subject")["relative_time_s"].transform("max")
big_copy["session_pct"] = (big_copy["relative_time_s"] / max_times.replace(0, 1)) * 100

pct_bins = np.arange(0, 101, 10)
pct_centers = (pct_bins[:-1] + pct_bins[1:]) / 2
pct_means, pct_stds, pct_medians = [], [], []
for lo, hi in zip(pct_bins[:-1], pct_bins[1:]):
    chunk = big_copy.loc[(big_copy["session_pct"] >= lo) & (big_copy["session_pct"] < hi), "stress_score"]
    pct_means.append(chunk.mean())
    pct_stds.append(chunk.std())
    pct_medians.append(chunk.median())

pct_means = np.array(pct_means)
pct_stds = np.array(pct_stds)
pct_medians = np.array(pct_medians)

ax2c.fill_between(pct_centers, np.clip(pct_means - pct_stds, 0, 100),
                  np.clip(pct_means + pct_stds, 0, 100),
                  color=ACCENT, alpha=0.15, label="+/-1 SD")
ax2c.plot(pct_centers, pct_means, color=ACCENT, linewidth=2.5, marker="o", markersize=6, label="Mean")
ax2c.plot(pct_centers, pct_medians, color=ACCENT3, linewidth=1.5, linestyle="--", marker="s", markersize=5, label="Median")

ax2c.set_xlabel("Session Progress (%)")
ax2c.set_ylabel("Stress Score")
ax2c.set_title("C. Stress Across Normalised Session Time", fontsize=13, fontweight="bold", pad=10)
ax2c.legend(fontsize=9, framealpha=0.6)
ax2c.grid(True, linestyle="--", alpha=0.3)
ax2c.set_xlim(0, 100)

# Panel D — Correlation heatmap
ax2d = fig2.add_subplot(gs2[1, 1])
corr_cols = ["stress_score", "composite_stress", "bpm", "rr_ms"]
corr_matrix = big[corr_cols].corr(method="spearman")

im = ax2d.imshow(corr_matrix.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
ax2d.set_xticks(range(len(corr_cols)))
ax2d.set_yticks(range(len(corr_cols)))
labels_short = ["Stress", "Composite", "BPM", "RR interval"]
ax2d.set_xticklabels(labels_short, rotation=30, ha="right", fontsize=10)
ax2d.set_yticklabels(labels_short, fontsize=10)

# Annotate
for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        val = corr_matrix.values[i, j]
        color = "white" if abs(val) > 0.5 else TEXT
        ax2d.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=12,
                  fontweight="bold", color=color)

cbar = fig2.colorbar(im, ax=ax2d, shrink=0.8)
cbar.ax.yaxis.set_tick_params(color=TEXT)
cbar.outline.set_edgecolor(GRID)
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=TEXT)

ax2d.set_title("D. Spearman Correlation Matrix", fontsize=13, fontweight="bold", pad=10)

fig2.savefig(os.path.join(OUTPUT_DIR, "study_fig2_temporal_bio.png"), dpi=200, bbox_inches="tight")
plt.close(fig2)
print("Saved: study_fig2_temporal_bio.png")


# ════════════════════════════════════════════════════════════════
# FIGURE 3 — Subject Variability & Death Analysis (2x2)
# ════════════════════════════════════════════════════════════════
fig3 = plt.figure(figsize=(20, 14))
fig3.suptitle("Figure 3: Subject Variability & Event Impact (n=51 subjects)",
              fontsize=20, fontweight="bold", color="white", y=0.97)
gs3 = fig3.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                        left=0.08, right=0.95, top=0.91, bottom=0.08)

# Panel A — Subject-level mean stress vs mean BPM
ax3a = fig3.add_subplot(gs3[0, 0])
subj_agg = big.groupby("subject").agg(
    mean_stress=("stress_score", "mean"),
    mean_bpm=("bpm", "mean"),
    n_events=("stress_score", "count"),
).reset_index()

scatter_sizes = subj_agg["n_events"] * 2
ax3a.scatter(subj_agg["mean_bpm"], subj_agg["mean_stress"],
             s=scatter_sizes, alpha=0.7, c=subj_agg["mean_stress"],
             cmap="viridis", edgecolors="white", linewidths=0.5)

slope3, intercept3, r3, p3, _ = stats.linregress(subj_agg["mean_bpm"], subj_agg["mean_stress"])
bpm_x = np.linspace(subj_agg["mean_bpm"].min(), subj_agg["mean_bpm"].max(), 50)
ax3a.plot(bpm_x, slope3 * bpm_x + intercept3, color=ORANGE, linewidth=2,
          linestyle="--", label=f"r={r3:.3f}, p={p3:.3f}")

ax3a.set_xlabel("Mean BPM")
ax3a.set_ylabel("Mean Stress Score")
ax3a.set_title("A. Per-Subject: Mean BPM vs Mean Stress", fontsize=13, fontweight="bold", pad=10)
ax3a.legend(fontsize=10, framealpha=0.6)
ax3a.grid(True, linestyle="--", alpha=0.3)

# Panel B — Stress coefficient of variation per subject
ax3b = fig3.add_subplot(gs3[0, 1])
subj_cv = big.groupby("subject")["stress_score"].agg(["mean", "std"])
subj_cv["cv"] = (subj_cv["std"] / subj_cv["mean"].replace(0, np.nan)) * 100
subj_cv = subj_cv.sort_values("cv", ascending=True).dropna()

colors_cv = plt.cm.plasma(np.linspace(0.1, 0.9, len(subj_cv)))
ax3b.barh(range(len(subj_cv)), subj_cv["cv"].values, color=colors_cv, edgecolor="none", height=0.7)
ax3b.set_yticks(range(len(subj_cv)))
ax3b.set_yticklabels(subj_cv.index, fontsize=6)
ax3b.set_xlabel("Coefficient of Variation (%)")
ax3b.set_title("B. Stress Variability per Subject (CV%)", fontsize=13, fontweight="bold", pad=10)
ax3b.axvline(subj_cv["cv"].median(), color=ORANGE, linewidth=2, linestyle="--",
             label=f"Median CV = {subj_cv['cv'].median():.0f}%")
ax3b.legend(fontsize=9, framealpha=0.6)
ax3b.grid(True, axis="x", linestyle="--", alpha=0.3)

# Panel C — DEATH events: stress distribution with emotion overlay
ax3c = fig3.add_subplot(gs3[1, 0])
deaths = big[big["event"] == "DEATH"].copy()
if len(deaths) > 0:
    emo_colors_map = {"neutral": ACCENT, "fear": RED, "angry": ORANGE, "sad": ACCENT2,
                      "happy": GREEN, "surprise": PINK, "disgust": "#a78bfa", "NO_FACE": GRID}
    for emo in deaths["dominant_emotion"].unique():
        subset = deaths[deaths["dominant_emotion"] == emo]["stress_score"].dropna()
        if len(subset) >= 2:
            ax3c.hist(subset, bins=20, alpha=0.5, label=f"{emo} (n={len(subset)})",
                      color=emo_colors_map.get(emo, TEXT), edgecolor="none", density=True)
    ax3c.set_xlabel("Stress Score")
    ax3c.set_ylabel("Density")
    ax3c.set_title("C. DEATH Events: Stress by Emotion", fontsize=13, fontweight="bold", pad=10)
    ax3c.legend(fontsize=8, framealpha=0.6)
    ax3c.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel D — Session duration vs mean stress
ax3d = fig3.add_subplot(gs3[1, 1])
subj_dur = big.groupby("subject").agg(
    dur_s=("relative_time_s", "max"),
    mean_stress=("stress_score", "mean"),
    n_events=("stress_score", "count"),
).reset_index()
subj_dur["dur_min"] = subj_dur["dur_s"] / 60

ax3d.scatter(subj_dur["dur_min"], subj_dur["mean_stress"],
             s=subj_dur["n_events"] * 2, alpha=0.7, c=subj_dur["n_events"],
             cmap="cool", edgecolors="white", linewidths=0.5)

slope4, intercept4, r4, p4, _ = stats.linregress(subj_dur["dur_min"], subj_dur["mean_stress"])
dur_x = np.linspace(subj_dur["dur_min"].min(), subj_dur["dur_min"].max(), 50)
ax3d.plot(dur_x, slope4 * dur_x + intercept4, color=ORANGE, linewidth=2,
          linestyle="--", label=f"r={r4:.3f}, p={p4:.3f}")

ax3d.set_xlabel("Session Duration (minutes)")
ax3d.set_ylabel("Mean Stress Score")
ax3d.set_title("D. Session Duration vs Mean Stress", fontsize=13, fontweight="bold", pad=10)
ax3d.legend(fontsize=10, framealpha=0.6)
ax3d.grid(True, linestyle="--", alpha=0.3)

fig3.savefig(os.path.join(OUTPUT_DIR, "study_fig3_variability_events.png"), dpi=200, bbox_inches="tight")
plt.close(fig3)
print("Saved: study_fig3_variability_events.png")

print("\n" + "=" * 70)
print("   ANALYSIS COMPLETE")
print("=" * 70)
