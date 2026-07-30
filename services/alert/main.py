import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.consul.consul_registration import register_service

app = FastAPI(
    title="Alert Service"
)

register_service(app, service_name="alert-service", service_port=8003)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "alert-service"}
