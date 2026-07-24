from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import VesselPositionSchema, SimulationZoneSchema
from ingestion_service import IngestionService

router = APIRouter()

@router.get("/vessels/{mmsi}/history", response_model=List[VesselPositionSchema], tags=["Positions"])
def get_vessel_history(mmsi: int, minutes: int = 30, db: Session = Depends(get_db)):
    """API lue par prediction-service pour récupérer l'historique d'un navire."""
    return IngestionService.get_vessel_history(db, mmsi, minutes)

@router.get("/simulation-zone/current", response_model=SimulationZoneSchema, tags=["Simulation Zone"])
def get_current_zone(db: Session = Depends(get_db)):
    """Zone de simulation active récupérée par le simulateur."""
    return IngestionService.get_current_simulation_zone(db)

@router.post("/simulation-zone", response_model=SimulationZoneSchema, tags=["Simulation Zone"])
def update_zone(zone_data: SimulationZoneSchema, db: Session = Depends(get_db)):
    """Mise à jour de la zone dessinée sur Leaflet."""
    if zone_data.lat_min >= zone_data.lat_max or zone_data.lon_min >= zone_data.lon_max:
        raise HTTPException(status_code=400, detail="Coordonnées de zone invalides.")
    return IngestionService.create_simulation_zone(db, zone_data)