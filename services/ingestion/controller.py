from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from service import get_vessel_history

router = APIRouter(prefix="/vessels", tags=["vessels"])


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
