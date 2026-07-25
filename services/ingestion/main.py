import threading

from fastapi import FastAPI

from controller import router as vessel_router
from kafka_consumer import start_kafka_consumer

app = FastAPI(title="Ingestion Service")

app.include_router(vessel_router)


@app.on_event("startup")
def startup_event():
    print("Demarrage de l'ingestion-service...")
    thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    thread.start()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion-service"}
