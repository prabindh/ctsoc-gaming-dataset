# Stress Level Bifurcation Analysis

We have bifurcated the dataset into three distinct stress tiers based on the `stress_score`:
- **Low (0-20)**: Baseline/Resting state
- **Medium (20-60)**: Elevated engagement/tension
- **High (60-100)**: Peak stress moments

![Stress Bifurcation Dashboard](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/bifurcation_dashboard.png)

---

## 1. Distribution of Events

Most of the time spent in-game registers as low stress, with occasional high-stress spikes.

| Tier | Count | Percentage |
|---|---|---|
| **Low (0-20)** | 2,082 | **70.1%** |
| **Medium (20-60)** | 648 | **21.8%** |
| **High (60-100)** | 239 | **8.0%** |

---

## 2. Physiological Response (Heart Rate)

Interestingly, heart rate does *not* increase with facial stress score. In fact, it slightly decreases during the highest facial stress moments.

| Tier | Average BPM |
|---|---|
| **Low (0-20)** | 69.9 BPM |
| **Medium (20-60)** | 69.0 BPM |
| **High (60-100)** | 67.3 BPM |

> [!NOTE]
> This confirms our earlier finding: **Facial stress and heart rate are decoupled in this dataset.** When players experience intense visual/emotional stress (High Tier), their heart rate doesn't necessarily spike; they might actually be holding their breath or freezing, leading to a slightly lower BPM.

---

## 3. What causes High Stress?

Out of the 239 High Stress events, here is what triggered them:

- **KILL**: 207 occurrences (86%)
- **SPIKE_PLANTED**: 14 occurrences (6%)
- **DEATH**: 12 occurrences (5%)
- **SPIKE_DEFUSED**: 6 occurrences (3%)

---

## 4. Emotional Composition of High Stress

The "High Stress" tier is almost entirely driven by two negative emotions:

- **Angry**: 142 occurrences (59%)
- **Fear**: 76 occurrences (32%)
- **Surprise**: 21 occurrences (9%)

> [!IMPORTANT]
> The bifurcation clearly shows that the `stress_score` is essentially an "Anger/Fear Index". If you look at the dashboard (Panel D), the Low stress tier is dominated by Neutral expressions, while the High stress tier is entirely Angry and Fearful expressions.
