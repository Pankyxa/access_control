import base64
from uuid import UUID

from cryptography.fernet import Fernet
from litestar.security.jwt import JWTAuth
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import Users
from src.settings import settings


def decrypt(enc_token: str):
    key = base64.urlsafe_b64encode(settings.crypt_token.encode("utf-8").ljust(32)[:32])
    fernet = Fernet(key)
    return fernet.decrypt(enc_token.encode("utf-8")).decode('utf-8')


def encrypt(password: str):
    key = base64.urlsafe_b64encode(settings.crypt_token.encode("utf-8").ljust(32)[:32])
    fernet = Fernet(key)
    return fernet.encrypt(password.encode("utf-8")).decode('utf-8')


async def retrieve_user_handler(session: AsyncSession, user_id: UUID) -> Users | None:
    user = await session.get(Users, user_id)
    return user


jwt_auth = JWTAuth[Users](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=settings.jwt_secret,
    exclude=["/register", "/login", "/schema"],
)
