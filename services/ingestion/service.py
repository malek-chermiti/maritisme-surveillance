from models import VesselPositions
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session



def save_vessel_position(db, data: dict):
    '''Enregistre une position de navire recue (Kafka ou HTTP) en base.'''
    position = VesselPositions(
        mmsi=data.get("mmsi"),
        latitude=data.get("lat"),
        longitude=data.get("lon"),
        speed=data.get("speed"),
        heading=data.get("heading")
    )
    db.add(position)
    db.commit()
    return position


def get_vessel_history(db, mmsi: int, limit: int = 20):
    '''Recupere les dernieres positions connues d'un navire, du plus recent au plus ancien.'''
    return (
        db.query(VesselPositions)
        .filter(VesselPositions.mmsi == mmsi)
        .order_by(VesselPositions.recorded_at.desc())
        .limit(limit)
        .all()
    )


def update_simulation_zone(db: Session, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    if lat_min >= lat_max:
        raise HTTPException(status_code=400, detail="lat_min doit être inférieur à lat_max")
    if lon_min >= lon_max:
        raise HTTPException(status_code=400, detail="lon_min doit être inférieur à lon_max")

    db.execute(
        text("""
            UPDATE simulation_zone
            SET lat_min = :lat_min, lat_max = :lat_max,
                lon_min = :lon_min, lon_max = :lon_max,
                updated_at = now()
        """),
        {"lat_min": lat_min, "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max}
    )
    db.commit()

    return {"lat_min": lat_min, "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max}


def get_simulation_zone(db: Session):
    result = db.execute(
        text("SELECT lat_min, lat_max, lon_min, lon_max FROM simulation_zone LIMIT 1")
    ).fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Aucune zone de simulation définie")

    return {"lat_min": result[0], "lat_max": result[1], "lon_min": result[2], "lon_max": result[3]}