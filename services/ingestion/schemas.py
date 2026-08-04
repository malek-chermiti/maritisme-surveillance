from pydantic import BaseModel, Field


class ZoneUpdate(BaseModel):
    lat_min: float = Field(..., ge=-90, le=90)
    lat_max: float = Field(..., ge=-90, le=90)
    lon_min: float = Field(..., ge=-180, le=180)
    lon_max: float = Field(..., ge=-180, le=180)


class ZoneOut(BaseModel):
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float