from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class Requests(BaseModel):
    id: UUID
    full_name: str
    email_address: EmailStr
    appellant_id: UUID
    appellant: UserSerialize
    datetime: datetime
    status: int
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


class RequestsCreate(BaseModel):
    full_name: list[str]
    email: list[EmailStr]
    phone_number: list[PhoneNumber]
    is_foreign: list[bool]
    visit_purpose: str
    place_of_visit: str
    datetime_of_visit: datetime


class RequestsReview(BaseModel):
    request_id: UUID
    status: int


class RequestsDelete(BaseModel):
    request_id: UUID
