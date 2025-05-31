from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.security import verify_password, create_access_token
from dependencies import get_current_user
from db.database import get_db
from db.models import User
from schemas.user import TokenData, UserResponse, Token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/")


@router.post("/auth/", response_model=Token, tags=["auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    print(f"[DEBUG] Login attempt: {form_data.username}")
    """Login endpoint"""
    user = db.query(User).filter(User.username == form_data.username).first()

    # Check if user exists and verify password
    if not user or not verify_password(form_data.password, user.password_hash):
        # Check failed login attempts and account lockout
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.account_locked = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account locked due to too many failed login attempts",
                )
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Check if account is locked
    if user.account_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked due to too many failed login attempts",
        )

    # Reset failed login attempts on successful login
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, tags=["auth"])
def read_current_user(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
