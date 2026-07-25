import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Maritime API Gateway",
    description="Point d'entrée unique et sécurisé pour les microservices",
    version="1.0.0"
)

# Configuration CORS pour le Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🌐 Registre des ports et microservices de ton architecture
SERVICES = {
    "auth": "http://localhost:8004",
    "ingestion": "http://localhost:8001",
    "prediction": "http://localhost:8002",
    "alert": "http://localhost:8003"
}

# Routes publiques qui ne nécessitent pas d'être authentifié
PUBLIC_ROUTES = ["/api/auth/login", "/api/auth/register"]

@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    """
    Proxy inverse : intercepte /api/{service_name}/{path} et redirige 
    vers le microservice correspondant en interne.
    """
    if service_name not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le service '{service_name}' est inconnu."
        )

    full_path = f"/api/{service_name}/{path}"

    # 🛡️ Étape de sécurité (Auth Guard) : 
    # Si la route n'est pas publique, on vérifie la présence du token d'autorisation
    if full_path not in PUBLIC_ROUTES:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification manquant."
            )
        # Optionnel : Tu pourrais ici valider le JWT auprès du service 'auth' avant de laisser passer

    target_url = f"{SERVICES[service_name]}/{path}"

    # Transfert de la requête vers le microservice cible
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
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