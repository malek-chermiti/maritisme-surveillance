import os
import sys

from fastapi import FastAPI

if __package__:
    from controller import router as auth_router
else:
    sys.path.insert(0, os.path.dirname(__file__))
    from controller import router as auth_router

app = FastAPI(
    title="Auth Service",
    description="Service d'authentification et de gestion des tokens",
    version="1.0.0",
)

app.include_router(auth_router)


@app.get("/", tags=["Health"])
def health():
    return {"service": "auth", "status": "online"}
