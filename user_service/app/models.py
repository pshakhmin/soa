import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Primary Key"
    )
    email = Column(
        String(320), unique=True, nullable=False, comment="Unique email address"
    )
    password_hash = Column(Text, nullable=False, comment="Password hash")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Registration date with timezone",
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp"
    )

    is_active = Column(Boolean, default=True)
    role = Column(String(50), nullable=False, comment="Role: user|business|admin")
    phone = Column(String(15))

    meta = Column("metadata", JSONB, comment="Additional data")
    business_profile = relationship(
        "BusinessProfile", back_populates="user", uselist=False
    )


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    profile_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Primary Key"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        comment="Reference to users.id",
    )
    legal_name = Column(String(255), nullable=False, comment="Legal business name")
    tax_id = Column(String(20), comment="Tax identification number")
    address = Column(Text, comment="Legal address")
    contact_email = Column(String(255))
    contact_phone = Column(String(15))
    verified_at = Column(DateTime(timezone=True), comment="Verification date")

    user = relationship("User", back_populates="business_profile")

