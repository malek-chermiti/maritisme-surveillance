import logging
import threading
from fastapi import FastAPI

from database import engine, Base
from ingestion_controller import router as ingestion_router
from ingestion_service import run_kafka_consumer

logging.basicConfig(level=logging.INFO)

# Création des tables dans ingestion_db
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ingestion Service",
    description="Microservice gérant la réception Kafka, l'historique et la zone de simulation",
    version="1.0.0"
)

# Inclusion du controller
app.include_router(ingestion_router)

@app.on_event("startup")
def startup_event():
    # Démarrage du consumer Kafka en tâche de fond
    kafka_thread = threading.Thread(target=run_kafka_consumer, daemon=True)
    kafka_thread.start()

@app.get("/", tags=["Health"])
def health_check():
    return {"service": "ingestion-service", "status": "running"}