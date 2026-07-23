import asyncio
import json
import os

import websockets
from kafka import KafkaProducer
from dotenv import load_dotenv
from sqlalchemy import text

from database import engine

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "vessel-gps")
AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY")
AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"


def get_active_zone():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT lat_min, lat_max, lon_min, lon_max FROM simulation_zone LIMIT 1")
        )
        row = result.fetchone()
        if row is None:
            return {"lat_min": 32.0, "lat_max": 38.0, "lon_min": 7.5, "lon_max": 12.0}
        return {"lat_min": row[0], "lat_max": row[1], "lon_min": row[2], "lon_max": row[3]}


async def stream_real_ships():
    zone = get_active_zone()
    print("Zone active :", zone)

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    bounding_box = [[
        [zone["lat_min"], zone["lon_min"]],
        [zone["lat_max"], zone["lon_max"]]
    ]]

    async with websockets.connect(AISSTREAM_URL) as ws:
        subscribe_message = {
            "Apikey": AISSTREAM_API_KEY,
            "BoundingBoxes": bounding_box,
            "FilterMessageTypes": ["PositionReport"]
        }
        await ws.send(json.dumps(subscribe_message))
        print("Abonne au flux AISStream (DONNEES REELLES). En attente...")

        async for message_json in ws:
            message = json.loads(message_json)

            if message.get("MessageType") == "PositionReport":
                report = message["Message"]["PositionReport"]

                vessel_data = {
                    "mmsi": report.get("UserID"),
                    "lat": report.get("Latitude"),
                    "lon": report.get("Longitude"),
                    "speed": report.get("Sog"),
                    "heading": report.get("Cog")
                }

                producer.send(KAFKA_TOPIC, value=vessel_data)
                print("Navire reel recu :", vessel_data)


if __name__ == "__main__":
    try:
        asyncio.run(stream_real_ships())
    except KeyboardInterrupt:
        print("Arret du relais AISStream.")
