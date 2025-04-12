from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, validator
from app.models import DiscountTypeEnum # Import the enum from models

# Base schema for promocode properties
class PromocodeBase(BaseModel):
    code: str = Field(..., max_length=100)
    discount_type: DiscountTypeEnum
    discount_value: float = Field(..., gt=0) # Ensure discount value is positive
    expiration_date: Optional[datetime] = None
    usage_limit: int = Field(default=1, ge=0) # 0 for unlimited, otherwise positive
    is_active: bool = True

    class Config:
        orm_mode = True # Enable ORM mode for SQLAlchemy model conversion
        use_enum_values = True # Use enum values instead of enum members

# Schema for creating a promocode (inherits from Base)
# owner_id will be added separately in CRUD based on context
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

    class Config:
        use_enum_values = True

# Schema for representing a promocode in the database (includes DB-generated fields)
class PromocodeInDB(PromocodeBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Schema for returning a promocode in responses (can be same as InDB or customized)
class PromocodeResponse(PromocodeInDB):
    pass

# Schema for list response (useful if converting within the service)
class PromocodeListResponse(BaseModel):
    promocodes: list[PromocodeResponse]
    total_count: int
    page: int
    page_size: int
