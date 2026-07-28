from passlib.context import CryptContext
import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db, user):
    hashed = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db, email):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db, user_id, user_update):
    db_user = get_user(db, user_id)
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db, user_id):
    db_user = get_user(db, user_id)
    db.delete(db_user)
    db.commit()

def list_users(db):
    return db.query(models.User).all()