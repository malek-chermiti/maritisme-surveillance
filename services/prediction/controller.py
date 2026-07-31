from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security.internal_auth import verify_internal_secret
from service import predict_and_process, list_predictions_by_mmsi
import schemas

router = APIRouter(dependencies=[Depends(verify_internal_secret)])


@router.post("/predict/{mmsi}", response_model=schemas.PredictionOut)
async def predict(mmsi: int, db: Session = Depends(get_db)):
    """
    Récupère l'historique du navire, prédit sa position future + score d'anomalie,
    sauvegarde le résultat, et notifie alert-service (sans attendre sa réponse).
    """
    return await predict_and_process(db, mmsi)


@router.get("/predictions/{mmsi}", response_model=list[schemas.PredictionLogOut])
def get_predictions_history(mmsi: int, limit: int = 10, db: Session = Depends(get_db)):
    """Retourne l'historique des prédictions déjà réalisées pour un navire."""
    predictions = list_predictions_by_mmsi(db, mmsi, limit)
    if not predictions:
        raise HTTPException(status_code=404, detail="Aucune prédiction trouvée pour ce navire")
    return predictions