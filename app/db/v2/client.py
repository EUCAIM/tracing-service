from app.core.settings import DatabaseSettings, get_settings
# from asyncpg import create_pool, Pool
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr


class DBPool:
    def __init__(self):
        self._pool: AsyncConnectionPool | None = None

    async def start(self, settings: DatabaseSettings, database_password: SecretStr) -> None:
        if self._pool is not None:
            raise RuntimeError("Pool already started")

        self._pool = AsyncConnectionPool(
            conninfo=(
            f"host={settings.host} "
            f"port={settings.port} "
            f"dbname={settings.name} "
            f"user={settings.user} "
            f"password={database_password.get_secret_value()}"
        ),
            min_size=settings.pool.min_size,
            max_size=settings.pool.max_size,
            open=False,
        )

        await self._pool.open()

    async def stop(self) -> None:
        if self._pool is None:
            raise RuntimeError(
                "No pool has been created; call start() first"
            )

        if self._pool.closed:
            raise RuntimeError("Pool already closed")

        await self._pool.close()
        self._pool = None

    def get_pool(self) -> AsyncConnectionPool:
        if self._pool is None or self._pool.closed:
            raise RuntimeError("Pool not available")

        return self._pool
