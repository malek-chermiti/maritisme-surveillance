from pydantic import BaseModel
from datetime import datetime


class EvaluateRequest(BaseModel):
    mmsi: int
    pred_latitude: float
    pred_longitude: float
    anomaly_score: float


class EvaluateResponse(BaseModel):
    alert_created: bool
    alert_reason: str | None = None
    alert_level: str
    distance_km: float | None = None
    zone_name: str | None = None


class AlertOut(BaseModel):
    id: int
    mmsi: int
    zone_id: int | None
    alert_level: str
    distance_km: float | None
    anomaly_score: float | None
    alert_reason: str
    created_at: datetime

    class Config:
        from_attributes = True