import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# 📁 Charge le .env global situé à la racine du projet
# services/gateway/main.py -> .parent (gateway) -> .parent (services) -> .parent (racine)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="Maritime API Gateway",
    description="Point d'entrée unique et sécurisé pour les microservices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Secrets
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

if not INTERNAL_SECRET:
    raise RuntimeError(
        f"INTERNAL_SECRET n'est pas défini. Fichier .env recherché ici : {env_path} (existe: {env_path.exists()})"
    )

# 🌐 Registre des microservices
SERVICES = {
     "users": "http://localhost:8005", 
    "auth": "http://localhost:8004",
    "ingestion": "http://localhost:8001",
    "prediction": "http://localhost:8002",
    "alert": "http://localhost:8003"
}

@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    """
    Proxy inverse : injecte le secret interne, puis redirige vers le microservice.
    """
    if service_name not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le service '{service_name}' est inconnu."
        )

    target_url = f"{SERVICES[service_name]}/{path}"
#header {key= authorisation} lil service taa auth 
    # 🔐 Injection du secret interne (écrase toute valeur venant du client)
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
                content=await request.body()
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


@app.get("/", tags=["Health"])
def gateway_health():
    return {"gateway": "online", "status": "active"}