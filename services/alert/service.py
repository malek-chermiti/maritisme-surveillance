import os

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

import models

ANOMALY_THRESHOLD = 0.5
INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8001")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")


def get_active_simulation_zone():
    try:
        headers = {"X-Internal-Secret": INTERNAL_SECRET} if INTERNAL_SECRET else {}
        response = httpx.get(
            f"{INGESTION_SERVICE_URL}/vessels/zone",
            timeout=5.0,
            headers=headers,
        )
    except httpx.RequestError:
        return None

    if response.status_code != 200:
        return None

    zone = response.json()
    if not zone:
        return None

    return {
        "lat_min": float(zone.get("lat_min")),
        "lat_max": float(zone.get("lat_max")),
        "lon_min": float(zone.get("lon_min")),
        "lon_max": float(zone.get("lon_max")),
    }


def is_point_in_zone_bounds(lat: float, lon: float, zone: dict | None):
    if zone is None:
        return False

    lat_min = float(zone.get("lat_min"))
    lat_max = float(zone.get("lat_max"))
    lon_min = float(zone.get("lon_min"))
    lon_max = float(zone.get("lon_max"))

    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


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
    Évalue une prédiction uniquement dans la zone de simulation active.
    Si aucune zone active n'est disponible, on conserve le comportement de secours
    basé sur la zone protégée la plus proche.
    """
    active_zone = get_active_simulation_zone()
    if active_zone is not None:
        inside_active_zone = is_point_in_zone_bounds(pred_lat, pred_lon, active_zone)
        if not inside_active_zone:
            return {
                "alert_created": False,
                "alert_reason": None,
                "alert_level": "LOW",
                "distance_km": None,
                "zone_name": None,
            }

        is_intrusion = True
        distance_km = 0.0
        zone_name = None
    else:
        nearest_zone = find_nearest_zone(db, pred_lat, pred_lon)

        is_intrusion = False
        distance_km = None
        zone_name = None

        if nearest_zone is not None:
            zone_name = nearest_zone.name
            distance_km = round(nearest_zone.distance_km, 3)
            is_intrusion = distance_km < nearest_zone.radius_km

    is_degassing = anomaly_score >= ANOMALY_THRESHOLD

    if is_intrusion and is_degassing:
        alert_reason = "LES_DEUX"
        alert_level = "CRITICAL"
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


def list_alerts_by_zone(db: Session, lat: float, lon: float, limit: int = 50):
    active_zone = get_active_simulation_zone()
    if active_zone is not None:
        return (
            db.query(models.Alerts)
            .order_by(models.Alerts.created_at.desc())
            .limit(limit)
            .all()
        )

    nearest_zone = find_nearest_zone(db, lat, lon)
    if nearest_zone is None:
        return []

    return (
        db.query(models.Alerts)
        .filter(models.Alerts.zone_name == nearest_zone.name)
        .order_by(models.Alerts.created_at.desc())
        .limit(limit)
        .all()
    )