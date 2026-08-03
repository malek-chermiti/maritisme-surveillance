from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from security.internal_auth import verify_internal_secret
from service import evaluate_prediction, list_alerts, list_alerts_by_mmsi
import schemas

router = APIRouter(dependencies=[Depends(verify_internal_secret)])


@router.post("/alerts/evaluate", response_model=schemas.EvaluateResponse)
def evaluate(payload: schemas.EvaluateRequest, db: Session = Depends(get_db)):
    """
    Reçoit le résultat d'une prédiction (position future + score d'anomalie),
    calcule la distance à la zone protégée la plus proche, détermine s'il y a
    intrusion et/ou dégazage, et sauvegarde une alerte si un seuil est dépassé.
    """
    return evaluate_prediction(
        db,
        payload.mmsi,
        payload.pred_latitude_value,
        payload.pred_longitude_value,
        payload.anomaly_score,
    )


@router.get("/alerts", response_model=list[schemas.AlertOut])
def get_all_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Liste toutes les alertes récentes (pour consultation/frontend)."""
    return list_alerts(db, limit)


@router.get("/alerts/{mmsi}", response_model=list[schemas.AlertOut])
def get_alerts_by_mmsi(mmsi: int, limit: int = 20, db: Session = Depends(get_db)):
    """Liste les alertes pour un navire spécifique."""
    return list_alerts_by_mmsi(db, mmsi, limit)