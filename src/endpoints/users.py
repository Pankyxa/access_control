from typing import Any, List, Optional
from uuid import uuid4, UUID

from advanced_alchemy.filters import LimitOffset
from litestar import post, Request, Response, get
from litestar.exceptions import HTTPException
from litestar.pagination import OffsetPagination
from litestar.security.jwt import Token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.endpoints.roles import RolesEnum, get_roles
from src.models.users import Users, UserRoles, Tokens
from src.schemas.auth import CreateUser
from src.schemas.requests import UserSerialize
from src.utils import unique_token_generator, send_message


@post('users/create')
async def create_user_handler(
        request: 'Request[Users, Token, Any]',
        data: CreateUser,
        transaction: AsyncSession
) -> Response:
    query = select(Users).where(Users.email == data.email)
    existing_user = await transaction.execute(query)
    existing_user = existing_user.scalar_one_or_none()

    if RolesEnum.admin.value not in await get_roles(transaction, request.user.id):
        raise HTTPException(status_code=403, detail="Forbidden")

    if existing_user:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    user = Users(
        id=uuid4(),
        full_name=data.full_name,
        email=data.email,
        password=None,
    )
    transaction.add(user)
    await transaction.flush()

    for i in data.roles:
        user_roles = UserRoles(
            user_id=user.id,
            role_id=i
        )
        transaction.add(user_roles)
    await transaction.flush()

    token = await unique_token_generator(transaction)
    tokens = Tokens(
        id=uuid4(),
        user_id=user.id,
        token=token,
        created_by=request.user.id,
        status=0,
    )
    transaction.add(tokens)

    url = str(request.url.scheme) + '://' + str(request.url.netloc) + '/register/' + str(token)

    message = f'Вы были зарегестрированы в системе "Допуск на ТИУ третьих лиц". Перейдите по ссылке чтобы завершить регистрацию: {url}'
    html_message = f'''
            <html>
                <body>
                    <p>{message}</p>
                </body>
            </html>
            '''

    await send_message(str(user.email), html_message)

    return Response(status_code=202,
                    content={"message": "A link has been sent to the user to complete the registration",
                             'token': token})


async def list_users(
        session: AsyncSession,
        role: Optional[RolesEnum] = None,
        limit: int = 10,
        offset: int = 0
) -> List[Users]:
    query = select(Users).options(selectinload(Users.roles)).order_by(Users.created_at.desc())

    if role:
        query = query.join(UserRoles, Users.id == UserRoles.user_id).where(
            UserRoles.role_id == role.value
        ).distinct()

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return [it for it in result.scalars()]


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Users:
    statement = select(Users).filter(Users.id == user_id).options(
        selectinload(Users.roles)
    )
    result = await session.execute(statement)
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


@get(path='/users')
async def get_list_users(
        transaction: AsyncSession,
        limit_offset: LimitOffset,
        role: Optional[RolesEnum]
) -> OffsetPagination[UserSerialize]:
    users = await list_users(transaction, role, limit_offset.limit, limit_offset.offset)
    pydantic_users = [UserSerialize.from_orm(usr) for usr in users]
    total = len(pydantic_users)
    return OffsetPagination[UserSerialize](
        items=pydantic_users,
        total=total,
        limit=limit_offset.limit,
        offset=limit_offset.offset,
    )


@get(path="/users/{user_id:uuid}")
async def get_user_id(
        transaction: AsyncSession,
        user_id: UUID,
) -> UserSerialize:
    request = await get_user_by_id(transaction, user_id)
    return UserSerialize.from_orm(request)
