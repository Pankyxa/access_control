from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class StatusEnum(IntEnum):
    Ожидает = 1
    Одобрена = 2
    Отклонена = 3
    Удалена = 4


class Requests(BaseModel):
    id: UUID
    visit_purpose: str
    place_of_visit: str
    datetime_of_visit: datetime
    guests: list[GuestSerialize]
    appellant_id: UUID
    appellant: UserSerialize
    datetime: datetime
    status: StatusEnum
    confirming_id: Optional[UUID]
    confirming: Optional[UserSerialize]

    class Config:
        orm_mode = True
        from_attributes = True


class RoleSerialize(BaseModel):
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class UserSerialize(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    roles: List[RoleSerialize]

    class Config:
        orm_mode = True
        from_attributes = True


class GuestSerialize(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone_number: PhoneNumber
    is_foreign: bool
    visit_status: int

    class Config:
        orm_mode = True
        from_attributes = True


class RequestsCreate(BaseModel):
    guests: list[GuestsCreate]
    visit_purpose: str
    place_of_visit: str
    datetime_of_visit: datetime


class GuestsCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: PhoneNumber
    is_foreign: bool

    class Config:
        orm_mode = True
        from_attributes = True


class RequestsReview(BaseModel):
    request_id: UUID
    status: StatusEnum
    comment: Optional[str]


class RequestsDelete(BaseModel):
    request_id: UUID
