import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.consul.consul_registration import register_service

# 📁 Charge le .env global situé à la racine du projet
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="Maritime API Gateway",
    description="Point d'entrée unique et sécurisé pour les microservices",
    version="1.0.0"
)

register_service(app, service_name="gateway-service", service_port=8000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

if not INTERNAL_SECRET:
    raise RuntimeError(
        f"INTERNAL_SECRET n'est pas défini. Fichier .env recherché ici : {env_path} (existe: {env_path.exists()})"
    )

SERVICES = {
    "users": "http://localhost:8005",
    "auth": "http://localhost:8004",
    "ingestion": "http://localhost:8001",
    "prediction": "http://localhost:8002",
    "alert": "http://localhost:8003"
}

AUTH_SERVICE_URL = SERVICES["auth"]

# 🔓 Routes qui ne nécessitent PAS de JWT
PUBLIC_ROUTES = [
    "/api/auth/login",
    "/api/users/users",   # POST /users -> création de compte
]


@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    """
    Proxy inverse :
    - Bloque l'accès public aux routes internes (/internal/...)
    - Valide le JWT via auth-service (token attendu dans le body : {"token": "..."})
    - Injecte le secret interne
    - Redirige vers le microservice cible
    """
    if service_name not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le service '{service_name}' est inconnu."
        )

    full_path = f"/api/{service_name}/{path}"

    # 🚫 Bloque l'accès public aux routes internes
    if path.startswith("internal/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à cette route interne."
        )

    # Lit le body brut une seule fois (on le réutilisera pour le transfert)
    raw_body = await request.body()

    # 🛡️ Vérification JWT via auth-service (sauf routes publiques)
    if full_path not in PUBLIC_ROUTES:
        authorization_header = request.headers.get("authorization")
        if not authorization_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Header Authorization manquant."
            )

        if not authorization_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Format Authorization invalide. Utilisez 'Bearer <token>'."
            )

        token = authorization_header.removeprefix("Bearer ").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token manquant dans le header Authorization."
            )

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                validate_response = await client.post(
                    f"{AUTH_SERVICE_URL}/validate",
                    json={"token": token}
                )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Le service d'authentification est actuellement injoignable."
                )

        if validate_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré."
            )

    target_url = f"{SERVICES[service_name]}/{path}"

    # 🔐 Injection du secret interne
    forwarded_headers = dict(request.headers)
    forwarded_headers.pop("host", None)
    forwarded_headers.pop("content-length", None)
    forwarded_headers["X-Internal-Secret"] = INTERNAL_SECRET

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=forwarded_headers,
                params=request.query_params,
                content=raw_body   # 👈 réutilise le body déjà lu, pas de re-lecture
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Le service '{service_name}' est actuellement injoignable."
            )


@app.get("/health", tags=["Health"])
def gateway_health():
    return {"gateway": "online", "status": "active"}