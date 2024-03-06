from enum import Enum
from uuid import UUID

from litestar.exceptions import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.users import UserRoles, Users, Roles
from typing import Any

from litestar import post, Response, Request
from litestar.security.jwt import Token

from src.schemas.roles import AssignRole


class RolesEnum(Enum):
    employee = 1
    security = 2
    confirming = 3
    admin = 4


async def get_roles(session: AsyncSession, user_id: UUID) -> [int]:
    result = []
    query = select(UserRoles).where(UserRoles.user_id == user_id)
    existing_user = await session.execute(query)
    existing_user = existing_user.scalars().all()
    for user in existing_user:
        result.append(user.role_id)
    return result


@post('/role/assign')
async def assign_role_handler(
        request: "Request[Users, Token, Any]",
        data: AssignRole,
        transaction: AsyncSession
) -> Any:
    if RolesEnum.admin.value not in await get_roles(transaction, request.user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if data.role_id in await get_roles(transaction, data.user_id):
        raise HTTPException(status_code=403, detail="User already has this role")
    user_item = UserRoles(
        user_id=data.user_id,
        role_id=data.role_id,
    )
    transaction.add(user_item)
    return Response(status_code=202, content={"message": "Role added successfully"})


@post('/role/remove')
async def remove_role_handler(
        request: "Request[Users, Token, Any]",
        data: AssignRole,
        transaction: AsyncSession
) -> Any:
    if RolesEnum.admin.value not in await get_roles(transaction, request.user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if data.role_id not in await get_roles(transaction, data.user_id):
        raise HTTPException(status_code=403, detail="User does not have this role")
    if data.user_id == request.user.id:
        raise HTTPException(status_code=403, detail="You can't delete your roles")
    rem = delete(UserRoles).where(UserRoles.user_id == data.user_id and UserRoles.role_id == data.role_id)
    await transaction.execute(rem)
    return Response(status_code=200, content={"message": "Role removed"})
