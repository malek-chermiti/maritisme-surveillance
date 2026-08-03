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

# Intervalle entre chaque publication d'UN SEUL navire
PUBLISH_INTERVAL_SECONDS = 10

# Relit la zone active depuis la DB toutes les N publications
ZONE_REFRESH_EVERY_N_TICKS = 6  # ~1min si PUBLISH_INTERVAL_SECONDS = 10

DEGASSING_MMSI = 672123456

VESSELS = [
    {"mmsi": DEGASSING_MMSI, "lat": None, "lon": None, "heading": random.uniform(0, 360), "simulate_degassing": True},
    {"mmsi": 672123457, "lat": None, "lon": None, "heading": random.uniform(0, 360), "simulate_degassing": False},
    {"mmsi": 672123458, "lat": None, "lon": None, "heading": random.uniform(0, 360), "simulate_degassing": False},
    {"mmsi": 672123459, "lat": None, "lon": None, "heading": random.uniform(0, 360), "simulate_degassing": False},
    {"mmsi": 672123460, "lat": None, "lon": None, "heading": random.uniform(0, 360), "simulate_degassing": False},
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
    simulate_degassing = vessel.get("simulate_degassing", False)

    if simulate_degassing:
        vessel["heading"] += random.uniform(-40, 40)
        vessel["heading"] %= 360
        speed = round(random.uniform(0.5, 4), 2)
        step = 0.001
    else:
        vessel["heading"] += random.uniform(-15, 15)
        vessel["heading"] %= 360
        speed = round(random.uniform(5, 20), 2)
        step = 0.01

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

    print(f"Simulateur connecte a Kafka. Un seul navire envoye toutes les {PUBLISH_INTERVAL_SECONDS}s...")

    index = 0
    zone_refresh_counter = 0

    try:
        while True:
            # 🔄 Relit périodiquement la zone active depuis la DB
            if zone_refresh_counter >= ZONE_REFRESH_EVERY_N_TICKS:
                new_zone = get_active_zone()
                if new_zone != zone:
                    print("⚠️ Zone mise a jour par l'operateur :", new_zone)
                    zone = new_zone
                zone_refresh_counter = 0

            vessel = VESSELS[index % len(VESSELS)]
            speed = move_vessel(vessel, zone)

            message = {
                "mmsi": vessel["mmsi"],
                "lat": round(vessel["lat"], 6),
                "lon": round(vessel["lon"], 6),
                "speed": speed,
                "heading": round(vessel["heading"], 2)
            }
            producer.send(KAFKA_TOPIC, value=message)
            producer.flush()
            print("Envoye (MOCK) :", message)

            index += 1
            zone_refresh_counter += 1
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Arret du simulateur.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()