from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from sqlalchemy import create_engine

from src.models.users import Base

db_config = SQLAlchemyAsyncConfig(
    connection_string="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    metadata=Base.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler,
)
