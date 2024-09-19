from typing import List

from pydantic import BaseModel
from sqlalchemy import select

from src.core import db_helper


class BaseDAO:
    model = None

    @classmethod
    async def all(cls):
        async with db_helper.session_factory() as session:
            result = await session.execute(select(cls.model))
            return result.scalars().all()

    @classmethod
    async def sync_all(cls, dto_list: List[BaseModel]):
        models = await cls.all()
        await cls._sync(dto_list, models)

    @classmethod
    async def update_by_keys(cls, new_dto_list: List[BaseModel], key_sync: str = 'id'):
        model_keys_by_sync = [getattr(model, key_sync) for model in new_dto_list]
        async with db_helper.session_factory() as db:
            models_list = (await db.execute(
                select(cls.model).where(
                    getattr(cls.model, key_sync).in_(model_keys_by_sync))
            )).scalars().all()

            models_dict_key = {getattr(model, key_sync): model for model in models_list}

            await cls._sync_dto_with_models(
                db,
                key_sync,
                new_dto_list,
                models_dict_key
            )

    @classmethod
    async def _sync(cls, new_dto_list: list[BaseModel], dao_db_list: list, key_sync: str = 'id'):
        row_exist_db = {getattr(model, key_sync): model for model in dao_db_list}

        keys_for_del = row_exist_db.keys() - [getattr(id_prjc, key_sync) for id_prjc in new_dto_list]

        async with db_helper.session_factory() as db:
            await cls._sync_dto_with_models(
                db,
                key_sync,
                new_dto_list,
                row_exist_db
            )

            for id_del in keys_for_del:
                project_del = row_exist_db.get(id_del)
                if project_del is not None:
                    await db.delete(project_del)
                    await db.commit()

    @classmethod
    async def _sync_dto_with_models(cls, db, key_sync, new_dto_list, models_dict_key):
        for new_dto in new_dto_list:
            new_dto_dict = new_dto.model_dump()

            model_update = models_dict_key.get(getattr(new_dto, key_sync))
            if model_update is None:
                new_model = cls.model.create(**new_dto_dict)
                db.add(new_model)
            else:
                model_update.fill(**new_dto_dict)
                db.add(model_update)

            await db.commit()

    @classmethod
    async def create_or_update(cls, new_dto_list: list[BaseModel], key_sync: str = 'id'):
        pass
