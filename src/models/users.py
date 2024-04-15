from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import (
    DateTime,
)

from src.models import Base
from src.models.requests import RequestsDto


class Tokens(Base):
    __tablename__ = "tokens"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, server_default=func.now())
    created_by: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[int]

    creator = relationship('Users', back_populates="created_tokens", foreign_keys=[created_by], lazy='selectin')
    created_user = relationship('Users', back_populates="token", foreign_keys=[user_id], lazy='selectin')


class UserRoles(Base):
    __tablename__ = 'user_roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)


class Roles(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    users = relationship('Users', secondary='user_roles', back_populates='roles', lazy='selectin')


class Users(Base):
    __tablename__ = "users"

    # Определение атрибутов пользователя и их типов данных
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    roles = relationship('Roles', secondary='user_roles', back_populates='users', lazy='selectin')
    requests_appellant = relationship("RequestsDto", back_populates="appellant",
                                      foreign_keys=[RequestsDto.appellant_id])
    requests_confirming = relationship("RequestsDto", back_populates="confirming",
                                       foreign_keys=[RequestsDto.confirming_id])
    created_tokens = relationship("Tokens", back_populates="creator", foreign_keys=[Tokens.created_by], lazy='selectin')
    token = relationship('Tokens', back_populates="created_user", foreign_keys=[Tokens.user_id], lazy='selectin')
