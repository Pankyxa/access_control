from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr


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
    full_name: str
    email_address: EmailStr
    visit_purpose: str
    place_of_visit: str
    datetime_of_visit: datetime


class RequestsReview(BaseModel):
    request_id: UUID
    status: int


class RequestsDelete(BaseModel):
    request_id: UUID
