import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.alert.schemas import EvaluateRequest


def test_evaluate_request_accepts_prediction_payload():
    payload = EvaluateRequest(
        mmsi=999888778,
        predicted_lat_t30=34.860767,
        predicted_lon_t30=9.913769,
        anomaly_score=0.109,
    )

    assert payload.predicted_lat_t30 == 34.860767
    assert payload.predicted_lon_t30 == 9.913769


def test_evaluate_request_accepts_legacy_payload_names():
    payload = EvaluateRequest(
        mmsi=999888778,
        pred_latitude=34.860767,
        pred_longitude=9.913769,
        anomaly_score=0.109,
    )

    assert payload.predicted_lat_t30 == 34.860767
    assert payload.predicted_lon_t30 == 9.913769
