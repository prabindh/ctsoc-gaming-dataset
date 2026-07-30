---
marp: true
theme: default
paginate: true
backgroundColor: #0f172a
color: #e2e8f0
---

# Trend & Temporal Analysis in Valorant
## Understanding Stress Over Time and Across Events
**Dataset:** 51 Subjects | 2,969 Game Events

---

# 1. Temporal Trends (Habituation vs Fatigue)

Does playing Valorant make you more stressed over time, or do you get used to it?
- We normalized all 51 sessions to a relative 0-100% time scale.
- **Finding:** Stress remains strikingly **flat** across the session.
- There is no "warm-up" period and no "fatigue/habituation" drop-off. 
- Valorant successfully sustains a constant baseline level of engagement and tension.

---

# 2. The Decoupling of Heart Rate and Facial Stress

Our most significant finding is that Cardiac Response and Facial Expression measure two different types of stress.
- Pearson Correlation (Stress Score ↔ BPM): **r = -0.027**
- They are **statistically independent**. 
- A high heart rate (physical arousal) does not guarantee an angry/fearful facial expression (psychological stress), and vice versa.

---

# 3. What Drives Facial Stress? (Emotions)

Facial Emotion is the #1 predictor of the Stress Score (ANOVA F=1859, p<0.001).
- **Fear** (Mean Stress: 70.4)
- **Anger** (Mean Stress: 62.4)
- **Neutral** (Mean Stress: 7.9)
- **Happy** (Mean Stress: 0.7)

The stress metric is essentially an index of intense negative/aggressive focus.

---

# 4. What Drives Facial Stress? (Events)

Event type alone does not significantly differentiate stress (p=0.070), but specific comparisons do:
- **KILLS** (Mean: 17.39) cause slightly more stress than **DEATHS** (Mean: 14.10) (p=0.007).
- Kills require intense visual focus and aggressive action, driving up the "Anger" facial marker more than the passive event of dying.

---

# 5. Visual Evidence: Event & Emotion Trends

![Event and Emotion Trends](file:///P:/IEEE/SUBJECTS/stress_plots/study_fig1_event_emotion.png)

---

# 6. Visual Evidence: Temporal Trends

![Temporal Trends](file:///P:/IEEE/SUBJECTS/stress_plots/study_fig2_temporal_bio.png)

---

# 7. Key Takeaway

Trend analysis reveals that Valorant stress is **episodic, not cumulative**. It is driven entirely by discrete micro-events (kills/fights) that trigger immediate emotional responses, rather than a slow build-up of physical tension over time.
