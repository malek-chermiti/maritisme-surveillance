import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

# services/auth/security/internal_auth.py
# security/ -> auth/ -> services/ -> racine
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

if not INTERNAL_SECRET:
    raise RuntimeError(
        f"INTERNAL_SECRET n'est pas défini. Fichier cherché : {env_path} (existe: {env_path.exists()})"
    )


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
