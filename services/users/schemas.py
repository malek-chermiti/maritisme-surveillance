from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str  # mdp en clair reçu, sera hashé avant stockage
    role: str = "user"

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = None

class UserOut(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True