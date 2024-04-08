from enum import Enum
from typing import Any, List
from uuid import UUID, uuid4

from litestar import get, post, Request, Response
from litestar.channels import ChannelsPlugin
from litestar.controller import Controller
from litestar.exceptions import HTTPException
from litestar.pagination import OffsetPagination
from litestar.repository.filters import LimitOffset
from litestar.security.jwt import Token
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.endpoints.roles import RolesEnum, get_roles
from src.models.guests import RequestsDto
from src.models.users import Users
from src.schemas.requests import RequestsCreate, RequestsReview


class StatusEnum(Enum):
    NEW = 1
    ACCEPTED = 2
    REJECTED = 3


async def list_requests(db_session: AsyncSession, limit: int = 10, offset: int = 0) -> List[RequestsDto]:
    async with db_session as session:
        statement = select(RequestsDto).options(
            selectinload(RequestsDto.appellant), selectinload(RequestsDto.confirming)
        ).offset(offset).limit(limit)
        result = await session.execute(statement)
        return [it for it in result.scalars()]


async def get_request_by_id(db_session: AsyncSession, request_id: UUID) -> RequestsDto:
    async with db_session as session:
        statement = select(RequestsDto).filter(RequestsDto.id == request_id).options(
            selectinload(RequestsDto.appellant), selectinload(RequestsDto.confirming)
        )
        result = await session.execute(statement)
        obj = result.scalar_one_or_none()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        return obj


class RequestsController(Controller):
    dependencies = {}

    @get(path="/requests/get")
    async def get_list_requests(
            self,
            db_session: AsyncSession,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[RequestsDto]:
        total = await db_session.execute(select(func.count(RequestsDto.id)))
        total_count = total.scalar_one()
        requests = await list_requests(db_session, limit_offset.limit, limit_offset.offset)
        return OffsetPagination[RequestsDto](
            items=requests,
            total=total_count,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @get(path="/requests/{request_id:uuid}")
    async def get_request_id(
            self,
            db_session: AsyncSession,
            request_id: UUID,
    ) -> RequestsDto:
        return await get_request_by_id(db_session, request_id)

    @post(path="/requests/create")
    async def create_request(
            self,
            request: Request[Users, Token, Any],
            transaction: AsyncSession,
            data: RequestsCreate,
            channels: ChannelsPlugin,
    ) -> Any:
        statement = RequestsDto(
            id=uuid4(),
            full_name=data.full_name,
            email_address=data.email_address,
            visit_purpose=data.visit_purpose,
	    place_of_visit=data.place_of_visit,
            datetime_of_visit=data.datetime_of_visit,
            appellant_id=request.user.id,
            status=StatusEnum.NEW.value,
            confirming_id=None,
        )
        transaction.add(statement)
        # applicant_channel = f"applicant_{statement.appellant_id}"
        # await channels.subscribe(applicant_channel)
        #
        # channels.publish({'message': 'New request created, waiting for confirmation'}, 'sec')
        return Response(status_code=202,
                        content={"message": "Request sent to review", "appellant_id": statement.appellant_id})
	    
    @post(path="/requests/review")
    async def request_review(
            self,
            request: Request[Users, Token, Any],
            transaction: AsyncSession,
            data: RequestsReview,
            channels: ChannelsPlugin
    ) -> Response:
        if RolesEnum.confirming.value not in await get_roles(transaction, request.user.id):
            raise HTTPException(status_code=403, detail="Forbidden")
        statement = select(RequestsDto).where(RequestsDto.id == data.request_id)
        result = await transaction.execute(statement)
        result = result.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Request not found")
        result.status = data.status
        result.confirming_id = request.user.id
        #channels.publish({'message': 'Your request has been reviewed'}, 'applicant')
        return Response(status_code=202,
                        content={"message": "Request reviewed successfully", "appellant_id": result.appellant_id})
