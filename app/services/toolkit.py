from typing import Any, Dict, List, Optional

from sqlalchemy import Float, select
from sqlalchemy.orm import Session

from app.models import VesselState


def find_vessels_by_port(db: Session, port_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = select(VesselState).where(VesselState.destination.ilike(f"%{port_name}%"))
    q = q.order_by(VesselState.latest_event_time.desc()).limit(limit)
    rows = db.execute(q).scalars().all()
    return [_vessel_state_to_dict(v) for v in rows]


def find_nearest_vessel(db: Session, city_name: str, limit: int = 1) -> List[Dict[str, Any]]:
    city_coords = {
        "turku": (60.4518, 22.2666),
        "helsinki": (60.1699, 24.9384),
        "mariehamn": (60.0978, 19.9398),
        "stockholm": (59.3293, 18.0686),
    }

    if city_name.lower() not in city_coords:
        raise ValueError(f"Unsupported city for nearest-vessel lookup: {city_name}")

    lat, lon = city_coords[city_name.lower()]
    distance_expr = (VesselState.lat - lat) * (VesselState.lat - lat) + (VesselState.lon - lon) * (VesselState.lon - lon)

    q = (
        select(VesselState)
        .where(VesselState.lat.isnot(None), VesselState.lon.isnot(None))
        .order_by(distance_expr)
        .limit(limit)
    )
    rows = db.execute(q).scalars().all()
    return [_vessel_state_to_dict(v) for v in rows]


def find_vessel_location(db: Session, vessel_query: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = (
        select(VesselState)
        .where(
            VesselState.vessel_name.ilike(f"%{vessel_query}%")
            | VesselState.call_sign.ilike(f"%{vessel_query}%")
            | VesselState.destination.ilike(f"%{vessel_query}%")
        )
        .order_by(VesselState.latest_event_time.desc())
        .limit(limit)
    )
    rows = db.execute(q).scalars().all()
    return [_vessel_state_to_dict(v) for v in rows]


def _vessel_state_to_dict(vessel: VesselState) -> Dict[str, Any]:
    return {
        "mmsi": vessel.mmsi,
        "vessel_name": vessel.vessel_name,
        "call_sign": vessel.call_sign,
        "imo": vessel.imo,
        "vessel_type": vessel.vessel_type,
        "destination": vessel.destination,
        "latest_event_time": vessel.latest_event_time.isoformat() if vessel.latest_event_time else None,
        "lat": vessel.lat,
        "lon": vessel.lon,
        "sog": vessel.sog,
        "cog": vessel.cog,
        "heading": vessel.heading,
        "nav_stat": vessel.nav_stat,
    }


TOOL_REGISTRY = {
    "find_vessels_by_port": {
        "name": "find_vessels_by_port",
        "description": "按目的港过滤当前在航船只",
        "func": find_vessels_by_port,
    },
    "find_nearest_vessel": {
        "name": "find_nearest_vessel",
        "description": "查找指定城市附近最近的船只",
        "func": find_nearest_vessel,
    },
    "find_vessel_location": {
        "name": "find_vessel_location",
        "description": "按船名、呼号或目的地查找船只位置",
        "func": find_vessel_location,
    },
}


def get_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    return TOOL_REGISTRY.get(tool_name)


def call_tool(db: Session, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tool = get_tool(tool_name)
    if tool is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    func = tool["func"]
    result = func(db, **params)
    return {
        "tool_name": tool_name,
        "description": tool["description"],
        "params": params,
        "result": result,
    }
