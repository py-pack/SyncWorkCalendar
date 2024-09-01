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
    async def _sync(cls, new_dto_list: list[BaseModel], dao_db_list: list):
        row_exist_db = {model.id: model for model in dao_db_list}

        id_for_del = row_exist_db.keys() - [id_prjc.id for id_prjc in new_dto_list]

        async with db_helper.session_factory() as db:
            for new_dto in new_dto_list:
                new_dto_dict = new_dto.model_dump()

                project_update = row_exist_db.get(new_dto.id)
                if project_update is None:
                    new_project = cls.model.create(**new_dto_dict)
                    db.add(new_project)
                else:
                    project_update.fill(**new_dto_dict)
                    db.add(project_update)

                await db.commit()

            for id_del in id_for_del:
                project_del = row_exist_db.get(id_del)
                if project_del is not None:
                    await db.delete(project_del)
                    await db.commit()
