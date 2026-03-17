from __future__ import annotations

from math import cos, radians
from typing import Sequence
from app.models import VesselTrack


EARTH_KM_PER_DEG_LAT = 111.32


def _safe_lon_divisor(latitude: float) -> float:
    value = EARTH_KM_PER_DEG_LAT * cos(radians(latitude))
    return value if abs(value) > 1e-6 else 1e-6


def predict_future_position(points: Sequence[VesselTrack], minutes_ahead: int = 15):
    if len(points) < 2:
        raise ValueError('At least two points are required for prediction.')

    ordered = sorted(points, key=lambda p: p.event_time)
    p1 = ordered[-2]
    p2 = ordered[-1]

    seconds = (p2.event_time - p1.event_time).total_seconds()
    if seconds <= 0:
        raise ValueError('Track timestamps must be strictly increasing.')

    lat_per_sec = (p2.lat - p1.lat) / seconds
    lon_per_sec = (p2.lon - p1.lon) / seconds
    future_seconds = minutes_ahead * 60

    predicted_lat = p2.lat + lat_per_sec * future_seconds
    predicted_lon = p2.lon + lon_per_sec * future_seconds
    from datetime import timedelta
    predicted_timestamp = p2.event_time + timedelta(seconds=future_seconds)

    return {
        'current_lat': p2.lat,
        'current_lon': p2.lon,
        'predicted_lat': predicted_lat,
        'predicted_lon': predicted_lon,
        'predicted_timestamp': predicted_timestamp,
        'method': 'linear_extrapolation_from_last_two_points',
        'based_on_points': len(ordered),
        'minutes_ahead': minutes_ahead,
    }
