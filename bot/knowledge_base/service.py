from typing import Union

from sqlalchemy import text

from bot.db_connect import async_session
from bot.services.base_service import BaseService, Singleton


class KnowledgeService(BaseService, metaclass=Singleton):

    @classmethod
    async def get_root_divides(cls):

        async with async_session() as session:
            query = text("""
                SELECT id, title
                FROM $_knowledge_base_divides
                WHERE parent_id = 0
            """)

            res = await session.execute(query)
            result = res.mappings().all()

            return result   \

    @classmethod
    async def get_divides_by_root(cls, root_divide_id: Union[int, str]):

        async with async_session() as session:
            query = text(f"""
                SELECT id, title, parent_id
                FROM $_knowledge_base_divides
                WHERE parent_id = {root_divide_id} 
                ORDER BY $_knowledge_base_divides.order_num
            """)

            res = await session.execute(query)
            result = res.mappings().all()

            return result   \

    @classmethod
    async def get_files_by_divide(cls, root_divide_id: Union[int, str]):

        async with async_session() as session:
            query = text(f"""
                SELECT $_knowledge_base.id, $_knowledge_base.title, $_knowledge_base.type_id, $_knowledge_base_divides.parent_id,  $_knowledge_base.document
                FROM $_knowledge_base
                JOIN $_knowledge_base_divides ON $_knowledge_base_divides.id = $_knowledge_base.divide_id
                WHERE $_knowledge_base.divide_id = {root_divide_id} AND $_knowledge_base.available = 1
                ORDER BY $_knowledge_base.order_num
            """)

            res = await session.execute(query)
            result = res.mappings().all()

            return result

    @classmethod
    async def get_file_by_id(cls, file_id: str):

        async with async_session() as session:
            query = text(f"""
                SELECT *
                FROM $_knowledge_base
                WHERE id = {file_id}
            """)

            res = await session.execute(query)
            result = res.mappings().first()

            return result

    @classmethod
    async def get_divides_by_id_list(cls, query: str):

        async with async_session() as session:
            query = text(f"""
                SELECT *
                FROM $_knowledge_base_divides
                WHERE {query}
            """)

            res = await session.execute(query)
            result = res.mappings().all()

            return result

    @classmethod
    async def get_files_by_id_list(cls, query: str):

        async with async_session() as session:
            query = text(f"""
                SELECT *
                FROM $_knowledge_base
                WHERE {query}
            """)

            res = await session.execute(query)
            result = res.mappings().all()

            return result
