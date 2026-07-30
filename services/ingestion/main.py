import os
import sys
import threading
from pathlib import Path

from fastapi import Depends, FastAPI

from controller import router as vessel_router
from kafka_consumer import start_kafka_consumer
from security.internal_auth import verify_internal_secret

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.consul.consul_registration import register_service

app = FastAPI(
    title="Ingestion Service"
)

register_service(app, service_name="ingestion-service", service_port=8001)

app.include_router(vessel_router, dependencies=[Depends(verify_internal_secret)])


@app.on_event("startup")
def startup_event():
    print("Demarrage de l'ingestion-service...")
    thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    thread.start()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion-service"}
