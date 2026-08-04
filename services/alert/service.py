from sqlalchemy import text
from sqlalchemy.orm import Session

import models

ANOMALY_THRESHOLD = 0.5


def find_nearest_zone(db: Session, lat: float, lon: float):
    result = db.execute(
        text("""
            SELECT name, center_lat, center_lon, radius_km,
                   earth_distance(
                       ll_to_earth(center_lat, center_lon),
                       ll_to_earth(:lat, :lon)
                   ) / 1000.0 AS distance_km
            FROM protected_zones
            ORDER BY distance_km ASC
            LIMIT 1
        """),
        {"lat": lat, "lon": lon}
    ).fetchone()

    return result

def evaluate_prediction(db: Session, mmsi: int, pred_lat: float, pred_lon: float, anomaly_score: float):
    """
    Évalue une prédiction : calcule la distance à la zone protégée la plus proche,
    détermine s'il y a intrusion et/ou dégazage, et sauvegarde une alerte si besoin.
    """
    nearest_zone = find_nearest_zone(db, pred_lat, pred_lon)

    is_intrusion = False
    distance_km = None
    zone_name = None

    if nearest_zone is not None:
        zone_name = nearest_zone.name
        distance_km = round(nearest_zone.distance_km, 3)
        is_intrusion = distance_km < nearest_zone.radius_km

    is_degassing = anomaly_score >= ANOMALY_THRESHOLD

  # Détermine alert_reason et alert_level
    if is_intrusion and is_degassing:
        alert_reason = "LES_DEUX"
        alert_level = "CRITICAL"  # Remplacé "HIGH" par "CRITICAL" (ou une autre valeur acceptée par votre base)
    elif is_intrusion:
        alert_reason = "INTRUSION"
        alert_level = "MEDIUM"
    elif is_degassing:
        alert_reason = "DEGAZAGE"
        alert_level = "MEDIUM"
    else:
        alert_reason = None
        alert_level = "LOW"

    alert_created = alert_reason is not None

    if alert_created:
        alert = models.Alerts(
            mmsi=mmsi,
            zone_name=zone_name,
            alert_level=alert_level,
            distance_km=distance_km,
            anomaly_score=anomaly_score,
            alert_reason=alert_reason
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

    return {
        "alert_created": alert_created,
        "alert_reason": alert_reason,
        "alert_level": alert_level,
        "distance_km": distance_km,
        "zone_name": zone_name
    }


def list_alerts(db: Session, limit: int = 50):
    return (
        db.query(models.Alerts)
        .order_by(models.Alerts.created_at.desc())
        .limit(limit)
        .all()
    )


def list_alerts_by_mmsi(db: Session, mmsi: int, limit: int = 20):
    return (
        db.query(models.Alerts)
        .filter(models.Alerts.mmsi == mmsi)
        .order_by(models.Alerts.created_at.desc())
        .limit(limit)
        .all()
    )