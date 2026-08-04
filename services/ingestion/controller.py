from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from service import get_vessel_history

router = APIRouter(prefix="/vessels", tags=["vessels"])

import schemas
from service import update_simulation_zone, get_simulation_zone


@router.put("/zone", response_model=schemas.ZoneOut)
def update_zone(zone: schemas.ZoneUpdate, db: Session = Depends(get_db)):
    """Met à jour la zone de simulation dessinée par l'utilisateur sur la carte."""
    return update_simulation_zone(db, zone.lat_min, zone.lat_max, zone.lon_min, zone.lon_max)


@router.get("/zone", response_model=schemas.ZoneOut)
def read_zone(db: Session = Depends(get_db)):
    """Récupère la zone de simulation actuellement active."""
    return get_simulation_zone(db)
@router.get("/{mmsi}/history")
def read_vessel_history(mmsi: int, limit: int = 20, db: Session = Depends(get_db)):
    '''
    Endpoint HTTP utilise par les autres services (ex: prediction-service)
    pour recuperer l'historique recent d'un navire.
    '''
    history = get_vessel_history(db, mmsi, limit)
    return [
        {
            "mmsi": h.mmsi,
            "lat": h.latitude,
            "lon": h.longitude,
            "speed": h.speed,
            "heading": h.heading,
            "recorded_at": h.recorded_at.isoformat()
        }
        for h in history
    ]
