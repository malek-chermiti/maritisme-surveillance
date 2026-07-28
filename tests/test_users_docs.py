from fastapi.testclient import TestClient

from services.users.main import app


client = TestClient(app)


def test_docs_endpoints_are_available_without_internal_auth():
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
