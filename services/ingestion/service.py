from models import VesselPositions


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
