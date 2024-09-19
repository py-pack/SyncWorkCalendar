from src.models import JRUser
from .base_dao import BaseDAO


class JRUsersDAO(BaseDAO):
    model = JRUser
