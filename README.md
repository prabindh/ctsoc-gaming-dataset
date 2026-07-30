# Multi-Modal Gaming Biometric Stress Dataset (Tactical FPS Case Study)

## Overview
This repository contains the dataset schemas, PyTorch data loaders, exploratory statistical analysis scripts, technical documentation, and presentation slide decks for the Multi-Modal Gaming Biometric Stress Study.

The dataset captures synchronized in-game events (tactical FPS game telemetry via Overwolf integration), cardiac biosignals (PPG/ECG Heart Rate & RR intervals via HealthyPi Move), and computer vision facial micro-expression affect analysis across 51 gaming participants (2,969 total logged events).

## Directly Measured vs. Derived Components

To assist researchers and data scientists, the 11 feature columns are explicitly categorized into **Directly Measured** (raw biosignals & telemetry) vs **Derived** (algorithmic / fused metrics):

### 1. Directly Measured Components (Raw Signals)
* `timestamp_ms`: Hardware Unix epoch clock in milliseconds.
* `event`: In-game event trigger directly recorded from game telemetry hook (`KILL`, `DEATH`, `SPIKE_PLANTED`, `SPIKE_DEFUSED`).
* `player_name`: Participant player ID string directly recorded from telemetry API.
* `victim`: Opponent player ID string directly recorded from telemetry API (`ME` for death events).
* `weapon`: Game engine weapon/item ID directly recorded from telemetry API (e.g. `TX_Hud_AutoPistol`).
* `bpm`: Heart Rate in Beats Per Minute directly measured by PPG/ECG sensor hardware.
* `rr_ms`: R-R inter-beat interval in milliseconds directly measured by PPG/ECG pulse hardware.
* `dominant_emotion`: Primary facial emotion classification directly observed by computer vision (`neutral`, `angry`, `fear`, `surprise`, `happy`, `sad`, `NO_FACE`).

### 2. Derived Components (Algorithmic Metrics)
* `bio_status`: **DERIVED** — Categorical cardiac state (`NORMAL`, `ELEVATED`, `RECOVERY`, `CALIBRATING`, `INTENSE_SPIKE`) computed relative to a calibrated baseline.
* `stress_score`: **DERIVED** — Psychological stress index (0.0 to 100.0) calculated via Russell's Circumplex Affect Model applied to facial emotion vectors.
* `composite_stress`: **DERIVED** — Fused multimodal stress index combining `bio_status`, `stress_score` (x0.4), and event weight.

---

## Game Environment & Framework Portability

### Test Game Environment Context
A popular tactical FPS title (*Valorant*) was utilized as the initial test game environment after obtaining platform developer telemetry access.

### What Changes if a Different Game is Used?
The multi-modal stress recording framework is designed to be **modular and game-agnostic**:

* **UNCHANGED**: Cardiac biosignals (`bpm`, `rr_ms`, `bio_status`), facial affect tracking (`dominant_emotion`, `stress_score`), and real-time millisecond temporal synchronization operate 100% identically across any gaming genre.
* **CHANGED**: Game event tags (`event`) and HUD item names (`weapon`) map to the target game's schema (e.g., `BOMB_PLANTED` in Counter-Strike 2 vs `SPIKE_PLANTED`, `AK-47` vs `Vandal`, or elimination events in Apex Legends / Fortnite).

---

## Repository Structure

```text
ctsoc-gaming-dataset/
├── README.md                     # Repository documentation & Data Dictionary
├── LICENSE                       # MIT License
├── schemas/                      # Master JSON schema & 51 subject metadata schemas
├── src/                          # Data collection, PyTorch loader & analysis scripts
│   ├── w1.py                     # PPG/BLE Bluetooth heart rate streamer
│   ├── r1.py                     # Overwolf game telemetry receiver & CSV logger
│   ├── f1.py                     # OpenCV/DeepFace facial affect analyzer
│   ├── pytorch_dataset_loader.py # PyTorch Dataset & DataLoader class
│   ├── study_data.py            # Main statistical analysis suite
│   ├── anomaly_detection.py      # Multi-method anomaly detection & outlier pipeline
│   ├── bifurcate_stress.py       # Low/Med/High stress score bifurcation script
│   └── classify_players.py       # KPM skill level classification script
├── docs/                         # Markdown analytical research reports & visual collage
│   └── dataset_overview_collage.png  # Multi-panel half-page figure collage
└── presentations/                # PowerPoint slide decks (.pptx)
    └── Master_Gaming_Biometrics_Presentation.pptx
```

## Quick Start: Loading Data in PyTorch

```python
from src.pytorch_dataset_loader import ValorantBiometricDataset
from torch.utils.data import DataLoader

# Load preprocessed dataset into PyTorch Tensors
dataset = ValorantBiometricDataset(csv_dir='data/', exclude_failures=True)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

for x_batch, y_batch in train_loader:
    # x_batch shape: [32, 4] -> [BPM, RR_ms, Emotion_ID, Event_ID] (Measured Features)
    # y_batch shape: [32, 2] -> [Stress_Score, Composite_Stress] (Derived Targets)
    break
```

## License
Distributed under the MIT License. See `LICENSE` for more information.
