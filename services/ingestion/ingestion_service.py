import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import SessionLocal
from models import VesselPosition, SimulationZone
from schemas import VesselPositionSchema, SimulationZoneSchema

logger = logging.getLogger("ingestion-service")

class IngestionService:
    """
    Couche Métier (Service Layer) : Concentre absolument toute la logique métier,
    la validation complexe et l'accès aux données.
    """

    @staticmethod
    def save_vessel_position(db: Session, raw_data: dict) -> VesselPosition:
        """
        Valide et sauvegarde une position GPS.
        Applique les règles métier géographiques avant l'insertion en BDD.
        """
        # 1. Normalisation des données
        lat = raw_data.get("latitude") if raw_data.get("latitude") is not None else raw_data.get("lat")
        lon = raw_data.get("longitude") if raw_data.get("longitude") is not None else raw_data.get("lon")

        # 2. Règle Métier : Validation géographique absolue (les coordonnées terrestres ont des limites)
        if not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
            raise ValueError(f"Coordonnées GPS physiquement impossibles pour le MMSI {raw_data.get('mmsi')} : ({lat}, {lon})")

        # 3. Règle Métier : Validation des types de données via Pydantic
        validated_data = VesselPositionSchema(
            mmsi=raw_data["mmsi"],
            latitude=lat,
            longitude=lon,
            speed=raw_data.get("speed", 0.0),
            heading=raw_data.get("heading", 0.0),
            recorded_at=raw_data.get("recorded_at") or datetime.now(timezone.utc)
        )

        # 4. Persistance (ORM)
        position = VesselPosition(
            mmsi=validated_data.mmsi,
            latitude=validated_data.latitude,
            longitude=validated_data.longitude,
            speed=validated_data.speed,
            heading=validated_data.heading,
            recorded_at=validated_data.recorded_at
        )

        db.add(position)
        db.commit()
        db.refresh(position)
        return position

    @staticmethod
    def get_vessel_history(db: Session, mmsi: int, minutes: int = 30) -> List[VesselPosition]:
        """
        Récupère l'historique d'un navire.
        Vérifie la cohérence de la requête temporelle.
        """
        # Règle Métier : Le temps de recul doit être logique
        if minutes <= 0:
            raise ValueError("La durée de l'historique demandée doit être strictement positive.")

        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return (
            db.query(VesselPosition)
            .filter(VesselPosition.mmsi == mmsi)
            .filter(VesselPosition.recorded_at >= time_threshold)
            .order_by(desc(VesselPosition.recorded_at))
            .all()
        )

    @staticmethod
    def get_current_simulation_zone(db: Session) -> SimulationZone:
        """
        Fournit la zone active. Garantit qu'il y a toujours une zone par défaut
        pour éviter de faire crasher le simulateur.
        """
        zone = db.query(SimulationZone).order_by(desc(SimulationZone.id)).first()
        if not zone:
            logger.info("Aucune zone trouvée en DB. Initialisation de la zone de sécurité (Méditerranée/Tunisie).")
            zone = SimulationZone(lat_min=34.0, lat_max=38.0, lon_min=8.0, lon_max=12.0)
            db.add(zone)
            db.commit()
            db.refresh(zone)
        return zone

    @staticmethod
    def create_simulation_zone(db: Session, zone_data: SimulationZoneSchema) -> SimulationZone:
        """
        Enregistre une nouvelle zone de simulation après validation de sa géométrie.
        """
        # Règle Métier : Une Bounding Box doit avoir un minimum inférieur à son maximum
        if zone_data.lat_min >= zone_data.lat_max or zone_data.lon_min >= zone_data.lon_max:
            raise ValueError("Géométrie de zone invalide : les valeurs minimales (Sud/Ouest) doivent être inférieures aux valeurs maximales (Nord/Est).")

        new_zone = SimulationZone(
            name=zone_data.name or "Zone Personnalisée",
            lat_min=zone_data.lat_min,
            lat_max=zone_data.lat_max,
            lon_min=zone_data.lon_min,
            lon_max=zone_data.lon_max
        )
        db.add(new_zone)
        db.commit()
        db.refresh(new_zone)
        return new_zone


# ------------------------------------------------------------------------------
# Worker Process (Consommateur Kafka)
# Le worker devient complètement "aveugle", il se contente de passer la balle au Service.
# ------------------------------------------------------------------------------
def run_kafka_consumer():
    from kafka import KafkaConsumer
    logger.info("📡 Worker Kafka démarré sur le topic 'vessel-gps'...")

    try:
        consumer = KafkaConsumer(
            "vessel-gps",
            bootstrap_servers="localhost:9092",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="ingestion-group"
        )
        for message in consumer:
            db = SessionLocal()
            try:
                # Délégation totale à la couche métier
                saved_position = IngestionService.save_vessel_position(db, message.value)
                logger.info(f"✅ BDD Insérée -> MMSI: {saved_position.mmsi} | Lat: {saved_position.latitude}")
            except ValueError as ve:
                # La couche métier a rejeté la donnée (ex: GPS hors limites)
                logger.warning(f"⚠️ Donnée rejetée par les règles métier : {ve}")
            except Exception as e:
                # Erreur technique (ex: coupure base de données)
                db.rollback()
                logger.error(f"❌ Erreur technique d'insertion : {e}")
            finally:
                db.close()
    except Exception as e:
        logger.error(f"⚠️ Erreur critique de la connexion Kafka : {e}")