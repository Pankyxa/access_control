from litestar import Litestar
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend
from litestar.config.cors import CORSConfig
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.di import Provide

from src.auth import jwt_auth
# from src.channels.notifications import notifications_handler
from src.db import db_config
from src.dependencies import provide_transaction, limitoffsetpagination
from src.endpoints.auth import register_handler, login_handler
from src.endpoints.requests import RequestsController
from src.endpoints.roles import assign_role_handler, remove_role_handler
from src.endpoints.users import create_user_handler, get_list_users, get_user_id


async def start() -> None:
    async with db_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


cors_config = CORSConfig(allow_origins=['*'])

app = Litestar(
    [register_handler, login_handler, assign_role_handler, remove_role_handler, RequestsController,
     create_user_handler, get_list_users, get_user_id],
    on_app_init=[jwt_auth.on_app_init],
    on_startup=[start],
    dependencies={"transaction": Provide(provide_transaction),
                  "limit_offset": Provide(limitoffsetpagination, sync_to_thread=False)},
    plugins=[SQLAlchemyPlugin(db_config),
             ChannelsPlugin(backend=MemoryChannelsBackend(), channels=['sec', 'applicant'],
                            arbitrary_channels_allowed=True)],
    cors_config=cors_config,
)
