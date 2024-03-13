from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig

from src.models import Base
from src.settings import settings

db_config = SQLAlchemyAsyncConfig(
    connection_string=f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_ip}:{settings.db_port}/{settings.db_name}",
    metadata=Base.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler,
)
