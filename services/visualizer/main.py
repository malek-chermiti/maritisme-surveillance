import asyncio
import json
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from kafka import KafkaConsumer

app = FastAPI()

connected_clients = []
main_loop = None


def kafka_listener():
    consumer = KafkaConsumer(
        "vessel-gps",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest"
    )
    for message in consumer:
        data = message.value
        if main_loop:
            asyncio.run_coroutine_threadsafe(broadcast(data), main_loop)


async def broadcast(data):
    for client in connected_clients[:]:
        try:
            await client.send_json(data)
        except Exception:
            connected_clients.remove(client)


@app.on_event("startup")
async def startup():
    global main_loop
    main_loop = asyncio.get_event_loop()
    thread = threading.Thread(target=kafka_listener, daemon=True)
    thread.start()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


@app.get("/")
async def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vessel Tracker - Live</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body { margin: 0; }
            #map { height: 100vh; width: 100vw; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            const map = L.map('map').setView([35.0, 10.0], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

            const markers = {};

            const ws = new WebSocket("ws://" + window.location.host + "/ws");
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const mmsi = data.mmsi;
                const lat = data.lat;
                const lon = data.lon;

                if (markers[mmsi]) {
                    markers[mmsi].setLatLng([lat, lon]);
                } else {
                    const marker = L.marker([lat, lon]).addTo(map);
                    marker.bindTooltip("MMSI: " + mmsi, {permanent: false});
                    markers[mmsi] = marker;
                }
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
