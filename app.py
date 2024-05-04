from litestar import Litestar
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend
from litestar.config.cors import CORSConfig
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.di import Provide
from litestar.static_files import create_static_files_router

from src.auth import jwt_auth
# from src.channels.notifications import notifications_handler
from src.db import db_config
from src.dependencies import provide_transaction, limitoffsetpagination
from src.endpoints.auth import register_handler, login_handler
from src.endpoints.requests import RequestsController
from src.endpoints.roles import assign_role_handler, remove_role_handler
from src.endpoints.users import new_password_handler, recovery_password_handler, create_user_handler, get_list_users, get_user_id, get_user_self


async def start() -> None:
    async with db_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


cors_config = CORSConfig(
    allow_origins=["*"],  # Разрешает запросы от всех источников
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Разрешает все эти методы
    allow_headers=["Content-Type", "Authorization"],  # Разрешает заголовки Content-Type и Authorization
    allow_credentials=True  # Разрешает передачу cookies и credentials
)

app = Litestar(
    [register_handler, login_handler, assign_role_handler, remove_role_handler, RequestsController,
     create_user_handler, get_list_users, get_user_id, recovery_password_handler, new_password_handler,
     create_static_files_router(path='/static', directories=['qr'], send_as_attachment=True), get_user_self],
    on_app_init=[jwt_auth.on_app_init],
    on_startup=[start],
    dependencies={"transaction": Provide(provide_transaction),
                  "limit_offset": Provide(limitoffsetpagination, sync_to_thread=False)},
    plugins=[SQLAlchemyPlugin(db_config),
             ChannelsPlugin(backend=MemoryChannelsBackend(), channels=['sec', 'applicant'],
                            arbitrary_channels_allowed=True)],
    cors_config=cors_config,
)
