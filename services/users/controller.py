import os
import sys

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from .database import get_db
    from .security.internal_auth import verify_internal_secret
    from . import models, schemas, service
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from database import get_db
    from security.internal_auth import verify_internal_secret
    import models, schemas, service

router = APIRouter()


# --- CRUD classique ---
@router.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    return service.create_user(db, user)#internel secret

@router.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    user = service.get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User introuvable")
    return user

@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    return service.update_user(db, user_id, user)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    service.delete_user(db, user_id)
    return {"message": "Utilisateur supprimé"}

@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    return service.list_users(db)


# --- Endpoint interne, appelé UNIQUEMENT par auth-service ---
@router.get("/internal/users/credentials")
def get_credentials(email: str, db: Session = Depends(get_db), _: None = Depends(verify_internal_secret)):
    user = service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password_hash": user.password_hash,
        "role": user.role
    }