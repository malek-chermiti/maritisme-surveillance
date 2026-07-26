import threading

from fastapi import Depends, FastAPI

from controller import router as vessel_router
from kafka_consumer import start_kafka_consumer
from security.internal_auth import verify_internal_secret

app = FastAPI(
    title="Ingestion Service",
    dependencies=[Depends(verify_internal_secret)]
)

app.include_router(vessel_router)


@app.on_event("startup")
def startup_event():
    print("Demarrage de l'ingestion-service...")
    thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    thread.start()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion-service"}
