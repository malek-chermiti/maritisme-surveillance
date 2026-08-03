from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class EvaluateRequest(BaseModel):
    mmsi: int
    predicted_lat_t30: float | None = Field(default=None)
    predicted_lon_t30: float | None = Field(default=None)
    pred_latitude: float | None = Field(default=None)
    pred_longitude: float | None = Field(default=None)
    anomaly_score: float

    @model_validator(mode="after")
    def normalize_prediction_fields(self):
        if self.predicted_lat_t30 is None and self.pred_latitude is not None:
            self.predicted_lat_t30 = self.pred_latitude
        if self.predicted_lon_t30 is None and self.pred_longitude is not None:
            self.predicted_lon_t30 = self.pred_longitude

        if self.predicted_lat_t30 is None:
            raise ValueError("A latitude must be provided via predicted_lat_t30 or pred_latitude")
        if self.predicted_lon_t30 is None:
            raise ValueError("A longitude must be provided via predicted_lon_t30 or pred_longitude")
        return self

    @property
    def pred_latitude_value(self) -> float:
        return self.predicted_lat_t30

    @property
    def pred_longitude_value(self) -> float:
        return self.predicted_lon_t30


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