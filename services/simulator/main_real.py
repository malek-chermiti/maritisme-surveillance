
import asyncio
import json
import os

import websockets
from dotenv import load_dotenv

load_dotenv()

AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY")
AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"


async def test_connection():
    print("Cle API utilisee :", AISSTREAM_API_KEY)
    async with websockets.connect(AISSTREAM_URL) as ws:
        subscribe_message = {
            "Apikey": AISSTREAM_API_KEY,
            "BoundingBoxes": [[[-90, -180], [90, 180]]],
            "FilterMessageTypes": ["PositionReport"]
        }
        await ws.send(json.dumps(subscribe_message))
        print("Message envoye, en attente de reponse...")

        try:
            async for message_json in ws:
                print("Recu :", message_json[:200])
                break
        except Exception as e:
            print("Erreur pendant la reception :", e)


asyncio.run(test_connection())
