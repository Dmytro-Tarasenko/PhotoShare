import uuid
from datetime import datetime, date
from typing import Optional, Any, List, TypeAlias, Literal

from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from comment.orm import CommentORM
from database import Base, get_db
from photo.orm import PhotoORM

# Role typealias contains list of possible roles
Role: TypeAlias = Literal["user", "moderator", "admin"]


class UserORM(Base):
    """
    ORM mapping for UserAuth
    """
    __tablename__ = "users"

    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    loggedin: Mapped[bool] = mapped_column(default=False)
    # Relations
    profile: Mapped["ProfileORM"] = relationship(back_populates="user")


class ProfileORM(Base):
    """
    ORM mapping for ProfileData
    """
    __tablename__ = "profiles"
    # Table columns
    id: Mapped[uuid.UUID] = mapped_column(types.UUID, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(types.String(20))
    last_name: Mapped[Optional[str]] = mapped_column(types.String(20))
    email: Mapped[Optional[str]] = mapped_column(types.String(80), unique=True)
    is_banned: Mapped[bool] = mapped_column(default=False)
    email_verified: Mapped[bool] = mapped_column(default=False)
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())
    role: Mapped[Role] = mapped_column(types.String(20), default="user")
    birthday: Mapped[Optional[date]] = mapped_column(types.Date())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Realtions
    user: Mapped[UserORM] = relationship(back_populates="profile")
    photos: Mapped[List["PhotoORM"]] = relationship(back_populates="author")
    comments: Mapped[List["CommentORM"]] = relationship(back_populates="author")


class BlackListORM(Base):
    __tablename__ = "blacklist"
    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    token: Mapped[str] = mapped_column(unique=True)
    expire_access: Mapped[datetime] = mapped_column(types.DateTime(timezone=True))
    expire_refresh: Mapped[datetime] = mapped_column(types.DateTime(timezone=True))
