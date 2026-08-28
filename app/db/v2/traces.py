
from typing import Final
# from asyncpg import Pool
from app.core.exceptions import NotFoundException, DataIntegrityException
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Json

from app.models.v2.traces import Trace, TraceDatasetAdapter
from datetime import datetime
from app.core.logging import logging

logger = logging.getLogger(__name__)

class TracesRepo:

    DATASETS_TABLE: Final[str] = "DATASETS_V2"

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def add(self, trace: Trace) -> None:
        keys, values = map(list, zip(*trace.model_dump().items()))
        mapped_values = []
        for v in values:
            if isinstance(v, list):
                mapped_values.append(Json(v))
            elif isinstance(v, datetime):
                mapped_values.append(v.isoformat())
            else:
                mapped_values.append(v)
        # placeholders = []
        # for k in keys:
        #     # if k == "created_at":
        #     #     placeholders.append("CAST(%s AS TIMESTAMP)")
        #     # else:
        #         placeholders.append("%s")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                placeholders_joined = ', '.join(["%s" for i in range(len(keys))])
                columns = ', '.join(keys)
                await cur.execute(f"""
                    INSERT INTO {self.DATASETS_TABLE} ({columns}) VALUES ({placeholders_joined})
                """, mapped_values, prepare=False)

    async def get_traces(self, limit, offset, filter_fields: dict[str, str | int | bool]) -> tuple[list[Trace], int]:
        async with self.pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor(row_factory=dict_row) as cur:
                    filters: list[tuple[str, str]] = self.get_filters(filter_fields)
                    filters_str = ""
                    if len(filters) > 0:
                        filters_names, filters_values = map(list, zip(*filters)) 
                        fj = " AND ".join(filters_names)
                        filters_str = f" WHERE {fj} "
                    else:
                        filters_values = []
                    await cur.execute(f"""
                            SELECT * FROM {self.DATASETS_TABLE} {filters_str} ORDER BY created_at DESC LIMIT %s OFFSET %s
                        """, (*filters_values, limit, offset), prepare=False)
                    rows = await cur.fetchall()
                    await cur.execute(f"SELECT COUNT(*) AS total FROM {self.DATASETS_TABLE} {filters_str}", 
                        filters_values, prepare=False)
                    row = await cur.fetchone()
                    total = row["total"]
                    return [TraceDatasetAdapter.validate_python(r) for r in rows], total

    async def get_trace(self, trace_id: str) -> Trace:
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(f"SELECT * FROM {self.DATASETS_TABLE} WHERE id = '{trace_id}'")
                rows = await cur.fetchall() 
                if len(rows) == 0:
                    raise NotFoundException(f"Trace with ID {trace_id} not found.")
                if len(rows) > 1:
                    raise DataIntegrityException(f"Multiple traces with ID {trace_id} found.")
                return TraceDatasetAdapter.validate_python(rows[0])


    # async def execute(self, queries: list[tuple[str, tuple]]): #query:str, args:tuple=()):
    #     async with self.pool.acquire() as conn:
    #         async with conn.cursor() as cur:
    #             async with conn.transaction():
    #                 for query, args in queries:
    #                     await cur.execute(query, args)


    # def get_kvs(self, obj: BaseModel) -> tuple[list[str], list[any]]:
    #     return list(obj.model_dump().items())

    def get_filters(self, filterFields: dict[str, str | int | bool]) -> list[tuple[str, str]]:
        filters: list[tuple[str, str]] = []
        
        for k,v in filterFields.items():
            if k == "dataset_id":
                filters.append((" datasets_ids LIKE %s ", f'%%"{v}"%%'))
            else:
                filters.append((f" {k} = %s ", f'{v}'))
        return filters