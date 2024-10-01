from .base_dao import BaseDAO
from ..models import WorklogSyncTask


class WorklogSyncTaskDAO(BaseDAO):
    model = WorklogSyncTask
