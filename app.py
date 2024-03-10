from litestar import Litestar
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.di import Provide

from src.endpoints.auth import register_handler, login_handler
from src.endpoints.roles import assign_role_handler, remove_role_handler
from src.endpoints.func import GuestsController
from src.auth import jwt_auth
from src.db import db_config
from src.dependencies import provide_transaction, limitoffsetpagination


async def start() -> None:
    async with db_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


app = Litestar(
    [register_handler, login_handler, assign_role_handler, remove_role_handler, GuestsController],
    on_app_init=[jwt_auth.on_app_init],
    on_startup=[start],
    dependencies={"transaction": Provide(provide_transaction), 
                  "limit_offset": Provide(limitoffsetpagination, sync_to_thread=False)},
    plugins=[SQLAlchemyPlugin(db_config)],
)
