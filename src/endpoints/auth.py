from enum import Enum
from uuid import UUID

from litestar import post, Response
from litestar.exceptions import HTTPException, NotFoundException
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import encrypt, jwt_auth, decrypt
from src.models.users import Users, Tokens
from src.schemas.auth import UserRegister, UserLogin


class StatusEnum(Enum):
    awaiting_registration = 0,
    registered = 1


async def get_response_body(session: AsyncSession, user_id: UUID):
    query = select(Users).where(Users.id == user_id)
    existing_user = await session.execute(query)
    existing_user = existing_user.scalar_one()
    response_body = Users(
        id=existing_user.id,
        full_name=existing_user.full_name,
        created_at=existing_user.created_at,
        updated_at=existing_user.updated_at,
    )
    return response_body


@post('/register/{token: str}')
async def register_handler(data: UserRegister, transaction: AsyncSession, token: str) -> Response[UserLogin]:
    query = select(Tokens).where(Tokens.token == token)
    existing_token = await transaction.execute(query)
    existing_token = existing_token.scalar_one()

    if existing_token.status == StatusEnum.registered.value:
        raise HTTPException(status_code=401, detail="The account is already registered. Contact technical support")
    query = select(Users).where(Users.id == existing_token.user_id)
    existing_user = await transaction.execute(query)
    existing_user = existing_user.scalar_one()
    existing_user.password = encrypt(data.password)

    existing_token.status = StatusEnum.registered.value
    return jwt_auth.login(identifier=str(existing_user.email), send_token_as_response_body=True)


async def get_user_by_email(email: str, session: AsyncSession) -> Users:
    query = select(Users)
    result = await session.execute(query)
    for res in result.scalars():
        print(res.email)
    query = select(Users).where(Users.email == email)
    result = await session.execute(query)
    try:
        return result.scalar_one()
    except NoResultFound as e:
        raise NotFoundException(detail=f"Incorrect email or password") from e


@post('/login')
async def login_handler(data: UserLogin, transaction: AsyncSession) -> Response[UserLogin]:
    user = await get_user_by_email(data.email, transaction)
    try:
        if decrypt(user.password) == data.password:
            return jwt_auth.login(identifier=str(data.email), send_token_as_response_body=True)
        else:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
    except NoResultFound:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
