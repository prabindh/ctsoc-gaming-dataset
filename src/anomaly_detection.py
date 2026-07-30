"""
anomaly_detection.py
====================
Multi-method anomaly detection on the Valorant stress study dataset.

Methods:
  1. Data Integrity Checks (impossible values, missing data, duplicates)
  2. Statistical Outliers (Z-score, IQR, Grubbs')
  3. Temporal Anomalies (timestamp gaps, ordering, impossible speeds)
  4. Per-Subject Anomalies (subjects that deviate from the cohort)
  5. Multivariate Anomalies (Isolation Forest, Mahalanobis distance)
  6. Logical Consistency Checks (e.g. emotion vs stress mismatch)
"""

import os, glob, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats
from collections import defaultdict

warnings.filterwarnings("ignore")

# ── config ────────────────────────────────────────────────────
BASE_DIR   = r"p:\IEEE\SUBJECTS"
OUTPUT_DIR = os.path.join(BASE_DIR, "stress_plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# dark theme
BG, PANEL, ACCENT = "#0f172a", "#1e293b", "#38bdf8"
ACCENT2, ACCENT3, ORANGE = "#818cf8", "#c084fc", "#f97316"
GREEN, RED, PINK, TEXT, GRID = "#34d399", "#f87171", "#fb7185", "#e2e8f0", "#334155"

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
    sub_id = os.path.basename(os.path.dirname(fpath))
    ts = df["timestamp_ms"].values.astype(float)
    df = df.copy()
    df["relative_time_s"] = (ts - ts[0]) / 1000.0
    df["subject"] = sub_id
    df["source_file"] = os.path.basename(fpath)
    frames.append(df)

big = pd.concat(frames, ignore_index=True)
n_sub = big["subject"].nunique()
print(f"Loaded {n_sub} subjects, {len(big)} data-points.\n")

# Collection for all anomalies
anomalies = []

def log_anomaly(category, severity, subject, description, row_idx=None, values=None):
    """Log an anomaly to the collection."""
    anomalies.append({
        "category": category,
        "severity": severity,   # CRITICAL, WARNING, INFO
        "subject": subject,
        "description": description,
        "row_idx": row_idx,
        "values": str(values) if values else ""
    })


# ================================================================
# 1. DATA INTEGRITY CHECKS
# ================================================================
print("=" * 70)
print("  1. DATA INTEGRITY CHECKS")
print("=" * 70)

# 1a. Missing values
print("\n--- Missing Values ---")
for col in big.columns:
    n_miss = big[col].isna().sum()
    if n_miss > 0:
        pct = n_miss / len(big) * 100
        print(f"  {col}: {n_miss} missing ({pct:.1f}%)")
        log_anomaly("INTEGRITY", "WARNING", "ALL", f"Column '{col}' has {n_miss} missing values ({pct:.1f}%)")

# 1b. Zero BPM (sensor failure)
zero_bpm = big[big["bpm"] == 0]
if len(zero_bpm) > 0:
    per_sub = zero_bpm.groupby("subject").size()
    print(f"\n--- Zero BPM (sensor not connected/failure) ---")
    print(f"  Total rows with BPM=0: {len(zero_bpm)} ({len(zero_bpm)/len(big)*100:.1f}%)")
    for sub, cnt in per_sub.items():
        total = len(big[big["subject"] == sub])
        pct = cnt / total * 100
        print(f"    {sub}: {cnt}/{total} events ({pct:.0f}%)")
        sev = "CRITICAL" if pct > 50 else "WARNING"
        log_anomaly("INTEGRITY", sev, sub,
                    f"BPM=0 in {cnt}/{total} events ({pct:.0f}%) - possible sensor failure",
                    values={"zero_bpm_count": cnt, "total": total})

# 1c. Zero RR interval
zero_rr = big[big["rr_ms"] == 0]
if len(zero_rr) > 0:
    print(f"\n--- Zero RR Interval ---")
    print(f"  Total rows with RR=0: {len(zero_rr)} ({len(zero_rr)/len(big)*100:.1f}%)")
    per_sub_rr = zero_rr.groupby("subject").size()
    for sub, cnt in per_sub_rr.items():
        log_anomaly("INTEGRITY", "WARNING", sub,
                    f"RR_ms=0 in {cnt} events - sensor disconnected")

# 1d. Impossible physiological values
print("\n--- Impossible Physiological Values ---")
high_bpm = big[(big["bpm"] > 200) & (big["bpm"] > 0)]
low_bpm  = big[(big["bpm"] > 0) & (big["bpm"] < 30)]
if len(high_bpm) > 0:
    print(f"  BPM > 200: {len(high_bpm)} rows")
    for _, row in high_bpm.iterrows():
        log_anomaly("INTEGRITY", "CRITICAL", row["subject"],
                    f"Impossible BPM={row['bpm']}", values=row.to_dict())
if len(low_bpm) > 0:
    print(f"  BPM < 30 (non-zero): {len(low_bpm)} rows")
    for _, row in low_bpm.iterrows():
        log_anomaly("INTEGRITY", "WARNING", row["subject"],
                    f"Suspiciously low BPM={row['bpm']}", values={"bpm": row["bpm"], "event": row["event"]})

high_rr = big[big["rr_ms"] > 3000]
if len(high_rr) > 0:
    print(f"  RR > 3000ms: {len(high_rr)} rows")
    for _, row in high_rr.iterrows():
        log_anomaly("INTEGRITY", "WARNING", row["subject"],
                    f"RR interval {row['rr_ms']}ms (>3s) - possible missed beat")

# 1e. Stress score out of range
oor_stress = big[(big["stress_score"] < 0) | (big["stress_score"] > 100)]
if len(oor_stress) > 0:
    print(f"  Stress score out of [0,100]: {len(oor_stress)} rows")
    log_anomaly("INTEGRITY", "CRITICAL", "ALL", f"{len(oor_stress)} rows with stress outside [0,100]")
else:
    print(f"  Stress score range: OK (all within [0, 100])")

# 1f. Duplicate timestamps within same subject
print("\n--- Duplicate Timestamps ---")
dup_count = 0
for sub in big["subject"].unique():
    sub_df = big[big["subject"] == sub]
    dupes = sub_df[sub_df.duplicated(subset=["timestamp_ms"], keep=False)]
    if len(dupes) > 0:
        n_dup_ts = dupes["timestamp_ms"].nunique()
        dup_count += len(dupes)
        print(f"  {sub}: {len(dupes)} rows share {n_dup_ts} duplicate timestamps")
        log_anomaly("INTEGRITY", "WARNING", sub,
                    f"{len(dupes)} rows with duplicate timestamps ({n_dup_ts} unique ts)",
                    values={"dup_timestamps": n_dup_ts})

if dup_count == 0:
    print("  No duplicate timestamps found.")
else:
    print(f"  Total duplicated rows: {dup_count}")


# ================================================================
# 2. STATISTICAL OUTLIERS
# ================================================================
print("\n" + "=" * 70)
print("  2. STATISTICAL OUTLIERS")
print("=" * 70)

numeric_cols = ["stress_score", "composite_stress", "bpm", "rr_ms"]
outlier_indices = set()

for col in numeric_cols:
    vals = big[col].dropna()
    # Skip zero BPM/RR for outlier detection (they're sensor failures, not outliers)
    if col in ["bpm", "rr_ms"]:
        vals = vals[vals > 0]

    q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 3 * iqr    # using 3x IQR (extreme outliers)
    upper = q3 + 3 * iqr

    mask = (big[col] < lower) | (big[col] > upper)
    if col in ["bpm", "rr_ms"]:
        mask = mask & (big[col] > 0)  # don't double-count zeros

    extreme = big[mask]
    outlier_indices.update(extreme.index)

    z_scores = np.abs(stats.zscore(vals))
    z_extreme = (z_scores > 3).sum()

    print(f"\n--- {col} ---")
    print(f"  IQR method (3x): {len(extreme)} extreme outliers  [bounds: {lower:.1f} to {upper:.1f}]")
    print(f"  Z-score > 3:     {z_extreme} extreme values")

    if len(extreme) > 0:
        for _, row in extreme.head(5).iterrows():
            log_anomaly("OUTLIER", "INFO", row["subject"],
                        f"{col}={row[col]:.2f} is extreme outlier (IQR bounds: [{lower:.1f}, {upper:.1f}])")

print(f"\n  Total unique rows flagged as outliers: {len(outlier_indices)}")


# ================================================================
# 3. TEMPORAL ANOMALIES
# ================================================================
print("\n" + "=" * 70)
print("  3. TEMPORAL ANOMALIES")
print("=" * 70)

for sub in sorted(big["subject"].unique()):
    sub_df = big[big["subject"] == sub].sort_values("timestamp_ms").copy()
    ts = sub_df["timestamp_ms"].values

    # 3a. Out-of-order timestamps
    out_of_order = np.sum(np.diff(ts) < 0)
    if out_of_order > 0:
        print(f"  {sub}: {out_of_order} out-of-order timestamps")
        log_anomaly("TEMPORAL", "WARNING", sub,
                    f"{out_of_order} timestamps are out of chronological order")

    # 3b. Extremely rapid events (< 500ms apart)
    diffs_ms = np.diff(ts)
    rapid = np.sum((diffs_ms >= 0) & (diffs_ms < 500))
    if rapid > 0:
        rapid_pct = rapid / len(diffs_ms) * 100
        if rapid > 5:
            print(f"  {sub}: {rapid} events < 500ms apart ({rapid_pct:.0f}%)")
            log_anomaly("TEMPORAL", "INFO", sub,
                        f"{rapid} events less than 500ms apart ({rapid_pct:.0f}%) - possible burst events")

    # 3c. Large gaps (> 60s between events)
    large_gaps = np.sum(diffs_ms > 60000)
    if large_gaps > 0:
        max_gap_s = np.max(diffs_ms) / 1000
        log_anomaly("TEMPORAL", "INFO", sub,
                    f"{large_gaps} gaps > 60s (max gap: {max_gap_s:.0f}s)")

    # 3d. Session too short (< 3 minutes)
    duration_s = (ts[-1] - ts[0]) / 1000
    if duration_s < 180:
        print(f"  {sub}: Session only {duration_s:.0f}s ({duration_s/60:.1f} min)")
        log_anomaly("TEMPORAL", "WARNING", sub,
                    f"Very short session: {duration_s:.0f}s ({duration_s/60:.1f} min)")

    # 3e. Too few events
    if len(sub_df) < 25:
        print(f"  {sub}: Only {len(sub_df)} events (< 25)")
        log_anomaly("TEMPORAL", "WARNING", sub,
                    f"Only {len(sub_df)} events recorded - possible incomplete session")


# ================================================================
# 4. LOGICAL CONSISTENCY ANOMALIES
# ================================================================
print("\n" + "=" * 70)
print("  4. LOGICAL CONSISTENCY CHECKS")
print("=" * 70)

# 4a. High stress but happy emotion
happy_high = big[(big["dominant_emotion"] == "happy") & (big["stress_score"] > 50)]
print(f"\n--- Emotion-Stress Contradictions ---")
print(f"  'happy' with stress > 50: {len(happy_high)} rows")
for _, row in happy_high.iterrows():
    log_anomaly("LOGIC", "WARNING", row["subject"],
                f"Emotion='happy' but stress_score={row['stress_score']:.1f}",
                values={"event": row["event"], "bpm": row["bpm"]})

# 4b. NO_FACE with non-zero stress
noface_stress = big[(big["dominant_emotion"] == "NO_FACE") & (big["stress_score"] > 0)]
print(f"  'NO_FACE' with stress > 0: {len(noface_stress)} rows")
if len(noface_stress) > 0:
    log_anomaly("LOGIC", "WARNING", "MULTIPLE",
                f"{len(noface_stress)} rows have NO_FACE but stress > 0 (stress should be 0 when face undetected)")

# 4c. Neutral with very high stress
neutral_high = big[(big["dominant_emotion"] == "neutral") & (big["stress_score"] > 80)]
print(f"  'neutral' with stress > 80: {len(neutral_high)} rows")
for _, row in neutral_high.iterrows():
    log_anomaly("LOGIC", "WARNING", row["subject"],
                f"Emotion='neutral' but stress_score={row['stress_score']:.1f}",
                values={"event": row["event"], "bpm": row["bpm"]})

# 4d. ELEVATED bio_status but low BPM
elevated_low_bpm = big[(big["bio_status"] == "ELEVATED") & (big["bpm"] > 0) & (big["bpm"] < 70)]
print(f"  'ELEVATED' bio with BPM < 70: {len(elevated_low_bpm)} rows")
if len(elevated_low_bpm) > 0:
    log_anomaly("LOGIC", "WARNING", "MULTIPLE",
                f"{len(elevated_low_bpm)} rows classified ELEVATED but BPM < 70")

# 4e. RECOVERY bio_status but high BPM
recovery_high = big[(big["bio_status"] == "RECOVERY") & (big["bpm"] > 80)]
print(f"  'RECOVERY' bio with BPM > 80: {len(recovery_high)} rows")

# 4f. DEATH event where victim is not ME
deaths = big[big["event"] == "DEATH"]
deaths_not_me = deaths[deaths["victim"] != "ME"]
print(f"  DEATH events where victim != 'ME': {len(deaths_not_me)} rows")
if len(deaths_not_me) > 0:
    for _, row in deaths_not_me.head(5).iterrows():
        log_anomaly("LOGIC", "INFO", row["subject"],
                    f"DEATH event but victim='{row['victim']}' instead of 'ME'")

# 4g. SPIKE events with player_name / weapon filled
spike_events = big[big["event"].str.startswith("SPIKE")]
spike_with_player = spike_events[spike_events["player_name"].notna() & (spike_events["player_name"] != "")]
print(f"  SPIKE events with player_name filled: {len(spike_with_player)}")

# 4h. Composite stress lower than expected from formula
# Composite should incorporate both BPM and facial stress
# Check for cases where composite is very far from stress
big_valid = big[(big["bpm"] > 0) & (big["stress_score"].notna()) & (big["composite_stress"].notna())]
diff = (big_valid["composite_stress"] - big_valid["stress_score"]).abs()
large_diff = big_valid[diff > 40]
print(f"  |composite - stress| > 40: {len(large_diff)} rows")


# ================================================================
# 5. PER-SUBJECT ANOMALIES
# ================================================================
print("\n" + "=" * 70)
print("  5. PER-SUBJECT ANOMALIES (cohort outliers)")
print("=" * 70)

subj_stats = big.groupby("subject").agg(
    mean_stress=("stress_score", "mean"),
    std_stress=("stress_score", "std"),
    mean_bpm=("bpm", "mean"),
    n_events=("stress_score", "count"),
    pct_zero_stress=("stress_score", lambda x: (x == 0).mean() * 100),
    pct_high_stress=("stress_score", lambda x: (x > 50).mean() * 100),
    max_stress=("stress_score", "max"),
    session_s=("relative_time_s", "max"),
).reset_index()

# Z-score of each subject's mean stress
subj_stats["z_stress"] = stats.zscore(subj_stats["mean_stress"])
subj_stats["z_bpm"] = stats.zscore(subj_stats["mean_bpm"])

outlier_subs = subj_stats[subj_stats["z_stress"].abs() > 2]
print(f"\nSubjects with mean stress Z > 2 (cohort outliers):")
for _, row in outlier_subs.iterrows():
    direction = "HIGH" if row["z_stress"] > 0 else "LOW"
    print(f"  {row['subject']}: mean_stress={row['mean_stress']:.1f}, z={row['z_stress']:+.2f} ({direction})")
    log_anomaly("SUBJECT", "WARNING", row["subject"],
                f"Mean stress z-score = {row['z_stress']:+.2f} ({direction} outlier in cohort)",
                values={"mean_stress": round(row["mean_stress"], 1)})

# Subjects with very high % zero stress
high_zero = subj_stats[subj_stats["pct_zero_stress"] > 50]
print(f"\nSubjects with > 50% zero stress scores:")
for _, row in high_zero.iterrows():
    print(f"  {row['subject']}: {row['pct_zero_stress']:.0f}% zeros, mean={row['mean_stress']:.1f}")
    log_anomaly("SUBJECT", "INFO", row["subject"],
                f"{row['pct_zero_stress']:.0f}% of stress scores are exactly 0")

# Subjects with anomalous BPM
bpm_outlier_subs = subj_stats[subj_stats["z_bpm"].abs() > 2]
print(f"\nSubjects with anomalous mean BPM (z > 2):")
for _, row in bpm_outlier_subs.iterrows():
    print(f"  {row['subject']}: mean_bpm={row['mean_bpm']:.1f}, z={row['z_bpm']:+.2f}")
    log_anomaly("SUBJECT", "WARNING", row["subject"],
                f"Mean BPM z-score = {row['z_bpm']:+.2f} (mean_bpm={row['mean_bpm']:.1f})")


# ================================================================
# 6. MULTIVARIATE ANOMALY DETECTION (Isolation Forest)
# ================================================================
print("\n" + "=" * 70)
print("  6. MULTIVARIATE ANOMALY DETECTION")
print("=" * 70)

# Use only rows with valid sensor data
mv_data = big[["stress_score", "composite_stress", "bpm", "rr_ms", "subject"]].copy()
mv_valid = mv_data[(mv_data["bpm"] > 0) & (mv_data["rr_ms"] > 0)].dropna()

features = mv_valid[["stress_score", "composite_stress", "bpm", "rr_ms"]].values

# Standardize
from sklearn.preprocessing import StandardScaler
try:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # Mahalanobis distance
    mean = np.mean(X_scaled, axis=0)
    cov = np.cov(X_scaled, rowvar=False)
    cov_inv = np.linalg.pinv(cov)

    mahal_dists = np.array([
        np.sqrt((x - mean) @ cov_inv @ (x - mean).T) for x in X_scaled
    ])

    # Chi-squared threshold for 4 degrees of freedom, p=0.001
    threshold = np.sqrt(stats.chi2.ppf(0.999, df=4))
    mahal_outliers = mv_valid.iloc[mahal_dists > threshold].copy()
    mahal_outliers["mahal_dist"] = mahal_dists[mahal_dists > threshold]

    print(f"\n--- Mahalanobis Distance ---")
    print(f"  Threshold (chi2, p=0.001): {threshold:.2f}")
    print(f"  Outliers detected: {len(mahal_outliers)} / {len(mv_valid)} ({len(mahal_outliers)/len(mv_valid)*100:.1f}%)")

    if len(mahal_outliers) > 0:
        per_sub_mahal = mahal_outliers.groupby("subject").size().sort_values(ascending=False)
        print(f"  Top subjects with multivariate outliers:")
        for sub, cnt in per_sub_mahal.head(10).items():
            total = len(big[big["subject"] == sub])
            print(f"    {sub}: {cnt} outliers / {total} events ({cnt/total*100:.0f}%)")
            log_anomaly("MULTIVARIATE", "INFO", sub,
                        f"{cnt} multivariate outliers (Mahalanobis > {threshold:.1f})")

    HAS_MAHAL = True
except Exception as e:
    print(f"  Mahalanobis computation failed: {e}")
    mahal_dists = None
    mahal_outliers = pd.DataFrame()
    HAS_MAHAL = False

# Try Isolation Forest
try:
    from sklearn.ensemble import IsolationForest
    iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
    iso_labels = iso.fit_predict(X_scaled)
    iso_outliers = mv_valid.iloc[iso_labels == -1]
    iso_scores = iso.decision_function(X_scaled)

    print(f"\n--- Isolation Forest (contamination=5%) ---")
    print(f"  Outliers detected: {len(iso_outliers)} / {len(mv_valid)}")

    per_sub_iso = iso_outliers.groupby("subject").size().sort_values(ascending=False)
    print(f"  Top subjects:")
    for sub, cnt in per_sub_iso.head(10).items():
        total = len(big[big["subject"] == sub])
        print(f"    {sub}: {cnt} outliers / {total} events ({cnt/total*100:.0f}%)")

    HAS_ISO = True
except ImportError:
    print("  sklearn not available - skipping Isolation Forest")
    iso_outliers = pd.DataFrame()
    iso_scores = None
    HAS_ISO = False


# ================================================================
# SUMMARY & VISUALIZATION
# ================================================================
print("\n" + "=" * 70)
print("  ANOMALY SUMMARY")
print("=" * 70)

anom_df = pd.DataFrame(anomalies)
if len(anom_df) > 0:
    print(f"\nTotal anomalies logged: {len(anom_df)}")
    print(f"\nBy severity:")
    for sev in ["CRITICAL", "WARNING", "INFO"]:
        cnt = len(anom_df[anom_df["severity"] == sev])
        if cnt > 0:
            print(f"  {sev}: {cnt}")

    print(f"\nBy category:")
    for cat, cnt in anom_df["category"].value_counts().items():
        print(f"  {cat}: {cnt}")

    print(f"\nCRITICAL anomalies:")
    crits = anom_df[anom_df["severity"] == "CRITICAL"]
    for _, row in crits.iterrows():
        print(f"  [{row['category']}] {row['subject']}: {row['description']}")


# ── FIGURE: Anomaly Detection Dashboard ──────────────────────
fig = plt.figure(figsize=(22, 16))
fig.suptitle("Anomaly Detection Dashboard", fontsize=22, fontweight="bold", color="white", y=0.97)
gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3,
                      left=0.06, right=0.96, top=0.91, bottom=0.06)

# Panel A — BPM anomalies scatter
ax_a = fig.add_subplot(gs[0, 0])
valid_bpm = big[big["bpm"] > 0]
colors_a = np.where(valid_bpm["bpm"] < 30, "red",
           np.where(valid_bpm["bpm"] > 120, "red", ACCENT))
ax_a.scatter(valid_bpm["bpm"], valid_bpm["stress_score"], s=8, alpha=0.4,
             c=colors_a, edgecolors="none")
# Mark zero-BPM subjects
zero_bpm_subs = big[big["bpm"] == 0]["subject"].unique()
ax_a.axvline(30, color=RED, linewidth=1.5, linestyle="--", alpha=0.7, label="Low BPM threshold")
ax_a.set_xlabel("BPM")
ax_a.set_ylabel("Stress Score")
ax_a.set_title(f"A. BPM Anomalies (zeros={len(zero_bpm)})", fontsize=13, fontweight="bold", pad=10)
ax_a.legend(fontsize=8, framealpha=0.6)
ax_a.grid(True, linestyle="--", alpha=0.3)

# Panel B — Duplicate timestamp analysis
ax_b = fig.add_subplot(gs[0, 1])
dup_per_sub = []
for sub in sorted(big["subject"].unique()):
    sub_df = big[big["subject"] == sub]
    n_dup = sub_df.duplicated(subset=["timestamp_ms"], keep=False).sum()
    dup_per_sub.append({"subject": sub, "duplicates": n_dup, "total": len(sub_df)})
dup_df = pd.DataFrame(dup_per_sub)
dup_df["pct"] = dup_df["duplicates"] / dup_df["total"] * 100
dup_df = dup_df.sort_values("pct", ascending=True)

colors_b = [RED if p > 10 else (ORANGE if p > 0 else GREEN) for p in dup_df["pct"]]
ax_b.barh(range(len(dup_df)), dup_df["pct"].values, color=colors_b, edgecolor="none", height=0.7)
ax_b.set_yticks(range(len(dup_df)))
ax_b.set_yticklabels(dup_df["subject"].values, fontsize=5.5)
ax_b.set_xlabel("Duplicate Timestamps (%)")
ax_b.set_title("B. Duplicate Timestamps per Subject", fontsize=13, fontweight="bold", pad=10)
ax_b.grid(True, axis="x", linestyle="--", alpha=0.3)

# Panel C — Emotion-Stress Contradictions
ax_c = fig.add_subplot(gs[0, 2])
emotions = ["neutral", "happy", "fear", "angry", "sad", "surprise", "NO_FACE"]
emotions = [e for e in emotions if e in big["dominant_emotion"].values]
emo_data = []
for em in emotions:
    subset = big[big["dominant_emotion"] == em]["stress_score"]
    emo_data.append(subset.values)

emo_colors = {"neutral": ACCENT, "happy": GREEN, "fear": RED, "angry": ORANGE,
              "sad": ACCENT2, "surprise": PINK, "NO_FACE": GRID}
bp_c = ax_c.boxplot(emo_data, widths=0.5, patch_artist=True,
                    medianprops=dict(color="white", linewidth=2),
                    whiskerprops=dict(color=TEXT), capprops=dict(color=TEXT),
                    flierprops=dict(marker=".", markerfacecolor=RED, markersize=3, alpha=0.4))
for i, (patch, em) in enumerate(zip(bp_c["boxes"], emotions)):
    patch.set_facecolor(emo_colors.get(em, TEXT))
    patch.set_alpha(0.7)
ax_c.set_xticks(range(1, len(emotions)+1))
ax_c.set_xticklabels(emotions, rotation=35, ha="right", fontsize=8)
ax_c.set_ylabel("Stress Score")
ax_c.set_title("C. Stress-Emotion Consistency", fontsize=13, fontweight="bold", pad=10)
# Highlight contradictions
ax_c.axhline(50, color=RED, linewidth=1, linestyle=":", alpha=0.5)
ax_c.annotate("Contradiction zone\n(happy/neutral > 50)", xy=(2, 55),
              fontsize=7, color=RED, ha="center")
ax_c.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel D — Inter-event timing anomalies
ax_d = fig.add_subplot(gs[1, 0])
all_gaps = []
for sub in big["subject"].unique():
    sub_ts = big[big["subject"] == sub].sort_values("timestamp_ms")["timestamp_ms"].values
    gaps = np.diff(sub_ts) / 1000.0  # seconds
    all_gaps.extend(gaps[gaps >= 0])

all_gaps = np.array(all_gaps)
ax_d.hist(all_gaps[all_gaps < 60], bins=60, color=ACCENT, alpha=0.7, edgecolor=PANEL)
ax_d.axvline(0.5, color=RED, linewidth=2, linestyle="--", label=f"Burst (<0.5s): {np.sum(all_gaps < 0.5)}")
ax_d.set_xlabel("Inter-event Gap (seconds)")
ax_d.set_ylabel("Frequency")
ax_d.set_title("D. Inter-Event Timing Distribution", fontsize=13, fontweight="bold", pad=10)
ax_d.legend(fontsize=9, framealpha=0.6)
ax_d.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel E — Mahalanobis distance distribution
ax_e = fig.add_subplot(gs[1, 1])
if HAS_MAHAL and mahal_dists is not None:
    ax_e.hist(mahal_dists[mahal_dists < 10], bins=60, color=ACCENT2, alpha=0.7, edgecolor=PANEL)
    ax_e.axvline(threshold, color=RED, linewidth=2, linestyle="--",
                 label=f"Threshold={threshold:.1f}\nOutliers={len(mahal_outliers)}")
    ax_e.set_xlabel("Mahalanobis Distance")
    ax_e.set_ylabel("Frequency")
    ax_e.set_title("E. Mahalanobis Distance Distribution", fontsize=13, fontweight="bold", pad=10)
    ax_e.legend(fontsize=9, framealpha=0.6)
else:
    ax_e.text(0.5, 0.5, "Not computed", ha="center", va="center", fontsize=14, color=TEXT)
    ax_e.set_title("E. Mahalanobis Distance", fontsize=13, fontweight="bold", pad=10)
ax_e.grid(True, axis="y", linestyle="--", alpha=0.3)

# Panel F — Subject anomaly score (composite)
ax_f = fig.add_subplot(gs[1, 2])
# Build a composite anomaly score per subject
sub_anomaly = defaultdict(float)
for _, a in anom_df.iterrows():
    weight = {"CRITICAL": 3, "WARNING": 1.5, "INFO": 0.5}.get(a["severity"], 1)
    sub_anomaly[a["subject"]] += weight

# Remove global entries
sub_anomaly.pop("ALL", None)
sub_anomaly.pop("MULTIPLE", None)

if sub_anomaly:
    sa_df = pd.DataFrame(list(sub_anomaly.items()), columns=["subject", "score"])
    sa_df = sa_df.sort_values("score", ascending=True)
    colors_f = plt.cm.YlOrRd(np.linspace(0.1, 0.9, len(sa_df)))
    ax_f.barh(range(len(sa_df)), sa_df["score"].values, color=colors_f, edgecolor="none", height=0.7)
    ax_f.set_yticks(range(len(sa_df)))
    ax_f.set_yticklabels(sa_df["subject"].values, fontsize=6)
    ax_f.set_xlabel("Anomaly Score (weighted)")
    ax_f.set_title("F. Composite Anomaly Score per Subject", fontsize=13, fontweight="bold", pad=10)
    ax_f.grid(True, axis="x", linestyle="--", alpha=0.3)
else:
    ax_f.text(0.5, 0.5, "No subject anomalies", ha="center", va="center", fontsize=14, color=TEXT)
    ax_f.set_title("F. Subject Anomaly Scores", fontsize=13, fontweight="bold", pad=10)

out_path = os.path.join(OUTPUT_DIR, "anomaly_detection_dashboard.png")
fig.savefig(out_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nDashboard saved: {out_path}")

# Save anomaly log to CSV
anom_csv = os.path.join(OUTPUT_DIR, "anomaly_log.csv")
anom_df.to_csv(anom_csv, index=False)
print(f"Anomaly log saved: {anom_csv}")

print("\n-- DONE --")
