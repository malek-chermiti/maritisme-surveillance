import os
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header
from passlib.context import CryptContext
from pydantic import BaseModel
from security import create_access_token, create_refresh_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8005")


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(payload: LoginRequest):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USERS_SERVICE_URL}/internal/users/credentials",
            params={"email": payload.email},
            headers={"X-Internal-Secret": INTERNAL_SECRET}
        )

    if response.status_code != 200:
        raise HTTPException(401, "Email ou mot de passe incorrect")

    user = response.json()

    if not pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")

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
def validate(authorization: str = Header(...)):
    """Valide un access_token et retourne l'objet user (décodé du JWT)."""
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(401, "Token invalide ou expiré")

    return {"user_id": int(payload["sub"])}
#il injecte le id de user dans chaque req necessite un id_user pour user de 
# id x ne permet update le profile d'update user de id y


@router.post("/refresh")
def refresh(payload: RefreshRequest):
    """Génère un nouveau access_token à partir d'un refresh_token valide."""
    decoded = decode_token(payload.refresh_token)

    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(401, "Refresh token invalide ou expiré")

    user_id = int(decoded["sub"])
    new_access_token = create_access_token(user_id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }