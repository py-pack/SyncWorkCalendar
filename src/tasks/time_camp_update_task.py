from datetime import datetime

from src.services.time_camp import TCRequestService
from src.dao import TCProjectDAO, TCEntriesDAO
from src.config import settings
from src.core import get_async_asession


class TimeCampUpdateTask:
    def __init__(self):
        self.client = TCRequestService(settings.tc.token)

    async def update_project(self):
        async with get_async_asession() as db:
            projects = self.client.get_projects()
            dao = TCProjectDAO()
            await dao.sync_all(db, projects)

    async def update_entries(self, start_time: datetime, end_time: datetime):
        """
        Обновить все события

        :param start_time: - начало периода, пример:
            datetime = datetime(2024, 7, 1)
        :param end_time: - конец период, пример:
            end_time: datetime = datetime(2024, 8, 31)
        """
        async with get_async_asession() as db:
            entries = self.client.get_entries(start_time, end_time)
            dao = TCEntriesDAO()
            await dao.sync_all_between(db, entries, start_time, end_time)
