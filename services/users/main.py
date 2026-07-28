import os
import sys

from fastapi import FastAPI

try:
    from .security.internal_auth import verify_internal_secret
    from .controller import router as users_router
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from security.internal_auth import verify_internal_secret
    from controller import router as users_router

app = FastAPI(
    title="Users Service",
    description="Service de gestion des utilisateurs (CRUD)",
    version="1.0.0",
)

app.include_router(users_router)


@app.get("/", tags=["Health"])
def health():
    return {"service": "users", "status": "online"}