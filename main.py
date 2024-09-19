import asyncio

from datetime import datetime
from src.config import settings

from src.services.time_camp import TCRequestService
from src.services.jira import JiraService
from src.dao import TCEntriesDAO, TCProjectDAO, JRProjectDAO


async def main():

    await sync_time_camp()

    await sync_jira()


async def sync_jira():
    client = JiraService(settings.jira.token)
    jira_projects = client.get_projects()

    await JRProjectDAO.sync_all(jira_projects)


async def sync_time_camp():
    client = TCRequestService(settings.tc.token)
    # TC Project
    tc_project = client.get_projects()
    await TCProjectDAO.sync_all(tc_project)
    # TC Enties
    date_from = datetime.strptime("2024-07-01", "%Y-%m-%d")
    date_to = datetime.strptime("2024-07-31", "%Y-%m-%d")
    tc_entries = client.get_entries(date_from, date_to)
    await TCEntriesDAO.sync_all_between(tc_entries, date_from, date_to)


if __name__ == '__main__':
    asyncio.run(main())
