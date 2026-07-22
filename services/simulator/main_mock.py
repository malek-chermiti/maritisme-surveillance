
import json
import random
import time
import os
import math

from kafka import KafkaProducer
from dotenv import load_dotenv
from sqlalchemy import text

from database import engine

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "vessel-gps")

VESSELS = [
    {"mmsi": 672123456, "lat": None, "lon": None, "heading": random.uniform(0, 360)},
    {"mmsi": 672123457, "lat": None, "lon": None, "heading": random.uniform(0, 360)},
    {"mmsi": 672123458, "lat": None, "lon": None, "heading": random.uniform(0, 360)},
    {"mmsi": 672123459, "lat": None, "lon": None, "heading": random.uniform(0, 360)},
    {"mmsi": 672123460, "lat": None, "lon": None, "heading": random.uniform(0, 360)},
]


def get_active_zone():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT lat_min, lat_max, lon_min, lon_max FROM simulation_zone LIMIT 1")
        )
        row = result.fetchone()
        if row is None:
            return {"lat_min": 32.0, "lat_max": 38.0, "lon_min": 7.5, "lon_max": 12.0}
        return {"lat_min": row[0], "lat_max": row[1], "lon_min": row[2], "lon_max": row[3]}


def init_vessel_positions(zone):
    for vessel in VESSELS:
        vessel["lat"] = random.uniform(zone["lat_min"], zone["lat_max"])
        vessel["lon"] = random.uniform(zone["lon_min"], zone["lon_max"])


def move_vessel(vessel, zone):
    step = 0.01
    vessel["heading"] += random.uniform(-15, 15)
    vessel["heading"] %= 360

    rad = math.radians(vessel["heading"])
    new_lat = vessel["lat"] + step * math.cos(rad)
    new_lon = vessel["lon"] + step * math.sin(rad)

    if not (zone["lat_min"] <= new_lat <= zone["lat_max"]):
        vessel["heading"] = (vessel["heading"] + 180) % 360
    else:
        vessel["lat"] = new_lat

    if not (zone["lon_min"] <= new_lon <= zone["lon_max"]):
        vessel["heading"] = (vessel["heading"] + 180) % 360
    else:
        vessel["lon"] = new_lon

    speed = round(random.uniform(5, 20), 2)
    return speed


def main():
    print("Demarrage du simulateur MOCK...")
    zone = get_active_zone()
    print("Zone active :", zone)

    init_vessel_positions(zone)

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    print("Simulateur connecte a Kafka. Envoi des positions toutes les 5 secondes...")

    try:
        while True:
            for vessel in VESSELS:
                speed = move_vessel(vessel, zone)
                message = {
                    "mmsi": vessel["mmsi"],
                    "lat": round(vessel["lat"], 6),
                    "lon": round(vessel["lon"], 6),
                    "speed": speed,
                    "heading": round(vessel["heading"], 2)
                }
                producer.send(KAFKA_TOPIC, value=message)
                print("Envoye (MOCK) :", message)
            producer.flush()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Arret du simulateur.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
