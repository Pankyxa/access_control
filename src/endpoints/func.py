from uuid import UUID
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from litestar import get
from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from litestar.controller import Controller
from litestar.di import Provide
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset

from src.schemas.pydantic_models import Guests
from src.models.guests import GuestsModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.guests import GuestsModel

class GuestsRepository(SQLAlchemyAsyncRepository[GuestsModel]):
    model_type = GuestsModel
    
async def guestsrepo(db_session: AsyncSession) -> GuestsRepository:
    return GuestsRepository(session=db_session)


async def guestsdetailsrepo(db_session: AsyncSession) -> GuestsRepository:
    return GuestsRepository(
        statement=select(GuestsModel).options(selectinload(GuestsModel.invited)),
        session=db_session,
    )  
    

class GuestsController(Controller):
    dependencies = {"guests_repo": Provide(guestsrepo)}
    
    @get(path="/")
    async def page(self) -> str:
        return " "  
    
    @get(path="/guests")
    async def list_guests(
        self, guests_repo: GuestsRepository, limit_offset: LimitOffset,
    ) -> OffsetPagination[Guests]:
        results, total = await guests_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[Guests])
        return OffsetPagination[Guests](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )         
        
    @get(path="/guests/{guests_id:uuid}", dependencies={"guests_repo": Provide(guestsdetailsrepo)})
    async def get_guest(
    self, guests_repo: GuestsRepository, guests_id: UUID = Parameter(title="Guest ID",),
    ) -> Guests:
        obj = await guests_repo.get(guests_id)
        return Guests.model_validate(obj)

    