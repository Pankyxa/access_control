from pydantic import BaseModel, EmailStr


class CreateUser(BaseModel):
    full_name: str
    email: EmailStr
    roles: list[int]


class UserRegister(BaseModel):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
