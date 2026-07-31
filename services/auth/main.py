import os
import sys
from pathlib import Path

from fastapi import FastAPI

if __package__:
    from controller import router as auth_router
else:
    sys.path.insert(0, os.path.dirname(__file__))
    from controller import router as auth_router

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.consul.consul_registration import register_service

app = FastAPI(
    title="Auth Service",
    description="Service d'authentification et de gestion des tokens",
    version="1.0.0",
)

register_service(app, service_name="auth-service", service_port=8004)

app.include_router(auth_router)


@app.get("/health", tags=["Health"])
def health():
    return {"service": "auth", "status": "online"}
