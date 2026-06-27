"""Чистка дубльованих Tempo-worklog-ів (capability `api-worklog-dedup`, D2/D3).

По кожній обраній групі: лишити один канонічний worklog (явний `WST.target_id`,
інакше найменший `id`), решту **реально видалити з Tempo** (`JiraService.
delete_worklog`), перелінкувати на канонічний будь-який `WST.target_id` зайвого і
прибрати локальний рядок `jr_worklogs` — **лише** після успішного Tempo DELETE.
Помилка видалення одного worklog-а не валить усю дію: збирається в `errors`,
локальне дзеркало для нього лишається, чистка триває далі.
"""

from app.core import get_async_asession
from app.config import settings
from app.dao import JRWorklogDAO
from app.services.jira import JiraService


class WorklogDedupTask:
    def __init__(self):
        self.jira_client = JiraService(settings.jira.token)

    async def run(self, groups: list[list[int]], worker: str) -> dict:
        """Прибрати дублі для переданих груп; повернути `{deleted, kept, groups, errors}`."""
        deleted = 0
        kept = 0
        errors: list[dict] = []

        async with get_async_asession() as db:
            for ids in groups:
                # Лише ті worklog-и групи, що реально існують у дзеркалі.
                rows = await JRWorklogDAO.get_by_ids(db, ids)
                existing = [r.id for r in rows]
                if not existing:
                    continue

                linked_ids = await JRWorklogDAO.linked_target_ids(db, existing)
                canonical = JRWorklogDAO.choose_canonical(existing, linked_ids)
                kept += 1
                victims = [i for i in existing if i != canonical]

                for vid in victims:
                    try:
                        # Незворотне видалення з Tempo (raise_on_error=True).
                        self.jira_client.delete_worklog(vid, worker)
                    except Exception as exc:
                        # Помилка одного worklog-а — у підсумок, рядок не чіпаємо.
                        errors.append({"worklog_id": vid, "reason": str(exc)})
                        continue

                    # Лінк зайвого → на канонічний (до видалення, щоб не лишити
                    # битий target_id), потім прибрати локальний рядок.
                    await JRWorklogDAO.repoint_links(
                        db, from_id=vid, to_id=canonical
                    )
                    await JRWorklogDAO.delete_by_ids(db, [vid])
                    await db.commit()
                    deleted += 1

        return {
            "deleted": deleted,
            "kept": kept,
            "groups": len(groups),
            "errors": errors,
        }
