import json
import os

from kafka import KafkaConsumer
from dotenv import load_dotenv

from database import SessionLocal
from service import save_vessel_position

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "vessel-gps")


def start_kafka_consumer():
    '''Boucle infinie qui ecoute Kafka et sauvegarde chaque position recue.'''
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="ingestion-group"
    )

    print("Kafka consumer demarre. En attente de messages sur", KAFKA_TOPIC)

    for message in consumer:
        data = message.value
        db = SessionLocal()
        try:
            save_vessel_position(db, data)
            print("Insere en base :", data)
        except Exception as e:
            db.rollback()
            print("Erreur lors de l'insertion :", e)
        finally:
            db.close()
