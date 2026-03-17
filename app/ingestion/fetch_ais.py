from __future__ import annotations

import json
import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from sqlalchemy import select

from app.db import SessionLocal
from app.models import VesselMetadata, VesselState, VesselTrack
from app.settings import get_settings

settings = get_settings()


def _topic_parts(topic: str) -> list[str]:
    return topic.split('/')


def _extract_mmsi(topic: str) -> int | None:
    parts = _topic_parts(topic)
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except (TypeError, ValueError):
        return None


def _epoch_seconds_to_dt(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)


def _epoch_millis_to_dt(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).replace(tzinfo=None)


def save_location_message(topic: str, payload: dict[str, Any]) -> None:
    mmsi = _extract_mmsi(topic)
    event_time = _epoch_seconds_to_dt(payload.get('time'))
    if mmsi is None or event_time is None:
        return

    db = SessionLocal()
    try:
        track = VesselTrack(
            mmsi=mmsi,
            event_time=event_time,
            lat=payload['lat'],
            lon=payload['lon'],
            sog=payload.get('sog'),
            cog=payload.get('cog'),
            heading=payload.get('heading'),
            nav_stat=payload.get('navStat'),
            rot=payload.get('rot'),
            pos_acc=payload.get('posAcc'),
            raim=payload.get('raim'),
            source_topic=topic,
        )
        db.add(track)

        stmt = select(VesselState).where(VesselState.mmsi == mmsi)
        state = db.execute(stmt).scalar_one_or_none()
        if state is None:
            state = VesselState(mmsi=mmsi)
            db.add(state)

        state.latest_event_time = event_time
        state.lat = payload['lat']
        state.lon = payload['lon']
        state.sog = payload.get('sog')
        state.cog = payload.get('cog')
        state.heading = payload.get('heading')
        state.nav_stat = payload.get('navStat')
        db.commit()
        print(f"[OK] Stored location | MMSI={mmsi} lat={payload['lat']} lon={payload['lon']} sog={payload.get('sog')}")
    except Exception as exc:
        db.rollback()
        print(f'[ERROR] Failed to store location message: {exc}')
    finally:
        db.close()


def save_metadata_message(topic: str, payload: dict[str, Any]) -> None:
    mmsi = _extract_mmsi(topic)
    metadata_timestamp = _epoch_millis_to_dt(payload.get('timestamp'))
    if mmsi is None or metadata_timestamp is None:
        return

    db = SessionLocal()
    try:
        meta = VesselMetadata(
            mmsi=mmsi,
            metadata_timestamp=metadata_timestamp,
            vessel_name=payload.get('name'),
            destination=payload.get('destination'),
            call_sign=payload.get('callSign'),
            imo=payload.get('imo'),
            vessel_type=payload.get('type'),
            draught=payload.get('draught'),
            source_topic=topic,
        )
        db.add(meta)

        stmt = select(VesselState).where(VesselState.mmsi == mmsi)
        state = db.execute(stmt).scalar_one_or_none()
        if state is None:
            state = VesselState(mmsi=mmsi)
            db.add(state)

        state.vessel_name = payload.get('name')
        state.destination = payload.get('destination')
        state.call_sign = payload.get('callSign')
        state.imo = payload.get('imo')
        state.vessel_type = payload.get('type')
        db.commit()
        print(f"[OK] Stored metadata | MMSI={mmsi} name={payload.get('name')}")
    except Exception as exc:
        db.rollback()
        print(f'[WARN] Metadata insert skipped or failed: {exc}')
    finally:
        db.close()


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    print(f'Connected to MQTT broker with reason code: {reason_code}')
    client.subscribe(settings.mqtt_topic)
    print(f'Subscribed to: {settings.mqtt_topic}')


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    topic = msg.topic
    if topic.endswith('/status') or topic == 'status':
        return
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except Exception as exc:
        print(f'[ERROR] Invalid JSON payload on topic {topic}: {exc}')
        return

    if topic.endswith('/locations') or topic.endswith('/location'):
        save_location_message(topic, payload)
    elif topic.endswith('/metadata'):
        save_metadata_message(topic, payload)


def build_client() -> mqtt.Client:
    client = mqtt.Client(client_id=settings.mqtt_client_id, transport='websockets', protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.ws_set_options(path=settings.mqtt_path)
    return client


def main():
    print('Starting AIS MQTT ingestion...')
    client = build_client()
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_forever()


if __name__ == '__main__':
    main()
