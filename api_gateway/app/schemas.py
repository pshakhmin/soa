import enum
import uuid
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, date
import re

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(None, regex=r'^\+?[0-9]{10,15}$')
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int

class TokenData(BaseModel):
    username: str

class RefreshToken(BaseModel):
    refresh_token: str


# --- Promocode Schemas ---

# Enum for Discount Type (mirroring proto)
class DiscountTypeEnum(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

# Base schema for promocode properties used in requests
class PromocodeBase(BaseModel):
    code: str = Field(..., max_length=100)
    discount_type: DiscountTypeEnum
    discount_value: float = Field(..., gt=0)
    expiration_date: Optional[datetime] = None
    usage_limit: int = Field(default=1, ge=0) # 0 for unlimited

# Schema for creating a promocode
class PromocodeCreate(PromocodeBase):
    pass

# Schema for updating a promocode (all fields optional)
class PromocodeUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=100)
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[float] = Field(None, gt=0)
    expiration_date: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

# Schema for the promocode data returned in responses
class PromocodeResponseData(PromocodeBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True # Allow conversion from objects with attributes
        use_enum_values = True

# Schema for a single promocode response
class PromocodeResponse(BaseModel):
    promocode: PromocodeResponseData

# Schema for listing promocodes
class ListPromocodesResponse(BaseModel):
    promocodes: list[PromocodeResponseData]
    total_count: int
    page: int
    page_size: int
