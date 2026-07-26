import os
import secrets
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

if not INTERNAL_SECRET:
    raise RuntimeError("INTERNAL_SECRET n'est pas défini dans l'environnement")


async def verify_internal_secret(
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret")
) -> None:
    """
    Vérifie que la requête provient bien de la gateway,
    en comparant le header X-Internal-Secret au secret partagé.
    """
    if x_internal_secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-Internal-Secret manquant",
        )

    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Secret interne invalide",
        )
