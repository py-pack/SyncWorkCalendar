from datetime import datetime

from sqlalchemy import update

from app.core import get_async_asession
from app.dao import (
    TCProjectDAO,
    TCEntriesDAO,
    WorklogSyncTaskDAO,
    JRIssuesDAO,
    JRWorklogDAO,
)
from app.models import TCProject, TCEntry, WorklogSyncTask, StatusTaskEnum
from app.services.jira import JiraService

from app.config import settings

from app.tasks.jira_update_task import UpdateJiraTask


class WorllogSyncTask:
    def __init__(self):
        self.jira_client = JiraService(settings.jira.token)

    @classmethod
    async def create_task_for_sync(cls, start_date: datetime, end_date: datetime):
        async with get_async_asession() as db:
            dao = TCEntriesDAO()
            worklogs_dict = await dao.get_entries_for_worklogs(db, start_date, end_date)

            dao_wst = WorklogSyncTaskDAO()
            for worklog in worklogs_dict:
                exist = await dao_wst.exists(db, worklog.source_id, 'source_id')
                if not exist:
                    wst = WorklogSyncTask.create(**worklog.model_dump())
                    db.add(wst)
                    await db.commit()

    @classmethod
    async def before_create(cls, start_date: datetime, end_date: datetime):

        async with get_async_asession() as db:
            all_tasks: list[WorklogSyncTask] = await WorklogSyncTaskDAO.get_by_period_and_status(
                db,
                start_date,
                end_date,
                status=StatusTaskEnum.pre_create
            )
            all_keys_task = set(task.issue_key for task in all_tasks)
            keys_jr = await JRIssuesDAO.get_in_keys(db, all_keys_task)

            keys_except = all_keys_task - set(jr.key for jr in keys_jr)

            if keys_except:
                jira_service = UpdateJiraTask()
                await jira_service.update_jira_issues(keys_except)

            jira_id_keys = await JRIssuesDAO.get_in_keys(db, all_keys_task)
            jira_key_dict = {jirad.key: jirad.id for jirad in jira_id_keys}

            for task in all_tasks:
                task.issue_id = jira_key_dict.get(task.issue_key)
                task.status = StatusTaskEnum.create
                await db.commit()

    async def push_one(self, task_id: int, worker: str | None = None) -> dict:
        """Точковий пуш одного `WorklogSyncTask` у Tempo (пер-рядкова дія екрана).

        Дзеркалить `create_worklogs`, але обмежене одним записом і з дедупом проти
        `jr_worklogs` (як реконсиляція): якщо worklog уже існує — лінкуємо без
        HTTP. Якщо `issue_id` ще не зарезолвлено — підтягуємо задачу за ключем.
        Ідемпотентно: уже-`created`/`updated` запис повертає поточний стан.
        """
        actor = worker or settings.current_user
        async with get_async_asession() as db:
            wst = await WorklogSyncTaskDAO.find(db, task_id)
            if wst is None:
                return {"task_id": task_id, "action": "not_found"}

            # Уже в Tempo → нічого не пушимо (точкова дія ідемпотентна).
            if wst.status in (StatusTaskEnum.created, StatusTaskEnum.updated):
                return {
                    "task_id": task_id,
                    "status": wst.status.value,
                    "action": "noop",
                    "target_id": wst.target_id,
                }

            # Резолв issue_id, якщо бракує (підтягуємо задачу за ключем).
            if wst.issue_id is None and wst.issue_key:
                present = await JRIssuesDAO.get_in_keys(db, {wst.issue_key})
                if not present:
                    await UpdateJiraTask().update_jira_issues({wst.issue_key})
                    present = await JRIssuesDAO.get_in_keys(db, {wst.issue_key})
                id_by_key = {row.key: row.id for row in present}
                wst.issue_id = id_by_key.get(wst.issue_key)
                await db.commit()

            if wst.issue_id is None:
                return {
                    "task_id": task_id,
                    "status": wst.status.value,
                    "action": "unresolved_issue",
                }

            # Tempo відхиляє нульову тривалість (VALIDATION_FAILED → 400). Не шлемо
            # такий запис — повертаємо зрозумілий «пропущено» замість помилки.
            if wst.time_spent <= 0:
                return {
                    "task_id": task_id,
                    "status": wst.status.value,
                    "action": "skipped_zero_duration",
                }

            # Дедуп проти реальних Tempo-worklog-ів (capability backend-auto-linking).
            match = await JRWorklogDAO.find_match(
                db,
                jr_issues_id=int(wst.issue_id),
                jr_worker_key=actor,
                started_at=wst.started_at,
                duration=wst.time_spent,
            )
            if match is not None:
                wst.target_id = match.id
                wst.status = StatusTaskEnum.created
                await db.commit()
                return {
                    "task_id": task_id,
                    "status": "created",
                    "action": "deduped",
                    "target_id": match.id,
                }

            result = self.jira_client.create_worklog(
                actor,
                int(wst.issue_id),
                wst.content,
                wst.started_at,
                wst.time_spent,
            )
            wst.target_id = result.get("originId")
            wst.status = StatusTaskEnum.created
            await db.commit()
            return {
                "task_id": task_id,
                "status": "created",
                "action": "pushed",
                "target_id": wst.target_id,
            }

    async def create_worklogs(
        self,
        start_date: datetime,
        end_date: datetime,
        worker: str | None = None,
    ):
        # ``worker`` is the Jira key that owns the produced Tempo worklogs.
        # HTTP callers pass it explicitly from JWT.worker_key; CLI/notebook
        # callers fall back to settings.current_user.
        actor = worker or settings.current_user
        async with get_async_asession() as db:
            all_tasks: list[WorklogSyncTask] = await WorklogSyncTaskDAO.get_by_period_and_status(
                db,
                start_date,
                end_date,
                status=StatusTaskEnum.create
            )

            pushed = skipped = 0
            for wlst in all_tasks:
                # Tempo відхиляє worklog із нульовою тривалістю
                # (`timeSpentSeconds must be > 0`, VALIDATION_FAILED → 400).
                # Пропускаємо такі записи, щоб один нульовий не блокував увесь
                # пуш періоду (раніше — `KeyError: 0`/500 на першому ж).
                if wlst.time_spent <= 0:
                    skipped += 1
                    continue

                result = self.jira_client.create_worklog(
                    actor,
                    int(wlst.issue_id),
                    wlst.content,
                    wlst.started_at,
                    wlst.time_spent
                )

                wlst.target_id = result.get('originId')
                wlst.status = StatusTaskEnum.created
                await db.commit()
                pushed += 1

            return {"pushed": pushed, "skipped": skipped, "total": len(all_tasks)}
