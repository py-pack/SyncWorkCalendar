from .base_dao import BaseDAO
from src.models import JRProject


class JRProjectDAO(BaseDAO):
    model = JRProject
