from enum import Enum
from uuid import UUID, uuid4
from typing import Any

from litestar import post, put, Response, Request
from litestar.exceptions import HTTPException, NotFoundException
from litestar.security.jwt import Token
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import encrypt, jwt_auth, decrypt
from src.models.users import Users, Tokens
from src.schemas.auth import UserRegister, UserLogin
from src.utils import unique_token_generator, send_message


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
            return jwt_auth.login(identifier=str(user.email),
                                  token_extras={"full_name": user.full_name, "id": str(user.id),
                                                "roles": [int(role.id) for role in user.roles]},
                                  send_token_as_response_body=True)
        else:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
    except NoResultFound:
        raise HTTPException(status_code=401, detail="Incorrect email or password")


@post('/recovery_password')
async def recovery_password_handler(
        transaction: AsyncSession,
        request: 'Request[Users, Token, Any]',
        email: str
) -> Response:
    query = select(Users).where(Users.email == email)
    existing_user = await transaction.execute(query)
    existing_user = existing_user.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")

    token = await unique_token_generator(transaction)
    tokens = Tokens(
        id=uuid4(),
        user_id=existing_user.id,
        token=token,
        created_by=existing_user.id,
        status=0,
    )
    transaction.add(tokens)
    await transaction.flush()

    url = str(request.url.scheme) + '://' + str(request.url.netloc) + f'/new_password/{token}'

    message = f'Для восстановления пароля перейдите по ссылке: {url}'
    html_message = f'''
        <html>
            <body>
                <p>{message}</p>
            </body>
        </html>
    '''

    await send_message(str(existing_user.email), html_message)

    return Response(status_code=202, content={
        "message": "A link has been sent to the user to recovery the password", "token": token})


@put('/new_password/{token: str}')
async def new_password_handler(
    token: str,
    new_password: str,
    transaction: AsyncSession
) -> Response:
    query = select(Tokens).where(Tokens.token == token)
    existing_token = await transaction.execute(query)
    existing_token = existing_token.scalar_one()

    if not existing_token:
        raise HTTPException(status_code=404, detail="Token not found")

    if existing_token.status != 0:
        raise HTTPException(status_code=400, detail="Invalid token")

    query = update(Users).where(Users.id == existing_token.user_id).values(password=encrypt(new_password))
    await transaction.execute(query)

    existing_token.status = 1
    await transaction.flush()

    return Response(status_code=200, content={"message": "The new password has been successfully set"})
