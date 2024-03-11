from __future__ import annotations
from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    ...

class GuestsModel(Base):
    __tablename__ = "Guests" 
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True) 
    fullname: Mapped[str]
    email_address: Mapped[str]
    responsible_person_id: Mapped[int] = mapped_column(ForeignKey("Persons.res_id"))
    date_time: Mapped[date]
    approver: Mapped[str] = mapped_column(ForeignKey("Security.sec_id"))
    status: Mapped[bool]
    invited:Mapped["ResponsiblePersModel"] = relationship(back_populates="request") 
    approved:Mapped["SecurityModel"] = relationship(back_populates="request_approval")


class ResponsiblePersModel(Base):
    __tablename__ = "Persons" 
    res_id: Mapped[int] = mapped_column(primary_key=True) 
    person_fullname: Mapped[str]
    request:Mapped["GuestsModel"] = relationship(back_populates="invited") 

class SecurityModel(Base):
    __tablename__ = "Security"
    sec_id: Mapped[int] = mapped_column(primary_key=True)
    security_fullname: Mapped[str]
    request_approval:Mapped["GuestsModel"] = relationship(back_populates="approved") 
    


    
