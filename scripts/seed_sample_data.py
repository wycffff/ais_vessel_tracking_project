from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import VesselState, VesselTrack

SAMPLE_VESSELS = [
    {
        'mmsi': 230123250,
        'vessel_name': 'DEMO BALTIC STAR',
        'call_sign': 'OJD1',
        'imo': 9354321,
        'vessel_type': 70,
        'destination': 'TURKU',
        'points': [
            (60.4350, 22.2250, 11.0, 45.0, 45.0),
            (60.4450, 22.2450, 11.2, 46.0, 46.0),
            (60.4550, 22.2650, 11.3, 47.0, 47.0),
        ],
    },
    {
        'mmsi': 230123251,
        'vessel_name': 'DEMO ARCHIPELAGO',
        'call_sign': 'OJD2',
        'imo': 9354322,
        'vessel_type': 60,
        'destination': 'NAANTALI',
        'points': [
            (60.3800, 21.9500, 8.1, 78.0, 78.0),
            (60.3855, 21.9820, 8.0, 79.0, 79.0),
            (60.3910, 22.0150, 8.2, 80.0, 80.0),
        ],
    },
]

def seed():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        sample_mmsis = [v['mmsi'] for v in SAMPLE_VESSELS]

        db.execute(delete(VesselTrack).where(VesselTrack.mmsi.in_(sample_mmsis)))

        for vessel in SAMPLE_VESSELS:
            existing = db.execute(select(VesselState).where(VesselState.mmsi == vessel['mmsi'])).scalar_one_or_none()
            if existing is None:
                existing = VesselState(mmsi=vessel['mmsi'])
                db.add(existing)

            existing.vessel_name = vessel['vessel_name']
            existing.call_sign = vessel['call_sign']
            existing.imo = vessel['imo']
            existing.vessel_type = vessel['vessel_type']
            existing.destination = vessel['destination']

            for idx, (lat, lon, sog, cog, heading) in enumerate(vessel['points']):
                event_time = now - timedelta(minutes=(len(vessel['points']) - idx) * 5)
                db.add(
                    VesselTrack(
                        mmsi=vessel['mmsi'],
                        event_time=event_time,
                        lat=lat,
                        lon=lon,
                        sog=sog,
                        cog=cog,
                        heading=heading,
                        nav_stat=0,
                        rot=0.0,
                        pos_acc=True,
                        raim=False,
                        source_topic=f"seed/{vessel['mmsi']}/location",
                    )
                )
                existing.latest_event_time = event_time
                existing.lat = lat
                existing.lon = lon
                existing.sog = sog
                existing.cog = cog
                existing.heading = heading
                existing.nav_stat = 0

        db.commit()
        print('Sample data inserted successfully.')
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    seed()