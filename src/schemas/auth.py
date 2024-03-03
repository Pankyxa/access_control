from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    encrypted_password: str


class UserLogin(BaseModel):
    email: EmailStr
    encrypted_password: str
