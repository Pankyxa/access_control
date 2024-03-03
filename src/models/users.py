from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class Base(DeclarativeBase):
    ...


class UserRoles(Base):
    __tablename__ = 'user_roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)


class Roles(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    users = relationship('Users', secondary='user_roles', back_populates='roles')


class Users(Base):
    __tablename__ = "users"

    # Определение атрибутов пользователя и их типов данных
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    encrypted_password: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    roles = relationship('Roles', secondary='user_roles', back_populates='users')
