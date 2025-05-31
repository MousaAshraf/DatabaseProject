from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from core.security import verify_password_hash, create_access_token
from schemas.user import TokenData, UserResponse, Token
from dependencies import get_current_user

# jwt
import jwt
from jose import JWTError
from core.config import get_settings

settings = get_settings()


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/")


@router.post("/auth/", response_model=Token, tags=["auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password_hash",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password_hash(form_data.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.account_locked = True
        db.commit()

        if user.account_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password_hash",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, tags=["auth"])
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", tags=["auth"])
def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=403, detail="Not a refresh token")

        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token payload")

        # Return a new access token
        new_access_token = create_access_token(data={"sub": username})
        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
