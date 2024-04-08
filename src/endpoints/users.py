from typing import Any
from uuid import uuid4

from litestar import post, Request, Response
from litestar.exceptions import HTTPException
from litestar.security.jwt import Token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.endpoints.roles import RolesEnum, get_roles
from src.models.users import Users, UserRoles, Tokens
from src.schemas.auth import CreateUser
from src.utils import unique_token_generator, send_message


@post('user/create')
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

    message = (f'You have been registered in the Third Party TIU Eligibility System, '
               f'please follow the link to complete your registration: {url}')

    await send_message(str(user.email), message)

    return Response(status_code=202,
                    content={"message": "A link has been sent to the user to complete the registration"})
