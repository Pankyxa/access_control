from __future__ import annotations
from datetime import date
from uuid import UUID
from pydantic import BaseModel
from pydantic import EmailStr
  
  
class Guests(BaseModel):
    id: UUID | None
    fullname: str
    email_address: EmailStr
    responsible_person: str
    date_time: date | None = None
    approver: str
    status: bool


class GuestsCreate(BaseModel):
    id: UUID | None
    fullname: str
    email_address: EmailStr
    responsible_person: str
    date_time: date | None = None
    approver: str
    status: bool