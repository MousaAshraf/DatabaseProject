from pydantic import BaseModel, field_validator, EmailStr
import re
from typing import Optional
from datetime import datetime

EGYPT_PHONE_REGEX = r"^\+20(10|11|12|15)[0-9]{8}$"


class UserCreate(BaseModel):
    firstname: str
    lastname: str
    username: str
    email: EmailStr
    password: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(EGYPT_PHONE_REGEX, v):
            raise ValueError("Enter a phone number in this format: '+201xxxxxxxxx'")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "firstname": "John",
                "lastname": "Doe",
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepassword123",
                "phone": "+2010123456789",
            }
        }
    }


class UserResponse(BaseModel):
    id: str
    firstname: str
    lastname: str
    username: str
    email: str
    phone: str
    is_admin: bool = False
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
