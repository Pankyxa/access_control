from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr


class Requests(BaseModel):
    id: UUID
    full_name: str
    email_address: EmailStr
    appellant_id: UUID
    datetime: datetime
    status: int
    confirming_id: Optional[UUID]


class RequestsCreate(BaseModel):
    full_name: str
    email_address: EmailStr
    visit_purpose: str
    place_of_visit: str
    datetime_of_visit: datetime


class RequestsReview(BaseModel):
    request_id: UUID
    status: int
