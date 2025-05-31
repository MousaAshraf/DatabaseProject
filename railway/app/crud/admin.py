from sqlalchemy.orm import Session
from core.security import get_password_hash
from db.models import User


def create_admin_user(db: Session, email: str, password: str):
    """Internal function to create admin users"""
    hashed_password = get_password_hash(password)
    admin = User(
        Name="Admin",
        Email=email,
        password=hashed_password,
        phone="+201234567890",  # Default phone
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    return admin


def promote_to_admin(db: Session, user_id: int):
    """Promote existing user to admin"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.is_admin = True
    db.commit()
    return user


def get_all_users(db: Session):
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    db.delete(user)
    db.commit()
    return user


def update_user_role(db: Session, user_id: int, new_role: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.Role = new_role
    db.commit()
    return user


def update_user_info(
    db: Session,
    user_id: int,
    name: str = None,
    email: str = None,
    phone: str = None,
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    if name:
        user.username = name
    if email:
        user.email = email
    if phone:
        user.phone = phone

    db.commit()
    return user
