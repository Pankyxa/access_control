from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class RequestsDto(Base):
    __tablename__ = "requests"
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    visit_purpose: Mapped[str]
    place_of_visit: Mapped[str]
    datetime_of_visit: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    appellant_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), default=uuid4)
    datetime: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[int]
    confirming_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id'), default=None)
    comment: Mapped[str | None]

    appellant = relationship("Users", back_populates="requests_appellant", foreign_keys=[appellant_id],
                             lazy='selectin')
    confirming = relationship("Users", back_populates="requests_confirming", foreign_keys=[confirming_id],
                              lazy='selectin')

    guests = relationship('Guests', back_populates="request", lazy='selectin')


class Guests(Base):
    __tablename__ = "guests"
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    request_id: Mapped[UUID] = mapped_column(ForeignKey('requests.id'))
    full_name: Mapped[str]
    email: Mapped[str]
    phone_number: Mapped[str]
    is_foreign: Mapped[bool]
    visit_status: Mapped[int]

    request = relationship("RequestsDto", back_populates="guests", foreign_keys=[request_id])
