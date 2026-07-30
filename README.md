# CTSOC Multi-Modal Gaming Biometric Dataset

## Overview
This repository contains the dataset schemas, PyTorch data loaders, exploratory statistical analysis scripts, technical documentation, and presentation slide decks for the CTSOC Multi-Modal Gaming Biometric Study.

The dataset captures synchronized in-game events (Valorant telemetry via Overwolf), cardiac biosignals (PPG/ECG Heart Rate & RR intervals via HealthyPi Move), and computer vision facial micro-expression analysis across 51 gaming subjects (2,969 total logged events).

## Repository Structure

```text
ctsoc-gaming-dataset/
├── README.md                     # Repository documentation
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
├── docs/                         # Markdown analytical research reports
└── presentations/                # PowerPoint slide decks (.pptx)
```

## Quick Start: Loading Data in PyTorch

```python
from src.pytorch_dataset_loader import ValorantBiometricDataset
from torch.utils.data import DataLoader

# Load preprocessed dataset into PyTorch Tensors
dataset = ValorantBiometricDataset(csv_dir='data/', exclude_failures=True)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

for x_batch, y_batch in train_loader:
    # x_batch shape: [32, 4] -> [BPM, RR_ms, Emotion_ID, Event_ID]
    # y_batch shape: [32, 2] -> [Stress_Score, Composite_Stress]
    break
```

## License
Distributed under the MIT License. See `LICENSE` for more information.
