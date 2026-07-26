from fastapi import Depends, FastAPI

from security.internal_auth import verify_internal_secret

app = FastAPI(
    title="Alert Service",
    dependencies=[Depends(verify_internal_secret)]
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "alert-service"}
