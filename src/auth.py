import base64
from typing import Any

from cryptography.fernet import Fernet
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token
from sqlalchemy import select

from src.db import db_config
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


async def retrieve_user_handler(
        token: Token,
        _: "ASGIConnection[Any]",
) -> Users | None:
    async with db_config.get_session() as session:
        result = await session.execute(
            select(Users)
            .where(
                Users.email == token.sub
            )
        )
        result = result.scalar_one()
    return result


jwt_auth = JWTAuth[Users](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=settings.jwt_secret,
    exclude=["/register", "/login", "/schema"],
)
