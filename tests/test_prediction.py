from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.predict import predict_future_position


def test_predict_future_position():
    t1 = datetime(2026, 3, 1, 12, 0, 0)
    t2 = t1 + timedelta(minutes=5)

    points = [
        SimpleNamespace(event_time=t1, lat=60.0000, lon=22.0000),
        SimpleNamespace(event_time=t2, lat=60.0100, lon=22.0200),
    ]

    result = predict_future_position(points, minutes_ahead=10)

    assert result['predicted_lat'] > 60.0100
    assert result['predicted_lon'] > 22.0200
    assert result['minutes_ahead'] == 10
