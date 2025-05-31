from sqlalchemy.orm import Session
from db.models import User
from core.security import get_password_hash
from schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        firstname=user.firstname,
        lastname=user.lastname,
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        is_admin=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: str, user_update: UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    if user_update.firstname:
        db_user.firstname = user_update.firstname
    if user_update.lastname:
        db_user.lastname = user_update.lastname
    if user_update.email:
        db_user.email = user_update.email
    if user_update.phone:
        db_user.phone = user_update.phone
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: str):
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    db.delete(db_user)
    db.commit()
    return db_user
