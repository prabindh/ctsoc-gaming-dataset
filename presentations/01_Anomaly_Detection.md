---
marp: true
theme: default
paginate: true
backgroundColor: #0f172a
color: #e2e8f0
---

# Anomaly Detection in Valorant Biometrics
## Identifying Errors and Extreme Responses
**Dataset:** 51 Subjects | 2,969 Game Events

---

# 1. Methodology

We applied a multi-method anomaly detection pipeline:
- **Data Integrity Checks**: Missing values, duplicate timestamps
- **Statistical Outliers**: Z-score and IQR bounds
- **Temporal Anomalies**: Burst events and session lengths
- **Multivariate Detection**: Isolation Forest & Mahalanobis distance

---

# 2. Critical Hardware Failures (Sensor Dropouts)

Not all data is usable. We identified complete or partial sensor failures:
- **SUB037**: 100% BPM=0 (Complete failure)
- **SUB038**: 100% BPM=0 (Complete failure)
- **SUB007**: 53% BPM=0 (Intermittent failure)

**Action taken:** These subjects must be excluded from cardiac (BPM) analysis to prevent skewed averages.

---

# 3. Logical Consistency (The Good News)

The dataset is highly consistent logically:
- **0** contradictions between Emotion and Stress (Happy always = 0 stress).
- **0** impossible physiological values (Stress strictly bounded 0-100).
- Bio-status markers (ELEVATED, RECOVERY) perfectly align with BPM thresholds.

---

# 4. Cohort Outliers (Extreme Responders)

Some subjects are genuine "Collective Outliers"—they exhibit unusually extreme stress responses compared to the group:
- **SUB032**: Mean stress 47.8 (Z-score: +3.08). Highly reactive throughout the entire session.
- **SUB025**: Identified as highly anomalous by Isolation Forest (21% of events) due to rare combinations of extreme stress *and* high BPM.

---

# 5. Visual Dashboard

![Anomaly Dashboard](file:///P:/IEEE/SUBJECTS/stress_plots/anomaly_detection_dashboard.png)

---

# 6. Conclusion & Recommendations

- The dataset is generally clean and robust.
- The 130 flagged anomalies are mostly **contextual outliers** (genuine peak human stress), not data corruption.
- Excluding the 3 hardware-failure subjects yields a highly reliable dataset for multimodal analysis.
