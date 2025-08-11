# ml_predictor.py
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from pathlib import Path

_torch = None
_model = None
_preprocessor = None
_device = "cpu"

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "ml_model" / "findmyspot_model.pth"))
ZONE_MAP_PATH = Path(os.getenv("ZONE_MAP_PATH", BASE_DIR / "config" / "zone_locations.json"))

def _lazy_torch():
    global _torch
    if _torch is None:
        import torch  # noqa
        _torch = torch
    return _torch

def _build_parking_lstm(input_size=6, hidden_size=32, num_layers=2, dropout=0.2):
    torch = _lazy_torch()
    import torch.nn as nn

    class ParkingLSTM(nn.Module):
        def __init__(self, input_size=6, hidden_size=32, num_layers=2, output_size=1, dropout=0.2):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0.0,
                batch_first=True
            )
            self.fc_layers = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, output_size),
                nn.Sigmoid()
            )

        def forward(self, x):
            lstm_out, _ = self.lstm(x)
            last = lstm_out[:, -1, :]
            return self.fc_layers(last)

    return ParkingLSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, dropout=dropout)

def _load_checkpoint_once():
    global _model, _preprocessor, _device
    if _model is not None and _preprocessor is not None:
        return _model, _preprocessor

    if not os.path.exists(MODEL_PATH):
        return None, None

    torch = _lazy_torch()
    _device = "cuda" if torch.cuda.is_available() else "cpu"

    ckpt = torch.load(MODEL_PATH, map_location=_device)
    cfg = ckpt.get("model_config", {})
    model = _build_parking_lstm(
        input_size=cfg.get("input_size", 6),
        hidden_size=cfg.get("hidden_size", 32),
        num_layers=cfg.get("num_layers", 2),
        dropout=0.2
    )
    state = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state)
    model.to(_device).eval()

    preprocessor = ckpt.get("preprocessor", None)
    _model, _preprocessor = model, preprocessor
    return _model, _preprocessor

def _next_datetime_for(day_type: str, hour: int) -> datetime:
    day = (day_type or "weekday").strip().lower()
    now = datetime.now()
    day_map = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
    target_idx = day_map.get(day)
    if target_idx is None:
        target_idx = 2 if day == "weekday" else now.weekday()
    days_ahead = (target_idx - now.weekday()) % 7
    return (now + timedelta(days=days_ahead)).replace(hour=int(hour), minute=0, second=0, microsecond=0)

def _feature_vector(ts: datetime, location_name: str, location_encoder: Dict[str, int]) -> np.ndarray:
    hour_sin = np.sin(2 * np.pi * ts.hour / 24.0)
    hour_cos = np.cos(2 * np.pi * ts.hour / 24.0)
    day_sin  = np.sin(2 * np.pi * ts.weekday() / 7.0)
    day_cos  = np.cos(2 * np.pi * ts.weekday() / 7.0)
    if location_name not in location_encoder:
        raise KeyError(f"Location '{location_name}' not found in location_encoder")
    location_encoded = float(location_encoder[location_name])
    is_weekend = 1.0 if ts.weekday() >= 5 else 0.0
    return np.array([hour_sin, hour_cos, day_sin, day_cos, location_encoded, is_weekend], dtype=np.float32)

def _build_sequence(end_time: datetime, location_name: str, location_encoder: Dict[str,int], seq_len: int = 12) -> np.ndarray:
    rows = []
    for i in range(seq_len, 0, -1):
        ts = end_time - timedelta(hours=i)
        rows.append(_feature_vector(ts, location_name, location_encoder))
    return np.vstack(rows)

def _load_zone_map() -> Dict[str, str]:
    if os.path.exists(ZONE_MAP_PATH):
        with open(ZONE_MAP_PATH, "r") as f:
            return json.load(f)
    return {}

def _predict_for_endtime_location(location_name: str, end_time: datetime) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    model, pre = _load_checkpoint_once()
    if model is None or pre is None or not hasattr(pre, "scaler") or not hasattr(pre, "location_encoder"):
        return None, "Model or embedded preprocessor not found"
    try:
        seq = _build_sequence(end_time, location_name, pre.location_encoder)
        seq_scaled = pre.scaler.transform(seq)
    except Exception as e:
        return None, f"Preprocessing error: {e}"
    torch = _lazy_torch()
    with torch.no_grad():
        x = torch.tensor(seq_scaled, dtype=torch.float32, device=_device).unsqueeze(0)
        y = model(x).detach().cpu().numpy().reshape(-1)[0]
    availability = float(min(1.0, max(0.0, y)))
    status = "🟢 Good" if availability >= 0.6 else "🟡 Fair" if availability >= 0.3 else "🔴 Poor"
    confidence = round(1 - 2 * abs(availability - 0.5), 2)
    return {
        "predicted_availability": round(availability, 3),
        "available_spots": int(availability * 100),
        "status": status,
        "confidence_score": confidence
    }, None

def predict_by_location(location_name: str, hour: int, day_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    end_time = _next_datetime_for(day_type, int(hour))
    base, err = _predict_for_endtime_location(location_name, end_time)
    if err: return None, err
    return {
        "location": location_name,
        "hour": int(hour),
        "day_type": (day_type or "weekday").capitalize(),
        **base
    }, None

def predict_by_zone(zone_number: int, hour: int, day_type: str) -> Tuple[Optional[Dict[str,Any]], Optional[str]]:
    zone_map = _load_zone_map()
    loc = zone_map.get(str(int(zone_number)))
    if not loc:
        return None, f"Zone {zone_number} has no mapping in {ZONE_MAP_PATH}. Add it as {{\"{zone_number}\": \"Your Location Name\"}}."
    return predict_by_location(loc, hour, day_type)

def predict_many_by_zone(zone_number: int, hour: int, day_type: str, hours_ahead: int = 3) -> Tuple[Optional[List[Dict[str,Any]]], Optional[str]]:
    hours_ahead = max(1, min(int(hours_ahead), 3))
    zone_map = _load_zone_map()
    loc = zone_map.get(str(int(zone_number)))
    if not loc:
        return None, f"Zone {zone_number} has no mapping in {ZONE_MAP_PATH}. Add it as {{\"{zone_number}\": \"Your Location Name\"}}."
    start_dt = _next_datetime_for(day_type, int(hour))
    out = []
    for i in range(hours_ahead):
        end_time = start_dt + timedelta(hours=i)
        base, err = _predict_for_endtime_location(loc, end_time)
        if err:
            return None, err
        out.append({
            "Zone_Number": int(zone_number),
            "hour": (end_time.hour),
            "day_type": (day_type or "weekday").capitalize(),
            "location": loc,
            **base
        })
    return out, None

def list_known_locations() -> Tuple[Optional[list], Optional[str]]:
    _, pre = _load_checkpoint_once()
    if pre is None or not hasattr(pre, "location_encoder"):
        return None, "Embedded preprocessor not found"
    return list(pre.location_encoder.keys()), None

def health_check() -> Dict[str, Any]:
    model_exists = os.path.exists(MODEL_PATH)
    zone_map_exists = os.path.exists(ZONE_MAP_PATH)
    info = {
        "model_path": MODEL_PATH,
        "model_file_exists": model_exists,
        "zone_map_path": ZONE_MAP_PATH,
        "zone_map_exists": zone_map_exists,
    }
    if model_exists:
        m, pre = _load_checkpoint_once()
        info.update({
            "model_loaded": m is not None,
            "preprocessor_loaded": pre is not None,
            "has_scaler": bool(getattr(pre, "scaler", None)) if pre else False,
            "has_location_encoder": bool(getattr(pre, "location_encoder", None)) if pre else False,
        })
    return info
