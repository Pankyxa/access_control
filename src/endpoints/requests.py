import os
from enum import Enum
from typing import Any, List, Optional, Tuple
from uuid import UUID, uuid4

import qrcode
from litestar import get, post, Request, Response
from litestar.channels import ChannelsPlugin
from litestar.controller import Controller
from litestar.exceptions import HTTPException
from litestar.security.jwt import Token
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.endpoints.roles import RolesEnum, get_roles
from src.models.requests import RequestsDto, Guests
from src.models.users import Users
from src.schemas.requests import RequestsCreate, RequestsReview, Requests, RequestsDelete
from src.utils import send_message


class StatusEnum(Enum):
    NEW = 1
    ACCEPTED = 2
    REJECTED = 3


class VisitStatusEnum(Enum):
    PENDING = 1
    ENTERED = 2
    EXITED = 3


async def list_requests(
        db_session: AsyncSession,
        request: 'Request[Users, Token, Any]',
        status: Optional[StatusEnum] = None,
        fullname: Optional[str] = None,
        appellant: Optional[str] = None
) -> List[RequestsDto]:
    async with (db_session as session):
        query = select(RequestsDto).options(
            selectinload(RequestsDto.appellant),
            selectinload(RequestsDto.confirming),
            selectinload(RequestsDto.guest)
        ).order_by(RequestsDto.datetime.desc())

        if status:
            query = query.where(RequestsDto.status == status.value).distinct()

        if fullname:
            query = query.join(Guests, RequestsDto.guest).where(Guests.full_name.like(f'%{fullname}%')).distinct()

        if appellant:
            query = query.join(Users, RequestsDto.appellant).where(Users.full_name
                                                                   .like(f'%{appellant}%')).distinct()

        result = await session.execute(query)
        return [it for it in result.scalars()]


async def get_request_by_id(session: AsyncSession, request_id: UUID) -> RequestsDto:
    async with session as session:
        statement = select(RequestsDto).filter(RequestsDto.id == request_id).options(
            selectinload(RequestsDto.appellant), selectinload(RequestsDto.confirming),
            selectinload(RequestsDto.guest)
        )
        result = await session.execute(statement)
        obj = result.scalar_one_or_none()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        return obj


async def create_guests(session: AsyncSession, data: RequestsCreate, request_id: UUID):
    for i in range(len(data.full_name)):
        statement = Guests(
            id=uuid4(),
            request_id=request_id,
            full_name=data.full_name[i],
            email=data.email[i],
            phone_number=data.phone_number[i],
            is_foreign=data.is_foreign[i],
            visit_status=VisitStatusEnum.PENDING.value
        )
        session.add(statement)


class RequestsController(Controller):

    @get(path="/requests")
    async def get_list_requests(
            self,
            transaction: AsyncSession,
            request: 'Request[Users, Token, Any]',
            status: Optional[StatusEnum] = None,
            fullname: Optional[str] = None,
            appellant: Optional[str] = None
    ) -> List[Requests]:
        if len(request.user.roles) == 1 and RolesEnum.employee.value in await get_roles(transaction, request.user.id):
            requests = await list_requests(
                transaction,
                request,
                status=status,
                fullname=fullname,
                appellant=request.user.full_name
            )
        else:
            requests = await list_requests(
                transaction,
                request,
                status=status,
                fullname=fullname,
                appellant=appellant
            )

        return [Requests.from_orm(req) for req in requests]

    @get(path="/requests/{request_id:uuid}")
    async def get_request_id(
            self,
            transaction: AsyncSession,
            request_id: UUID,
    ) -> Requests:
        request = await get_request_by_id(transaction, request_id)
        return Requests.from_orm(request)

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
            visit_purpose=data.visit_purpose,
            place_of_visit=data.place_of_visit,
            datetime_of_visit=data.datetime_of_visit,
            appellant_id=request.user.id,
            status=StatusEnum.NEW.value,
            confirming_id=None,
        )
        transaction.add(statement)

        await create_guests(transaction, data, statement.id)

        # applicant_channel = f"applicant_{statement.appellant_id}"
        # await channels.subscribe(applicant_channel)
        #
        # channels.publish({'message': 'New request created, waiting for confirmation'}, 'sec')
        return Response(status_code=202,
                        content={"message": "Request sent to review", "appellant_id": statement.appellant_id})

    @post(path="/requests/remove")
    async def remove_request(
            self,
            request: Request[Users, Token, Any],
            transaction: AsyncSession,
            data: RequestsDelete,
    ) -> Response:
        if RolesEnum.admin.value not in await get_roles(transaction, request.user.id):
            raise HTTPException(status_code=403, detail="Forbidden")

        statement = select(RequestsDto).where(RequestsDto.id == data.request_id)
        obj = await transaction.execute(statement)
        obj = obj.scalar_one_or_none()

        if obj is None:
            raise HTTPException(status_code=404, detail="Request not found")

        await transaction.delete(obj)
        return Response(status_code=200, content={"message": "Request removed"})

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

        if data.status == StatusEnum.ACCEPTED.value:
            url = str(request.url.scheme) + '://' + str(request.url.netloc) + '/requests/' + str(data.request_id)
            qr_code_image = qrcode.make(url)
            if not os.path.isdir('qr'):
                os.mkdir('qr')
            if not os.path.isdir(f'qr/{result.datetime_of_visit.date()}'):
                os.mkdir(f'qr/{result.datetime_of_visit.date()}')
            path = f'qr/{result.datetime_of_visit.date()}/{data.request_id}.png'
            qr_code_image.save(path)

            message = f'''{result.appellant.full_name} назначил вам встречу.\nМесто встречи: {result.place_of_visit}.\nВремя встречи: {result.datetime_of_visit.date()} {result.datetime_of_visit.hour}:{result.datetime_of_visit.minute}.\nПредъявите данный qr-код охране при входе.'''
            message = message.split('\n')
            src = f"{str(request.url.scheme)}://{str(request.url.netloc)}/static/{path[3:]}"
            html_message = f'''
                <html lang="ru">
                <head>
                    <meta charset="utf-8">
                    <meta content="IE=edge" http-equiv="X-UA-Compatible">
                    <meta content="width=device-width,initial-scale=1.0" name="viewport">
                    <link href="<%= BASE_URL %>favicon.ico" rel="icon">
                    <title><%= htmlWebpackPlugin.options.title %></title>
                </head>
                <body style="background-color: blue; font-family: 'Inter', sans-serif; justify-content: center; display: flex; padding-top: 50px; padding-bottom: 50px">
                <div style="text-align:center;background-color:white;width:700px;border-radius:11px;margin:auto;padding-bottom: 22px;padding-top: 22px;">
                    <h1>{result.appellant.full_name} назначил вам встречу</h1>
                    <h2>Место встречи: {result.place_of_visit}</h2>
                    <h2>Время встречи: {result.datetime_of_visit.date()} {result.datetime_of_visit.hour}:{result.datetime_of_visit.minute}</h2>
                    <h2>Предъявите QR-код при входе</h2>
                    <img alt="hh" src={src}>
                </div>
                </body>
            '''
            print(html_message)
            for guest in result.guest:
                await send_message(guest.email, html_message)

            html_message = f'''
            <html>
                <body>
                    <p>Ваша заявка {result.id} была одобрена!</p>
                </body>
            </html>
            '''
            await send_message(result.appellant.email, html_message)
        else:
            html_message = f'''
                        <html>
                            <body>
                                <p>Ваша заявка {result.id} была отклонена!</p>
                            </body>
                        </html>
                        '''
            await send_message(result.appellant.email, html_message)

        # channels.publish({'message': 'Your request has been reviewed'}, 'applicant')
        return Response(status_code=202,
                        content={"message": "Request reviewed successfully", "appellant_id": result.appellant_id})
