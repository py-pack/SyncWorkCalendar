from app.dao.base_dao import BaseDAO
from app.models import TCProject


class TCProjectDAO(BaseDAO):
    model = TCProject
