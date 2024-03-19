from datetime import datetime
from uuid import uuid4

from litestar import post, Response
from litestar.exceptions import HTTPException, NotFoundException
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import encrypt, jwt_auth, decrypt
from src.models.users import Users
from src.schemas.auth import UserRegister, UserLogin


@post('/register')
async def register_handler(data: UserRegister, transaction: AsyncSession) -> Response[Users]:
    query = select(Users).where(Users.email == data.email)
    existing_user = await transaction.execute(query)
    existing_user = existing_user.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=409, detail="Registration error. Please try again or contact support.")

    user_item = Users(
        id=uuid4(),
        full_name=data.full_name,
        email=data.email,
        encrypted_password=encrypt(data.encrypted_password),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    transaction.add(user_item)
    query = select(Users).where(Users.email == data.email)
    return jwt_auth.login(identifier=str(data.email), response_body=user_item)


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
        if decrypt(user.encrypted_password) == data.encrypted_password:
            return jwt_auth.login(identifier=str(data.email), response_body=data)
        else:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
    except NoResultFound:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
