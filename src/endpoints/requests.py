from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from litestar import get, post, Request, Response
from litestar.channels import ChannelsPlugin
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset
from litestar.security.jwt import Token
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.endpoints.roles import RolesEnum, get_roles
from src.models.guests import RequestsDto
from src.models.users import Users
from src.schemas.requests import Requests, RequestsCreate, RequestsReview


class GuestsRepository(SQLAlchemyAsyncRepository[RequestsDto]):
    model_type = RequestsDto


async def guestsrepo(db_session: AsyncSession) -> GuestsRepository:
    return GuestsRepository(session=db_session)


async def guestsdetailsrepo(db_session: AsyncSession) -> GuestsRepository:
    return GuestsRepository(
        statement=select(RequestsDto).options(selectinload(RequestsDto.invited)),
        session=db_session,
    )


class StatusEnum(Enum):
    NEW = 1
    ACCEPTED = 2
    REJECTED = 3


class GuestsController(Controller):
    dependencies = {"guests_repo": Provide(guestsrepo)}

    @get(path="/")
    async def page(self) -> str:
        return " "

    @get(path="/requests/get")
    async def list_requests(
            self,
            guests_repo: GuestsRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[Requests]:
        results, total = await guests_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[RequestsDto])
        return OffsetPagination[Requests](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @get(path="/requests/{guests_id:uuid}", dependencies={"guests_repo": Provide(guestsdetailsrepo)})
    async def get_guest(
            self,
            guests_repo: GuestsRepository,
            guests_id: UUID = Parameter(title="Guest ID", ),
    ) -> Requests:
        obj = await guests_repo.get(guests_id)
        return Requests.model_validate(obj)

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
            datetime_of_visit=data.datetime_of_visit,
            appellant_id=request.user.id,
            datetime=datetime.now(),
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
        channels.publish({'message': 'Your request has been reviewed'}, 'applicant')
        return Response(status_code=202,
                        content={"message": "Request reviewed successfully", "appellant_id": result.appellant_id})
