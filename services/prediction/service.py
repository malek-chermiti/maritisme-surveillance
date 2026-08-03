import os
import pickle
from pathlib import Path

import httpx
import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session

import models

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")
INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8001")
ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8003")

MODEL_PATH = Path(__file__).resolve().parent / "training" / "model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def build_features(history: list[dict]) -> np.ndarray:
    """
    history attendu trié du plus récent au plus ancien.
    history[0] = t, history[1] = t-5, history[2] = t-10
    """
    if len(history) < 3:
        raise HTTPException(status_code=422, detail="Historique insuffisant (3 points minimum requis)")

    p_t, p_t5, p_t10 = history[0], history[1], history[2]

    features = [
        p_t["lat"], p_t["lon"], p_t["speed"] or 0, p_t["heading"] or 0,
        p_t5["lat"], p_t5["lon"], p_t5["speed"] or 0, p_t5["heading"] or 0,
        p_t10["lat"], p_t10["lon"], p_t10["speed"] or 0, p_t10["heading"] or 0,
    ]
    return np.array(features).reshape(1, -1)


async def fetch_history(mmsi: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{INGESTION_SERVICE_URL}/vessels/{mmsi}/history",
                params={"limit": 3},
                headers={"X-Internal-Secret": INTERNAL_SECRET}
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="ingestion-service injoignable")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Historique introuvable pour ce navire")

    history = response.json()
    if not history:
        raise HTTPException(status_code=404, detail="Aucune position enregistrée pour ce navire")

    return history


def save_prediction(db: Session, mmsi: int, pred_lat: float, pred_lon: float, anomaly_score: float):
    log = models.PredictionsLog(  # 👈 Correction ici (PredictionsLog au lieu de PredictionLog)
        mmsi=mmsi,
        pred_latitude=pred_lat,
        pred_longitude=pred_lon,
        anomaly_score=anomaly_score
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


async def notify_alert_service(mmsi: int, pred_lat: float, pred_lon: float, anomaly_score: float):
    """
    Envoie le résultat de prédiction à alert-service (fire and forget).
    prediction-service n'attend pas et n'utilise pas la réponse d'alert-service :
    c'est alert-service qui décide seul de créer ou non une alerte.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                f"{ALERT_SERVICE_URL}/alerts/evaluate",
                json={
                    "mmsi": mmsi,
                    "pred_latitude": pred_lat,
                    "pred_longitude": pred_lon,
                    "anomaly_score": anomaly_score
                },
                headers={"X-Internal-Secret": INTERNAL_SECRET}
            )
        except httpx.RequestError:
            # alert-service injoignable : on ignore, ça ne doit pas faire échouer la prédiction
            pass


def list_predictions_by_mmsi(db: Session, mmsi: int, limit: int = 10):
    return (
        db.query(models.PredictionsLog)  # 👈 Correction ici aussi pour l'historique
        .filter(models.PredictionsLog.mmsi == mmsi)
        .order_by(models.PredictionsLog.created_at.desc())
        .limit(limit)
        .all()
    )


async def predict_and_process(db: Session, mmsi: int):
    """
    Pipeline complet :
    1. Récupère l'historique du navire
    2. Prédit (lat_t30, lon_t30, anomaly_score)
    3. Sauvegarde le résultat dans prediction_log
    4. Notifie alert-service (sans attendre ni utiliser sa réponse)
    5. Retourne uniquement le résultat de la prédiction
    """
    history = await fetch_history(mmsi)
    features = build_features(history)
    prediction = model.predict(features)[0]

    predicted_lat_t30 = round(float(prediction[0]), 6)
    predicted_lon_t30 = round(float(prediction[1]), 6)
    anomaly_score = round(float(prediction[2]), 3)

    save_prediction(db, mmsi, predicted_lat_t30, predicted_lon_t30, anomaly_score)
    await notify_alert_service(mmsi, predicted_lat_t30, predicted_lat_t30, anomaly_score)

    return {
        "mmsi": mmsi,
        "predicted_lat_t30": predicted_lat_t30,
        "predicted_lon_t30": predicted_lon_t30,
        "anomaly_score": anomaly_score
    }