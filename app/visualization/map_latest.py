from __future__ import annotations

import math
import os
import folium
from sqlalchemy import select

from app.db import SessionLocal
from app.models import VesselState
from app.settings import get_settings

settings = get_settings()


def _heading_endpoint(lat: float, lon: float, heading: float | None, length_km: float = 2.0):
    if heading is None:
        return lat, lon
    angle = math.radians(heading)
    dlat = (length_km / 111.32) * math.cos(angle)
    dlon = (length_km / (111.32 * max(math.cos(math.radians(lat)), 1e-6))) * math.sin(angle)
    return lat + dlat, lon + dlon


def generate_latest_map(output_path: str | None = None):
    db = SessionLocal()
    try:
        rows = list(
            db.execute(
                select(VesselState).where(VesselState.lat.is_not(None), VesselState.lon.is_not(None))
            ).scalars().all()
        )
    finally:
        db.close()

    if not rows:
        raise RuntimeError('No vessel state data found. Ingest or seed data first.')

    center_lat = sum(r.lat for r in rows if r.lat is not None) / len(rows)
    center_lon = sum(r.lon for r in rows if r.lon is not None) / len(rows)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    for row in rows:
        popup = (
            f"MMSI: {row.mmsi}<br>"
            f"Name: {row.vessel_name or 'Unknown'}<br>"
            f"SOG: {row.sog}<br>"
            f"COG: {row.cog}<br>"
            f"Heading: {row.heading}<br>"
            f"Updated: {row.latest_event_time}"
        )
        folium.Marker([row.lat, row.lon], popup=popup, tooltip=f'{row.vessel_name or row.mmsi}').add_to(m)

        if row.heading is not None:
            lat2, lon2 = _heading_endpoint(row.lat, row.lon, row.heading)
            folium.PolyLine([(row.lat, row.lon), (lat2, lon2)], weight=3).add_to(m)

    os.makedirs(settings.map_output_dir, exist_ok=True)
    path = output_path or os.path.join(settings.map_output_dir, 'latest_vessels_map.html')
    m.save(path)
    print(f'Map saved to {path}')


if __name__ == '__main__':
    generate_latest_map()
