import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass

# User object
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    # Unique api key for each user, used for authentication
    api_key: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))


    
    # lemon_squeezy_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)

    superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    # 1-to-1 relationship with Subscription
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 1-to-Many relationship with WidgetConfig
    widget_configs: Mapped[List["WidgetConfig"]] = relationship(
        "WidgetConfig",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    
    # Changed from Python 'int' to SQLAlchemy 'Integer'
    tier_id: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="subscription")

class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    # Weather & Location Data
    #location_name: Mapped[str] = mapped_column(String)
    #lat: Mapped[float] = mapped_column(Float)
    #lon: Mapped[float] = mapped_column(Float)
    #base_elevation: Mapped[int] = mapped_column(Integer) 
    #peak_elevation: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    #extra_elevation: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship back to the parent user
    user: Mapped["User"] = relationship("User", back_populates="widget_configs")

class Domains(Base):
    __tablename__ = "allowed_doamins"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    domain_name: Mapped[String] = mapped_column(String, nullable=False)