import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from security.token import (
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# services/auth/controller.py -> .parent (auth) -> .parent (services) -> .parent (racine)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8005")

if not INTERNAL_SECRET:
    raise RuntimeError(
        f"INTERNAL_SECRET n'est pas défini. Fichier cherché : {env_path} (existe: {env_path.exists()})"
    )


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ValidateRequest(BaseModel):
    token: str


@router.post("/login")
async def login(payload: LoginRequest):
    """Vérifie les credentials via users-service, puis génère les tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USERS_SERVICE_URL}/internal/users/credentials",
            params={"email": payload.email},
            headers={"X-Internal-Secret": INTERNAL_SECRET}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    user = response.json()

    if not pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user["id"]
    }


@router.post("/validate")
def validate(payload: ValidateRequest):
    """Valide un access_token reçu dans le body et retourne l'user_id décodé."""
    decoded = decode_token(payload.token)

    if decoded is None or decoded.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    return {"user_id": int(decoded["sub"])}


@router.post("/refresh")
def refresh(payload: RefreshRequest):
    """Génère un nouveau access_token à partir d'un refresh_token valide."""
    decoded = decode_token(payload.refresh_token)

    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")

    user_id = int(decoded["sub"])
    new_access_token = create_access_token(user_id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }