# Valorant Stress Study — Comprehensive Data Analysis Report

> **Dataset**: 51 subjects, 2,969 game events, Valorant FPS gaming sessions
> **Metrics**: Facial stress score, composite stress, BPM, RR interval, dominant emotion
> **Analysis date**: July 2026

---

## 1. Summary Result Graph

![Result summary showing mean stress over time, distributions, per-subject means, and overall histogram](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/result_summary_all_subjects.png)

---

## 2. Descriptive Statistics

| Metric | Mean | Median | Std Dev | Min | Max | Skewness | Kurtosis |
|---|---|---|---|---|---|---|---|
| **Stress Score** | 17.2 | 6.3 | 24.1 | 0.0 | 100.0 | 1.47 | 0.93 |
| **Composite Stress** | 29.8 | 24.5 | 12.7 | 10.0 | 63.6 | 0.87 | -0.14 |
| **BPM** | 65.5 | 67.0 | 19.2 | 0.0 | 115.0 | -1.79 | 4.30 |
| **RR Interval (ms)** | 846.4 | 808.0 | 355.5 | 0.0 | 2042.0 | -0.08 | 0.56 |

> [!IMPORTANT]
> **All four metrics are NOT normally distributed** (Shapiro-Wilk p < 0.001). The stress score is heavily right-skewed — most events register low stress, with occasional extreme spikes. Non-parametric tests should be preferred.

---

## 3. Event Type Analysis

| Event | Count | Mean Stress | Median Stress | Std | Mean Composite |
|---|---|---|---|---|---|
| **KILL** | 2,422 (81.6%) | 17.39 | 6.09 | 24.26 | 29.20 |
| **DEATH** | 292 (9.8%) | 14.10 | 6.72 | 18.91 | 31.40 |
| **SPIKE_PLANTED** | 200 (6.7%) | 18.24 | 0.30 | 26.54 | 29.30 |
| **SPIKE_DEFUSED** | 55 (1.9%) | 20.40 | 5.98 | 26.71 | 33.43 |

> [!NOTE]
> **ANOVA: F=2.360, p=0.070 — NOT significant.** Event type alone does not significantly differentiate stress levels. However, the Welch's t-test for KILL vs DEATH is **significant (p=0.007)** with a small Cohen's d=0.15. KILLs produce slightly *higher* mean facial stress than DEATHs, possibly because kills involve more visual engagement.

![Figure 1: Event and Emotion Analysis](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/study_fig1_event_emotion.png)

---

## 4. Emotion Analysis — The Strongest Predictor

| Emotion | Count | Mean Stress | Median Stress | Mean BPM |
|---|---|---|---|---|
| **fear** | 107 | **70.39** | 73.87 | 67.7 |
| **angry** | 266 | **62.42** | 63.56 | 62.4 |
| **surprise** | 123 | **47.08** | 50.05 | 66.3 |
| **sad** | 162 | **39.60** | 39.39 | 67.2 |
| **neutral** | 1,851 | 7.85 | 4.49 | 65.6 |
| **happy** | 314 | 0.71 | 0.00 | 62.4 |
| **NO_FACE** | 145 | 0.00 | 0.00 | 67.8 |

> [!CAUTION]
> **ANOVA: F=1859.4, p=0.000 — HIGHLY SIGNIFICANT.** Detected facial emotion is by far the strongest predictor of stress score. Fear and anger produce stress scores 8-9x higher than neutral expressions. This confirms the facial stress scoring model is heavily emotion-driven.

---

## 5. Physiological (Bio) Status

| Bio Status | Count | Mean Stress | Mean BPM | Mean RR (ms) |
|---|---|---|---|---|
| **NORMAL** | 2,346 | 17.78 | 67.7 | 913.7 |
| **ELEVATED** | 256 | 15.89 | **91.4** | 656.1 |
| **RECOVERY** | 175 | 13.82 | 57.8 | **1097.7** |
| **CALIBRATING** | 180 | 16.28 | 0.0 | 0.0 |
| **INTENSE_SPIKE** | 12 | 1.29 | **109.8** | 539.0 |

> [!NOTE]
> Interestingly, ELEVATED heart rate does **not** correlate with higher stress scores. Bio status reflects cardiac response, while stress score is driven by facial expression — these are partially independent modalities.

![Figure 2: Temporal and Bio Analysis](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/study_fig2_temporal_bio.png)

---

## 6. Correlation Analysis

| Pair | Pearson r | Spearman ρ | Significance |
|---|---|---|---|
| **Stress ↔ Composite** | **+0.828** | **+0.748** | p < 0.001 ★★★ |
| **BPM ↔ Composite** | +0.334 | +0.284 | p < 0.001 ★★★ |
| **BPM ↔ RR interval** | +0.307 | -0.287 | p < 0.001 ★★★ |
| BPM ↔ Stress | -0.027 | -0.040 | p = 0.15 (NS) |
| RR ↔ Stress | +0.033 | +0.027 | p = 0.07 (NS) |
| RR ↔ Composite | +0.063 | -0.027 | mixed |

> [!IMPORTANT]
> **Key finding**: Facial stress score and heart rate (BPM) are essentially **uncorrelated** (r = -0.027, p = 0.15). However, both contribute to the composite stress index (r = 0.83 from face, r = 0.33 from BPM). This validates the multimodal approach — the two channels capture different aspects of stress.

---

## 7. Subject Variability

![Figure 3: Variability and Event Impact](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/study_fig3_variability_events.png)

### Top 5 highest-stress subjects:
| Subject | Mean Stress | Median | Max | Events | Session (s) |
|---|---|---|---|---|---|
| SUB032 | **47.8** | 51.2 | 97.3 | 65 | 801 |
| SUB009 | 37.3 | 24.8 | 96.1 | 64 | 711 |
| SUB023 | 33.7 | 33.4 | 91.3 | 62 | 935 |
| SUB027 | 32.7 | 35.0 | 58.3 | 51 | 537 |
| SUB029 | 32.7 | 38.3 | 100.0 | 54 | 625 |

### Bottom 5 lowest-stress subjects:
| Subject | Mean Stress | Median | Max | Events | Session (s) |
|---|---|---|---|---|---|
| SUB004 | **2.0** | 0.1 | 32.3 | 49 | 578 |
| SUB047 | 2.3 | 1.9 | 8.2 | 42 | 518 |
| SUB049 | 2.5 | 0.1 | 33.7 | 69 | 809 |
| SUB022 | 2.5 | 0.0 | 87.9 | 63 | 612 |
| SUB041 | 5.6 | 1.5 | 44.5 | 60 | 830 |

> [!NOTE]
> **Median CV = 125%** — stress responses are extremely variable within subjects. Session duration does NOT correlate with mean stress (r = 0.14, p = 0.32), confirming that stress is event-driven, not time-dependent.

---

## 8. Temporal Patterns

- Stress remains **relatively flat** across normalised session time (mean ≈ 15-19 throughout)
- No clear warm-up or fatigue effect observed
- Median stays low (5-10) with high variance, suggesting stress is **episodic**, driven by discrete game events rather than accumulation

---

## 9. Key Takeaways for IEEE Paper

1. **Facial emotion is the dominant stress predictor** (ANOVA F=1859, p<0.001). Fear/anger → high stress; neutral/happy → low stress.
2. **BPM and facial stress are independent channels** (r = -0.03). Composite stress successfully fuses both.
3. **Event type has limited direct effect on stress** (p=0.07). The stress response depends more on the emotional reaction to the event than the event type itself.
4. **High inter-subject variability** (CV=125%) — individual differences dominate. Some subjects are consistently high-stress (SUB032: mean=47.8) while others barely register (SUB004: mean=2.0).
5. **No temporal habituation** — stress doesn't decrease over time, suggesting Valorant maintains engagement throughout the session.

---

> **Generated files** (all in [stress_plots](file:///P:/IEEE/SUBJECTS/stress_plots)):
> - [result_summary_all_subjects.png](file:///P:/IEEE/SUBJECTS/stress_plots/result_summary_all_subjects.png)
> - [study_fig1_event_emotion.png](file:///P:/IEEE/SUBJECTS/stress_plots/study_fig1_event_emotion.png)
> - [study_fig2_temporal_bio.png](file:///P:/IEEE/SUBJECTS/stress_plots/study_fig2_temporal_bio.png)
> - [study_fig3_variability_events.png](file:///P:/IEEE/SUBJECTS/stress_plots/study_fig3_variability_events.png)
> - [study_data.py](file:///P:/IEEE/SUBJECTS/study_data.py) — full analysis script
