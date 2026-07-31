from pydantic import BaseModel
from datetime import datetime


class PredictionOut(BaseModel):
    mmsi: int
    predicted_lat_t30: float
    predicted_lon_t30: float
    anomaly_score: float


class PredictionLogOut(BaseModel):
    id: int
    mmsi: int
    pred_latitude: float
    pred_longitude: float
    anomaly_score: float
    created_at: datetime

    class Config:
        from_attributes = True