import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.models import VesselState, VesselTrack
from app.schemas import (
    AgentQueryIn,
    AgentQueryOut,
    McpToolCallIn,
    McpToolCallOut,
    VesselPredictionOut,
    VesselStateOut,
    VesselTrackOut,
)
from app.services.export import tracks_to_csv_buffer
from app.services.mcp import execute_tool
from app.services.agent import agent_handle_query
from app.services.predict import predict_future_position
from app.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="3.0.0")


REALTIME_MAP_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AIS Realtime Map</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: Arial, sans-serif;
            background: #f8fafc;
        }
        #topbar {
            min-height: 56px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 16px;
            background: #0f172a;
            color: white;
            box-sizing: border-box;
            gap: 12px;
            flex-wrap: wrap;
        }
        #main {
            display: grid;
            grid-template-columns: 360px 1fr;
            height: calc(100vh - 56px);
        }
        #sidebar {
            padding: 16px;
            background: white;
            border-right: 1px solid #e2e8f0;
            overflow-y: auto;
            box-sizing: border-box;
        }
        #map {
            width: 100%;
            height: 100%;
        }
        h2 {
            margin: 0 0 12px 0;
            font-size: 18px;
        }
        h3 {
            margin: 18px 0 8px 0;
            font-size: 15px;
        }
        .small { font-size: 13px; opacity: 0.95; }
        .status-ok { color: #86efac; font-weight: 600; }
        .status-warn { color: #fcd34d; font-weight: 600; }
        .status-error { color: #fca5a5; font-weight: 600; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
            color: #334155;
        }
        input {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 14px;
        }
        button {
            padding: 10px 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .primary { background: #2563eb; color: white; }
        .secondary { background: #e2e8f0; color: #0f172a; }
        .actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .summary-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px;
            margin-top: 16px;
            font-size: 14px;
            line-height: 1.55;
        }
        .legend {
            background: white;
            padding: 10px 12px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            font-size: 13px;
            line-height: 1.5;
        }
        .dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 6px;
            border-radius: 50%;
            vertical-align: middle;
        }
        .line-sample {
            display: inline-block;
            width: 18px;
            height: 0;
            border-top: 3px solid;
            vertical-align: middle;
            margin-right: 6px;
        }
        .checkbox-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            font-size: 14px;
        }
        .checkbox-row input {
            width: auto;
        }
        #vesselList {
            margin-top: 10px;
            max-height: 320px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px;
            background: #fff;
        }
        .vessel-item {
            padding: 8px;
            border-bottom: 1px solid #eef2f7;
            font-size: 13px;
            line-height: 1.45;
        }
        .vessel-item:last-child { border-bottom: none; }
        @media (max-width: 960px) {
            #main {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            #sidebar {
                border-right: none;
                border-bottom: 1px solid #e2e8f0;
            }
        }
    </style>
</head>
<body>
    <div id="topbar">
        <div>
            <strong>AIS Vessel Tracking and Prediction Platform</strong>
            <span class="small"> | Final live map mode</span>
        </div>
        <div id="connectionStatus" class="status-warn">Connecting...</div>
    </div>

    <div id="main">
        <div id="sidebar">
            <h2>Live Filters</h2>

            <div>
                <label for="mmsiInput">MMSI</label>
                <input id="mmsiInput" type="number" placeholder="e.g. 230935000" />
            </div>

            <div style="margin-top: 10px;">
                <label for="nameInput">Vessel name contains</label>
                <input id="nameInput" type="text" placeholder="e.g. FINN" />
            </div>

            <h3>Area filter</h3>
            <div class="grid">
                <div>
                    <label for="minLatInput">Min latitude</label>
                    <input id="minLatInput" type="number" step="0.0001" placeholder="59.0" />
                </div>
                <div>
                    <label for="maxLatInput">Max latitude</label>
                    <input id="maxLatInput" type="number" step="0.0001" placeholder="66.0" />
                </div>
                <div>
                    <label for="minLonInput">Min longitude</label>
                    <input id="minLonInput" type="number" step="0.0001" placeholder="18.0" />
                </div>
                <div>
                    <label for="maxLonInput">Max longitude</label>
                    <input id="maxLonInput" type="number" step="0.0001" placeholder="30.0" />
                </div>
            </div>

            <div style="margin-top: 10px;">
                <label for="minutesAheadInput">Prediction horizon (minutes)</label>
                <input id="minutesAheadInput" type="number" min="1" max="120" value="15" />
            </div>

            <div style="margin-top: 10px;">
                <label for="limitInput">Optional safety limit</label>
                <input id="limitInput" type="number" min="1" max="50000" placeholder="leave empty for all" />
            </div>

            <div class="checkbox-row">
                <input id="autoFitCheckbox" type="checkbox" />
                <label for="autoFitCheckbox" style="margin: 0; font-weight: 500;">Auto-fit when selection changes</label>
            </div>

            <div class="actions">
                <button class="primary" onclick="applyFilters()">Apply filters</button>
                <button class="secondary" onclick="resetFilters()">Reset</button>
                <button class="secondary" onclick="refreshSelection()">Refresh selection</button>
                <button class="secondary" onclick="fitToVessels()">Fit now</button>
            </div>

            <div class="summary-box">
                <div><strong>WebSocket:</strong> <span id="socketMode">waiting</span></div>
                <div><strong>Last update:</strong> <span id="lastUpdate">-</span></div>
                <div><strong>Visible vessels:</strong> <span id="vesselCount">0</span></div>
                <div><strong>Prediction horizon:</strong> <span id="predictionHorizonSummary">15</span> min</div>
                <div><strong>Tracking mode:</strong> Stable selected vessel set</div>
            </div>

            <h3>Visible vessels</h3>
            <div id="vesselList"></div>
        </div>

        <div id="map"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map("map").setView([60.423, 22.14], 7);

        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        let socket = null;
        let currentBounds = [];
        let markersByMmsi = {};
        let predictionLinesByMmsi = {};
        let predictionMarkersByMmsi = {};

        const legend = L.control({ position: "bottomright" });
        legend.onAdd = function () {
            const div = L.DomUtil.create("div", "legend");
            div.innerHTML = `
                <div><span class="dot" style="background:#2563eb;"></span> Current vessel position</div>
                <div><span class="line-sample" style="border-color:#dc2626;"></span> Predicted trajectory</div>
                <div><span class="dot" style="background:#ef4444;"></span> Predicted end point</div>
            `;
            return div;
        };
        legend.addTo(map);

        function emptyToNull(value) {
            const trimmed = (value || "").trim();
            return trimmed === "" ? null : trimmed;
        }

        function parseIntOrNull(value) {
            const trimmed = (value || "").trim();
            if (trimmed === "") return null;
            const parsed = parseInt(trimmed, 10);
            return Number.isNaN(parsed) ? null : parsed;
        }

        function parseFloatOrNull(value) {
            const trimmed = (value || "").trim();
            if (trimmed === "") return null;
            const parsed = parseFloat(trimmed);
            return Number.isNaN(parsed) ? null : parsed;
        }

        function getFilters() {
            return {
                type: "filters",
                mmsi: parseIntOrNull(document.getElementById("mmsiInput").value),
                vessel_name: emptyToNull(document.getElementById("nameInput").value),
                min_lat: parseFloatOrNull(document.getElementById("minLatInput").value),
                max_lat: parseFloatOrNull(document.getElementById("maxLatInput").value),
                min_lon: parseFloatOrNull(document.getElementById("minLonInput").value),
                max_lon: parseFloatOrNull(document.getElementById("maxLonInput").value),
                minutes_ahead: parseIntOrNull(document.getElementById("minutesAheadInput").value) || 15,
                limit: parseIntOrNull(document.getElementById("limitInput").value)
            };
        }

        function applyFilters() {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify(getFilters()));
            }
        }

        function refreshSelection() {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const payload = getFilters();
                payload.type = "refresh_selection";
                socket.send(JSON.stringify(payload));
            }
        }

        function resetFilters() {
            document.getElementById("mmsiInput").value = "";
            document.getElementById("nameInput").value = "";
            document.getElementById("minLatInput").value = "";
            document.getElementById("maxLatInput").value = "";
            document.getElementById("minLonInput").value = "";
            document.getElementById("maxLonInput").value = "";
            document.getElementById("minutesAheadInput").value = 15;
            document.getElementById("limitInput").value = "";
            applyFilters();
        }

        function fitToVessels() {
            if (currentBounds.length > 0) {
                map.fitBounds(currentBounds, { padding: [20, 20] });
            }
        }

        function formatValue(value, digits = 2) {
            if (value === null || value === undefined) return "N/A";
            if (typeof value === "number") return value.toFixed(digits);
            return value;
        }

        function arrowSymbol(heading) {
            if (heading === null || heading === undefined) return "•";
            const directions = ["↑","↗","→","↘","↓","↙","←","↖"];
            const normalized = ((heading % 360) + 360) % 360;
            const index = Math.round(normalized / 45) % 8;
            return directions[index];
        }

        function clearMissingVessels(newMmsiSet) {
            for (const mmsi in markersByMmsi) {
                if (!newMmsiSet.has(mmsi)) {
                    map.removeLayer(markersByMmsi[mmsi]);
                    delete markersByMmsi[mmsi];
                }
            }

            for (const mmsi in predictionLinesByMmsi) {
                if (!newMmsiSet.has(mmsi)) {
                    map.removeLayer(predictionLinesByMmsi[mmsi]);
                    delete predictionLinesByMmsi[mmsi];
                }
            }

            for (const mmsi in predictionMarkersByMmsi) {
                if (!newMmsiSet.has(mmsi)) {
                    map.removeLayer(predictionMarkersByMmsi[mmsi]);
                    delete predictionMarkersByMmsi[mmsi];
                }
            }
        }

        function renderPayload(payload) {
            currentBounds = [];
            const vesselList = document.getElementById("vesselList");
            vesselList.innerHTML = "";

            const newMmsiSet = new Set();

            for (const vessel of payload.vessels) {
                if (vessel.lat === null || vessel.lon === null) continue;

                const mmsiKey = String(vessel.mmsi);
                newMmsiSet.add(mmsiKey);

                const name = vessel.vessel_name || `MMSI ${vessel.mmsi}`;
                const position = [vessel.lat, vessel.lon];
                currentBounds.push(position);

                if (!markersByMmsi[mmsiKey]) {
                    markersByMmsi[mmsiKey] = L.circleMarker(position, {
                        radius: 7,
                        color: "#1d4ed8",
                        fillColor: "#2563eb",
                        fillOpacity: 0.85,
                        weight: 2
                    }).addTo(map);
                } else {
                    markersByMmsi[mmsiKey].setLatLng(position);
                }

                markersByMmsi[mmsiKey].bindTooltip(name, { sticky: true });
                markersByMmsi[mmsiKey].bindPopup(`
                    <div>
                        <strong>${name}</strong><br>
                        MMSI: ${vessel.mmsi}<br>
                        Position: ${formatValue(vessel.lat, 5)}, ${formatValue(vessel.lon, 5)}<br>
                        SOG: ${formatValue(vessel.sog, 1)} kn<br>
                        COG: ${formatValue(vessel.cog, 1)}°<br>
                        Heading: ${formatValue(vessel.heading, 1)}° ${arrowSymbol(vessel.heading)}<br>
                        Updated: ${vessel.latest_event_time || "N/A"}
                    </div>
                `);

                const listItem = document.createElement("div");
                listItem.className = "vessel-item";
                listItem.innerHTML = `
                    <strong>${name}</strong><br>
                    MMSI: ${vessel.mmsi}<br>
                    Position: ${formatValue(vessel.lat, 4)}, ${formatValue(vessel.lon, 4)}<br>
                    Speed: ${formatValue(vessel.sog, 1)} kn
                `;
                vesselList.appendChild(listItem);

                if (vessel.prediction) {
                    const predictedPosition = [
                        vessel.prediction.predicted_lat,
                        vessel.prediction.predicted_lon
                    ];
                    currentBounds.push(predictedPosition);

                    if (!predictionLinesByMmsi[mmsiKey]) {
                        predictionLinesByMmsi[mmsiKey] = L.polyline(
                            [position, predictedPosition],
                            { color: "#dc2626", weight: 3, opacity: 0.9 }
                        ).addTo(map);
                    } else {
                        predictionLinesByMmsi[mmsiKey].setLatLngs([position, predictedPosition]);
                    }

                    if (!predictionMarkersByMmsi[mmsiKey]) {
                        predictionMarkersByMmsi[mmsiKey] = L.circleMarker(predictedPosition, {
                            radius: 5,
                            color: "#dc2626",
                            fillColor: "#ef4444",
                            fillOpacity: 0.9,
                            weight: 2
                        }).addTo(map);
                    } else {
                        predictionMarkersByMmsi[mmsiKey].setLatLng(predictedPosition);
                    }

                    predictionMarkersByMmsi[mmsiKey].bindPopup(`
                        <div>
                            <strong>Prediction for ${name}</strong><br>
                            MMSI: ${vessel.mmsi}<br>
                            Predicted position: ${formatValue(vessel.prediction.predicted_lat, 5)}, ${formatValue(vessel.prediction.predicted_lon, 5)}<br>
                            Predicted time: ${vessel.prediction.predicted_timestamp}<br>
                            Method: ${vessel.prediction.method}
                        </div>
                    `);
                } else {
                    if (predictionLinesByMmsi[mmsiKey]) {
                        map.removeLayer(predictionLinesByMmsi[mmsiKey]);
                        delete predictionLinesByMmsi[mmsiKey];
                    }
                    if (predictionMarkersByMmsi[mmsiKey]) {
                        map.removeLayer(predictionMarkersByMmsi[mmsiKey]);
                        delete predictionMarkersByMmsi[mmsiKey];
                    }
                }
            }

            clearMissingVessels(newMmsiSet);

            document.getElementById("vesselCount").textContent = payload.count;
            document.getElementById("lastUpdate").textContent = payload.generated_at;
            document.getElementById("predictionHorizonSummary").textContent = payload.minutes_ahead;
            document.getElementById("socketMode").textContent = payload.selection_mode || "stable";

            if (payload.selection_changed && document.getElementById("autoFitCheckbox").checked && currentBounds.length > 0) {
                map.fitBounds(currentBounds, { padding: [20, 20] });
            }
        }

        function updateStatus(text, cssClass) {
            const status = document.getElementById("connectionStatus");
            status.textContent = text;
            status.className = cssClass;
        }

        function connectSocket() {
            const protocol = window.location.protocol === "https:" ? "wss" : "ws";
            socket = new WebSocket(`${protocol}://${window.location.host}/ws/map`);

            socket.onopen = () => {
                updateStatus("WebSocket connected", "status-ok");
                applyFilters();
            };

            socket.onmessage = (event) => {
                const payload = JSON.parse(event.data);
                renderPayload(payload);
            };

            socket.onclose = () => {
                updateStatus("Disconnected, reconnecting...", "status-warn");
                setTimeout(connectSocket, 1500);
            };

            socket.onerror = () => {
                updateStatus("WebSocket error", "status-error");
            };
        }

        connectSocket();
    </script>
</body>
</html>
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _sanitize_filters(raw: dict[str, Any]) -> dict[str, Any]:
    def to_int(value: Any, default: int | None = None, minimum: int | None = None, maximum: int | None = None):
        if value in (None, ""):
            return default
        converted = int(value)
        if minimum is not None:
            converted = max(minimum, converted)
        if maximum is not None:
            converted = min(maximum, converted)
        return converted

    def to_float(value: Any):
        if value in (None, ""):
            return None
        return float(value)

    return {
        "mmsi": to_int(raw.get("mmsi")),
        "vessel_name": _clean_optional_str(raw.get("vessel_name")),
        "min_lat": to_float(raw.get("min_lat")),
        "max_lat": to_float(raw.get("max_lat")),
        "min_lon": to_float(raw.get("min_lon")),
        "max_lon": to_float(raw.get("max_lon")),
        "minutes_ahead": to_int(raw.get("minutes_ahead"), default=settings.prediction_default_minutes, minimum=1, maximum=120),
        "limit": to_int(raw.get("limit"), default=None, minimum=1, maximum=50000),
    }


def _base_filtered_query(filters: dict[str, Any]):
    stmt = select(VesselState).where(VesselState.lat.is_not(None), VesselState.lon.is_not(None))

    if filters["mmsi"] is not None:
        stmt = stmt.where(VesselState.mmsi == filters["mmsi"])
    if filters["vessel_name"]:
        stmt = stmt.where(VesselState.vessel_name.ilike(f"%{filters['vessel_name']}%"))
    if filters["min_lat"] is not None:
        stmt = stmt.where(VesselState.lat >= filters["min_lat"])
    if filters["max_lat"] is not None:
        stmt = stmt.where(VesselState.lat <= filters["max_lat"])
    if filters["min_lon"] is not None:
        stmt = stmt.where(VesselState.lon >= filters["min_lon"])
    if filters["max_lon"] is not None:
        stmt = stmt.where(VesselState.lon <= filters["max_lon"])

    stmt = stmt.order_by(VesselState.latest_event_time.desc().nullslast())
    if filters["limit"] is not None:
        stmt = stmt.limit(filters["limit"])
    return stmt


def _select_current_mmsis(db: Session, filters: dict[str, Any]) -> list[int]:
    stmt = _base_filtered_query(filters)
    vessels = list(db.execute(stmt).scalars().all())
    return [v.mmsi for v in vessels]


def _build_payload_for_selected_mmsis(
    db: Session,
    selected_mmsis: list[int],
    filters: dict[str, Any],
    selection_changed: bool,
) -> dict[str, Any]:
    vessel_items: list[dict[str, Any]] = []

    if not selected_mmsis:
        return {
            "generated_at": utc_now_iso(),
            "count": 0,
            "minutes_ahead": filters["minutes_ahead"],
            "filters": filters,
            "selection_changed": selection_changed,
            "selection_mode": "stable selected vessel set",
            "vessels": [],
        }

    stmt = (
        select(VesselState)
        .where(VesselState.mmsi.in_(selected_mmsis))
        .order_by(VesselState.latest_event_time.desc().nullslast())
    )
    vessels = list(db.execute(stmt).scalars().all())

    selected_set = set(selected_mmsis)
    vessels = [v for v in vessels if v.mmsi in selected_set]

    for vessel in vessels:
        vessel_item: dict[str, Any] = {
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
            "prediction": None,
        }

        track_stmt = (
            select(VesselTrack)
            .where(VesselTrack.mmsi == vessel.mmsi)
            .order_by(VesselTrack.event_time.desc())
            .limit(2)
        )
        track_rows = list(reversed(list(db.execute(track_stmt).scalars().all())))

        if len(track_rows) >= 2:
            try:
                prediction = predict_future_position(track_rows, minutes_ahead=filters["minutes_ahead"])
                vessel_item["prediction"] = {
                    "current_lat": prediction["current_lat"],
                    "current_lon": prediction["current_lon"],
                    "predicted_lat": prediction["predicted_lat"],
                    "predicted_lon": prediction["predicted_lon"],
                    "predicted_timestamp": prediction["predicted_timestamp"].isoformat(),
                    "method": prediction["method"],
                    "based_on_points": prediction["based_on_points"],
                    "minutes_ahead": prediction["minutes_ahead"],
                }
            except ValueError:
                vessel_item["prediction"] = None

        vessel_items.append(vessel_item)

    return {
        "generated_at": utc_now_iso(),
        "count": len(vessel_items),
        "minutes_ahead": filters["minutes_ahead"],
        "filters": filters,
        "selection_changed": selection_changed,
        "selection_mode": "stable selected vessel set",
        "vessels": vessel_items,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "timestamp": utc_now_iso(),
    }


@app.get("/vessels/latest", response_model=list[VesselStateOut])
def get_latest_vessels(
    limit: int | None = Query(None, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    stmt = select(VesselState).order_by(VesselState.latest_event_time.desc().nullslast())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


@app.get("/vessels/{mmsi}/latest", response_model=VesselStateOut)
def get_vessel_latest(mmsi: int, db: Session = Depends(get_db)):
    stmt = select(VesselState).where(VesselState.mmsi == mmsi)
    vessel = db.execute(stmt).scalar_one_or_none()
    if vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return vessel


@app.get("/vessels/{mmsi}/track", response_model=list[VesselTrackOut])
def get_vessel_track(
    mmsi: int,
    limit: int = Query(100, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    stmt = (
        select(VesselTrack)
        .where(VesselTrack.mmsi == mmsi)
        .order_by(VesselTrack.event_time.desc())
        .limit(limit)
    )
    rows = list(db.execute(stmt).scalars().all())
    if not rows:
        raise HTTPException(status_code=404, detail="No track data found for this vessel")
    return list(reversed(rows))


@app.get("/vessels/{mmsi}/predict", response_model=VesselPredictionOut)
def predict_vessel_position(
    mmsi: int,
    minutes_ahead: int = Query(settings.prediction_default_minutes, ge=1, le=120),
    points: int = Query(2, ge=2, le=20),
    db: Session = Depends(get_db),
):
    stmt = (
        select(VesselTrack)
        .where(VesselTrack.mmsi == mmsi)
        .order_by(VesselTrack.event_time.desc())
        .limit(points)
    )
    rows = list(reversed(list(db.execute(stmt).scalars().all())))
    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="Not enough points for prediction")

    result = predict_future_position(rows, minutes_ahead=minutes_ahead)
    return VesselPredictionOut(mmsi=mmsi, **result)


@app.get("/export/vessels/{mmsi}/track.csv")
def export_vessel_track_csv(
    mmsi: int,
    limit: int = Query(500, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    stmt = (
        select(VesselTrack)
        .where(VesselTrack.mmsi == mmsi)
        .order_by(VesselTrack.event_time.desc())
        .limit(limit)
    )
    rows = list(reversed(list(db.execute(stmt).scalars().all())))
    if not rows:
        raise HTTPException(status_code=404, detail="No data to export")

    payload = [
        {
            "mmsi": row.mmsi,
            "event_time": row.event_time.isoformat(),
            "lat": row.lat,
            "lon": row.lon,
            "sog": row.sog,
            "cog": row.cog,
            "heading": row.heading,
            "nav_stat": row.nav_stat,
            "rot": row.rot,
            "pos_acc": row.pos_acc,
            "raim": row.raim,
            "source_topic": row.source_topic,
        }
        for row in rows
    ]
    buffer = tracks_to_csv_buffer(payload)
    filename = f"vessel_{mmsi}_track.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers=headers)


@app.get("/map", response_class=HTMLResponse)
def realtime_map_page():
    return HTMLResponse(content=REALTIME_MAP_HTML)


@app.get("/map/data")
def realtime_map_data(
    mmsi: int | None = Query(None),
    vessel_name: str | None = Query(None),
    min_lat: float | None = Query(None),
    max_lat: float | None = Query(None),
    min_lon: float | None = Query(None),
    max_lon: float | None = Query(None),
    minutes_ahead: int = Query(15, ge=1, le=120),
    limit: int | None = Query(None, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    filters = _sanitize_filters(
        {
            "mmsi": mmsi,
            "vessel_name": vessel_name,
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
            "minutes_ahead": minutes_ahead,
            "limit": limit,
        }
    )
    selected_mmsis = _select_current_mmsis(db, filters)
    return _build_payload_for_selected_mmsis(db, selected_mmsis, filters, selection_changed=True)


@app.post("/mcp/execute", response_model=McpToolCallOut)
def mcp_execute(call: McpToolCallIn, db: Session = Depends(get_db)):
    return execute_tool(db, call.tool_name, call.params)


@app.post("/agent/query", response_model=AgentQueryOut)
def agent_query(query_in: AgentQueryIn, db: Session = Depends(get_db)):
    return agent_handle_query(query_in.query, db)


@app.websocket("/ws/map")
async def websocket_map(websocket: WebSocket):
    await websocket.accept()

    filters = _sanitize_filters({})
    selected_mmsis: list[int] = []
    selection_changed = True
    last_signature: str | None = None

    try:
        while True:
            try:
                incoming = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)

                if isinstance(incoming, dict):
                    msg_type = incoming.get("type")
                    if msg_type == "filters":
                        filters = _sanitize_filters(incoming)
                        with SessionLocal() as db:
                            selected_mmsis = _select_current_mmsis(db, filters)
                        selection_changed = True
                        last_signature = None

                    elif msg_type == "refresh_selection":
                        filters = _sanitize_filters(incoming)
                        with SessionLocal() as db:
                            selected_mmsis = _select_current_mmsis(db, filters)
                        selection_changed = True
                        last_signature = None

            except asyncio.TimeoutError:
                pass

            with SessionLocal() as db:
                if not selected_mmsis:
                    selected_mmsis = _select_current_mmsis(db, filters)
                    selection_changed = True

                payload = _build_payload_for_selected_mmsis(
                    db=db,
                    selected_mmsis=selected_mmsis,
                    filters=filters,
                    selection_changed=selection_changed,
                )

            signature = json.dumps(
                {
                    "vessels": payload["vessels"],
                    "minutes_ahead": payload["minutes_ahead"],
                    "selected_mmsis": selected_mmsis,
                },
                sort_keys=True,
                default=str,
            )

            if signature != last_signature or selection_changed:
                await websocket.send_json(payload)
                last_signature = signature
                selection_changed = False

    except WebSocketDisconnect:
        return