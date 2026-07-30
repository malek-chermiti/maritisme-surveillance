import httpx
from fastapi import FastAPI

CONSUL_URL = "http://localhost:8500"


def register_service(app: FastAPI, service_name: str, service_port: int):
    """
    Enregistre un service FastAPI auprès de Consul et initialise son cycle de vie.
    Le health check utilise host.docker.internal car Consul tourne dans un container
    Docker et doit pouvoir contacter les services lancés sur l'hôte Windows.
    """
    service_id = f"{service_name}-{service_port}"

    @app.on_event("startup")
    async def _register_with_consul():
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.put(
                    f"{CONSUL_URL}/v1/agent/service/register",
                    json={
                        "Name": service_name,
                        "ID": service_id,
                        "Port": service_port,
                        "Address": "localhost",
                        "Check": {
                            "HTTP": f"http://host.docker.internal:{service_port}/health",
                            "Interval": "10s",
                            "Timeout": "3s"
                        },
                    },
                )
                print(f"✅ {service_name} enregistré auprès de Consul")
            except httpx.RequestError as exc:
                print(f"⚠️ Impossible de contacter Consul, {service_name} non enregistré : {exc}")

    @app.on_event("shutdown")
    async def _deregister_from_consul():
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.put(f"{CONSUL_URL}/v1/agent/service/deregister/{service_id}")
            except httpx.RequestError:
                pass
