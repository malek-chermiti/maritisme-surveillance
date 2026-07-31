import os
import sys
from pathlib import Path

from fastapi import FastAPI

try:
    from .security.internal_auth import verify_internal_secret
    from .controller import router as users_router
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from security.internal_auth import verify_internal_secret
    from controller import router as users_router

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.consul.consul_registration import register_service

app = FastAPI(
    title="Users Service",
    description="Service de gestion des utilisateurs (CRUD)",
    version="1.0.0",
)

register_service(app, service_name="users-service", service_port=8005)

app.include_router(users_router)


@app.get("/health", tags=["Health"])
def health():
    return {"service": "users", "status": "online"}