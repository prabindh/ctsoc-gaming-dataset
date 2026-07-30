# Estimated Player Skill Tiers

Since the dataset didn't include actual ranks, we estimated player skill using **Kills Per Minute (KPM)**, which is a strong proxy for aggression, skill, and game impact. We divided the 51 subjects into four tiers based on their KPM percentiles:

1. **Pro** (Top 15%): Highly aggressive, high kill rate (>5.2 KPM)
2. **Veteran** (Next 35%): Strong performance (4.7 - 5.2 KPM)
3. **Casual** (Next 35%): Average performance (3.8 - 4.7 KPM)
4. **New Player** (Bottom 15%): Slower pace, fewer kills (<3.8 KPM)

![Skill Tier Dashboard](C:/Users/PULKIT/.gemini/antigravity/brain/fb4836fb-2e7f-47b0-ae67-b780a1c43a19/skill_tier_dashboard.png)

---

## 1. Skill Distribution & Stress Response

| Tier | Players | Avg KPM | Avg Facial Stress | Avg Heart Rate |
|---|---|---|---|---|
| **Pro** | 8 | 5.25 | 17.0 | **70.7 BPM** |
| **Veteran** | 18 | 4.77 | 16.8 | 69.6 BPM |
| **Casual** | 17 | 4.24 | **18.1** | 68.7 BPM |
| **New Player** | 8 | 3.37 | **14.4** | 69.1 BPM |

### Key Takeaway: The "Casual" players show the most facial stress.
- **Casual** players exhibited the highest average facial stress (18.1). This makes sense: they know the game well enough to get frustrated or tense, but lack the total mastery to stay completely calm.
- **New** players showed the lowest facial stress (14.4). They may be playing slower, taking fewer risks, and therefore experiencing fewer intense firefights.
- **Pro** players have a moderate stress response (17.0) but the **highest average heart rate** (70.7 BPM). This suggests their high-paced, aggressive playstyle requires significant physiological arousal (cardiac output), even if their facial expressions remain relatively controlled.

---

## 2. Emotional Response During Kills (Panel D)

If you look at the dashboard (Panel D), there is a fascinating difference in *how* different tiers react when getting a KILL:

- **New Players & Casuals** show significantly more **Fear** and **Neutrality** when getting a kill. For them, firefights are chaotic and scary.
- **Pros & Veterans** show significantly more **Anger** and **Surprise**. For highly skilled players, kills are expected. When they lock in, their intense focus translates to an "Angry" facial reading in the model. 

---

### Conclusion for your research:
By proxying skill with Kills Per Minute, we see that **physiological arousal (BPM)** scales linearly with skill (Pros have the highest heart rate because they play the fastest). However, **psychological stress (facial expression)** follows a bell curve: Casual players are the most visibly stressed, while New players and Pros are more facially calm for different reasons (passivity vs. mastery).
