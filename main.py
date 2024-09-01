import asyncio

from datetime import datetime
from src.config import settings

from src.services.time_camp import TCRequestService
from src.dao import TCEntriesDAO, TCProjectDAO


async def main():

    client = TCRequestService(settings.tc.token)

    # TC Project
    tc_project = client.get_projects()
    await TCProjectDAO.sync_all(tc_project)

    # TC Enties
    date_from = datetime.strptime("2024-07-01", "%Y-%m-%d")
    date_to = datetime.strptime("2024-07-31", "%Y-%m-%d")

    tc_entries = client.get_entries(date_from, date_to)
    await TCEntriesDAO.sync_all_between(tc_entries, date_from, date_to)

    # JIRA Project

if __name__ == '__main__':
    asyncio.run(main())
