from __future__ import annotations

from datetime import datetime, date
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class RequestsDto(Base):
    __tablename__ = "requests"
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    full_name: Mapped[str]
    email_address: Mapped[str]
    visit_purpose: Mapped[str]
    datetime_of_visit: Mapped[date]
    appellant_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), default=uuid4)
    datetime: Mapped[datetime]
    status: Mapped[int]
    confirming_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id'), default=None)

    appellant = relationship("Users", back_populates="requests_appellant", foreign_keys=[appellant_id])
    confirming = relationship("Users", back_populates="requests_confirming", foreign_keys=[confirming_id])
