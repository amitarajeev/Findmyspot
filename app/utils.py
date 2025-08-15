# app/utils.py

import math
import pandas as pd
from typing import List, Optional, Any

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance (in meters) between two latitude-longitude points using the haversine formula.
    """
    R = 6371000.0  # Radius of the Earth in meters
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def infer_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Return the first matching column name from the candidate list that exists in the DataFrame.
    """
    return next((c for c in candidates if c in df.columns), None)

def as_bool(value: Any, default: bool = False) -> bool:
    """
    Convert various representations of truthy/falsy values into a boolean.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    return v in ("1", "true", "yes", "y", "on")
