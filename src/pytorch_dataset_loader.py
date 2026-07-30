"""
pytorch_dataset_loader.py
=========================
A PyTorch Dataset class for loading and preprocessing the Valorant Biometric Dataset.
"""

import os
import glob
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

class ValorantBiometricDataset(Dataset):
    """
    PyTorch Dataset loader for the Valorant Biometric Stress Dataset.
    Loads all subject CSVs from the specified directory and prepares tensor features.
    """
    def __init__(self, csv_dir, transform=None, exclude_sensor_failures=True):
        self.csv_dir = csv_dir
        self.transform = transform
        
        # List all CSV files
        csv_files = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))
        
        # Exclude known complete hardware failure subjects if requested
        if exclude_sensor_failures:
            csv_files = [f for f in csv_files if not any(sub in f for sub in ["SUB037", "SUB038"])]
            
        frames = []
        for fpath in csv_files:
            try:
                df = pd.read_csv(fpath, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(fpath, encoding="latin1")
            
            if "stress_score" in df.columns:
                frames.append(df)
                
        self.data = pd.concat(frames, ignore_index=True)
        
        # Preprocessing & Categorical Encoding
        self.event_map = {"KILL": 0, "DEATH": 1, "SPIKE_PLANTED": 2, "SPIKE_DEFUSED": 3}
        self.emotion_map = {"neutral": 0, "happy": 1, "sad": 2, "surprise": 3, "fear": 4, "angry": 5, "NO_FACE": 6}
        self.bio_map = {"NORMAL": 0, "ELEVATED": 1, "RECOVERY": 2, "CALIBRATING": 3, "INTENSE_SPIKE": 4}
        
        # Map categories to integer IDs
        self.data["event_id"] = self.data["event"].map(self.event_map).fillna(0).astype(int)
        self.data["emotion_id"] = self.data["dominant_emotion"].map(self.emotion_map).fillna(0).astype(int)
        self.data["bio_id"] = self.data["bio_status"].map(self.bio_map).fillna(0).astype(int)
        
        # Feature columns: [bpm, rr_ms, bio_id, emotion_id, event_id]
        feature_cols = ["bpm", "rr_ms", "bio_id", "emotion_id", "event_id"]
        self.features = self.data[feature_cols].values.astype(np.float32)
        
        # Targets: [stress_score, composite_stress]
        target_cols = ["stress_score", "composite_stress"]
        self.targets = self.data[target_cols].values.astype(np.float32)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.targets[idx], dtype=torch.float32)
        
        if self.transform:
            x = self.transform(x)
            
        return x, y

if __name__ == "__main__":
    dataset_path = r"P:\IEEE\SUBJECTS\All_CSVs"
    if os.path.exists(dataset_path):
        ds = ValorantBiometricDataset(csv_dir=dataset_path)
        loader = DataLoader(ds, batch_size=32, shuffle=True)
        
        print(f"Successfully loaded dataset! Total samples: {len(ds)}")
        for x_batch, y_batch in loader:
            print(f"Sample Batch Features shape: {x_batch.shape}")
            print(f"Sample Batch Targets shape:  {y_batch.shape}")
            break
