# Anomaly Detection Report — Valorant Stress Study

> **130 anomalies detected** across 6 categories | **3 CRITICAL** | **30 WARNING** | **97 INFO**

![Anomaly Detection Dashboard](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/anomaly_detection_dashboard.png)

---

## 1. CRITICAL Anomalies — Sensor Failure

> [!CAUTION]
> **3 subjects have complete or majority BPM sensor failure — their cardiac data is unusable.**

| Subject | BPM=0 Events | Total Events | % Missing | Impact |
|---|---|---|---|---|
| **SUB037** | **76/76** | 76 | **100%** | Complete sensor failure — no cardiac data at all |
| **SUB038** | **69/69** | 69 | **100%** | Complete sensor failure — no cardiac data at all |
| **SUB007** | **24/45** | 45 | **53%** | Majority sensor failure — cardiac data unreliable |

Additionally, SUB008 (11%), SUB034 (3%), and SUB040 (2%) have sporadic BPM dropouts.

**Total**: 180/2,969 rows (6.1%) have **BPM=0 and RR=0** — the heart rate monitor was disconnected or failed.

> [!IMPORTANT]
> **Recommendation**: Exclude SUB037 and SUB038 from any cardiac/BPM analysis. SUB007 should be treated with caution. For composite_stress calculations, these subjects' scores are based solely on facial data.

---

## 2. Data Integrity Issues

### Missing Values
| Column | Missing | % | Explanation |
|---|---|---|---|
| `player_name` | 255 | 8.6% | SPIKE events have no player |
| `victim` | 255 | 8.6% | SPIKE events have no victim |
| `weapon` | 288 | 9.7% | SPIKE + some KILL events |

> [!NOTE]
> These are **expected** — SPIKE_PLANTED and SPIKE_DEFUSED events naturally lack player/victim/weapon fields. Not a data quality issue.

### Duplicate Timestamps
**36 rows** across 12 subjects share duplicate timestamps:

| Subject | Duplicate Rows | Unique Dup Timestamps |
|---|---|---|
| SUB001, SUB006, SUB015, SUB034, SUB035, SUB048 | 4 each | 2 each |
| SUB003, SUB012, SUB016, SUB021, SUB028, SUB042 | 2 each | 1 each |

> [!NOTE]
> These are **SPIKE_PLANTED + another event occurring at the exact same millisecond**. This is expected in-game behaviour (e.g., a SPIKE_PLANTED and a KILL happening simultaneously). Not a bug.

---

## 3. Statistical Outliers

| Metric | IQR Extreme (3x) | Z-score > 3 |
|---|---|---|
| stress_score | 9 (> 99.0) | 72 |
| composite_stress | 0 | 23 |
| bpm | 0 | 12 |
| rr_ms | 0 | 0 |

> [!NOTE]
> Only **9 truly extreme statistical outliers** exist — all are stress scores near 99-100. These represent real peak-stress moments (fear/anger during intense gameplay). By Z-score, 72 values exceed 3 standard deviations, but this is expected for a right-skewed distribution.

---

## 4. Temporal Anomalies

### Burst Events (< 500ms between events)
- **384 event pairs** across 42 subjects occur within 500ms of each other
- Range: 9-21% of events per subject are "bursts"
- **This is normal** — Valorant can produce rapid kill sequences (multi-kills, spike plant + kill combos)

### Short Sessions
| Subject | Events | Concern |
|---|---|---|
| **SUB017** | 23 events | Only 298s (5 min) — fewest events of any subject |

### Large Gaps
Most subjects have 1-3 gaps > 60 seconds — these correspond to round transitions in-game.

---

## 5. Logical Consistency ✅

| Check | Violations | Status |
|---|---|---|
| Happy emotion + stress > 50 | **0** | PASS |
| NO_FACE + stress > 0 | **0** | PASS |
| Neutral + stress > 80 | **0** | PASS |
| ELEVATED bio + BPM < 70 | **0** | PASS |
| RECOVERY bio + BPM > 80 | **0** | PASS |
| DEATH victim != 'ME' | **0** | PASS |
| SPIKE with player_name | **0** | PASS |
| \|composite - stress\| > 40 | **29** | Expected — large difference indicates BPM contribution |

> [!TIP]
> **The data is logically clean.** Zero contradictions between emotion labels and stress scores. The stress model is consistent — happy/NO_FACE always maps to 0 stress, and bio classifications match BPM ranges perfectly.

---

## 6. Per-Subject Anomalies (Cohort Outliers)

### Stress Outliers (Z > 2)
| Subject | Mean Stress | Z-Score | Direction |
|---|---|---|---|
| **SUB032** | 47.8 | **+3.08** | Extremely high stress |
| **SUB009** | 37.3 | **+2.04** | High stress |

### High Zero-Stress Subjects
| Subject | % Zero Stress | Mean Stress |
|---|---|---|
| SUB031 | 72% | 7.8 |
| SUB037 | 55% | 11.2 |
| SUB034 | 54% | 9.2 |

### BPM Outliers
| Subject | Mean BPM | Z-Score | Issue |
|---|---|---|---|
| SUB037 | 0.0 | -4.45 | Sensor failure |
| SUB038 | 0.0 | -4.45 | Sensor failure |
| SUB007 | 35.4 | -2.05 | Partial sensor failure dragging average down |

---

## 7. Multivariate Anomaly Detection

### Mahalanobis Distance
- **16 multivariate outliers** (0.6% of valid data, threshold = 4.30)
- These are data points where the *combination* of stress + composite + BPM + RR is unusual

| Subject | Outliers | % of Events | Meaning |
|---|---|---|---|
| **SUB003** | 6 | 15% | Unusual stress-BPM combinations |
| **SUB025** | 5 | 7% | Unusual stress-BPM combinations |
| SUB018 | 2 | 3% | — |

### Isolation Forest (5% contamination)
- **140 anomalous data points** detected across the dataset

| Subject | Outliers | % of Events |
|---|---|---|
| **SUB025** | 14 | **21%** |
| **SUB032** | 13 | **20%** |
| **SUB018** | 12 | **17%** |
| **SUB009** | 11 | **17%** |
| SUB019 | 8 | 13% |
| SUB003 | 7 | 18% |

> [!IMPORTANT]
> SUB025, SUB032, SUB009, and SUB018 consistently appear as anomalous across multiple detection methods. These subjects have **genuinely unusual stress response patterns** — they are not data errors but represent real high-responders.

---

## 8. Summary & Recommendations

### Anomalies by Category
```
TEMPORAL:      84 (burst events, gaps — mostly expected game behavior)
INTEGRITY:     27 (sensor failures, duplicates)
SUBJECT:        8 (cohort outliers)
MULTIVARIATE:   6 (unusual multivariate combinations)
OUTLIER:        5 (extreme statistical values)
```

### Action Items

| # | Action | Severity | Subjects |
|---|---|---|---|
| 1 | **Exclude from BPM/cardiac analysis** | CRITICAL | SUB037, SUB038 |
| 2 | **Flag cardiac data as unreliable** | WARNING | SUB007 |
| 3 | **Note as high-stress outliers** in results | INFO | SUB032, SUB009 |
| 4 | **Note as multivariate outliers** | INFO | SUB025, SUB003 |
| 5 | **Note short session** | INFO | SUB017 (only 23 events) |

### Overall Data Quality Verdict

> [!TIP]
> **The dataset is largely clean.** The main issues are sensor failures in 3 subjects (not data corruption), plus expected game-related temporal patterns. The stress model is logically consistent with zero emotion-stress contradictions. After excluding SUB037/SUB038 from cardiac analysis, the remaining 49 subjects have reliable multimodal data.

---

> **Output files**:
> - [anomaly_detection_dashboard.png](file:///P:/IEEE/SUBJECTS/stress_plots/anomaly_detection_dashboard.png)
> - [anomaly_log.csv](file:///P:/IEEE/SUBJECTS/stress_plots/anomaly_log.csv) — all 130 anomalies in CSV
> - [anomaly_detection.py](file:///P:/IEEE/SUBJECTS/anomaly_detection.py) — full detection script
