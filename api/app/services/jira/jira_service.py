import logging

import requests

from typing import List, Any
from .dto import JiraUserDTO, JiraIssueDTO, JiraProjectDTO, JiraWorklogDTO
from datetime import datetime, date


logger = logging.getLogger(__name__)


class TempoApiError(RuntimeError):
    """Jira/Tempo REST повернув помилку — несе статус і тіло відповіді.

    Раніше помилку Tempo (напр. `400 Bad Request`) ковтав `_make_request`
    (`return {}`), а виклик `worklogs[0]` маскував її беззмістовним
    `KeyError: 0`. Тепер причину видно: і в `api_jobs.error` (панель Журналу),
    і в логах.
    """

    def __init__(self, method: str, path: str, status_code: int | None, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(
            f"Tempo/Jira {method} {path} → {status_code}: {body or '<порожнє тіло>'}"
        )


class JiraService:
    def __init__(self, token: str):
        self._url = "https://leadsdoit.io/jira/rest/"
        self._token = token

    def get_projects(self) -> List[JiraProjectDTO]:
        projects = self._make_request("api/2/project")
        results = [
            JiraProjectDTO(
                id=project.get("id"),
                key=project.get("key"),
                name=project.get("name"),
                is_archved=project.get("archived"),
            )
            for project in projects
        ]
        return results

    def search_issues(self, keys: List[str]) -> List[JiraIssueDTO]:
        """Задачі Jira за списком ключів (JQL `key in (…)`), з пагінацією."""
        if not keys:
            return []
        jql_keys = "key in ({})".format(",".join(keys))
        return self._search(jql_keys)

    def search_issues_by_projects(
        self,
        project_keys: List[str],
        *,
        updated_from: str | None = None,
        updated_to: str | None = None,
        page_size: int = 100,
    ) -> List[JiraIssueDTO]:
        """Задачі заданих проектів (JQL `project in (…)`) з пагінацією.

        На відміну від `search_issues` (за ключами), тягне задачі проектів
        незалежно від worklog-ів і assignee/reporter. Якщо задано
        `updated_from`/`updated_to` (рядки `YYYY-MM-DD`) — обмежує **періодом
        активності** за полем `updated` (задачі, з якими працювали у вікні),
        незалежно від дати створення.
        """
        if not project_keys:
            return []
        quoted = ",".join(
            '"{}"'.format(k.replace('"', "")) for k in project_keys
        )
        clauses = ["project in ({})".format(quoted)]
        if updated_from:
            clauses.append('updated >= "{}"'.format(updated_from))
        if updated_to:
            # «23:59», щоб увесь кінцевий день потрапив у вікно (JQL date → 00:00).
            clauses.append('updated <= "{} 23:59"'.format(updated_to))
        jql = " AND ".join(clauses) + " ORDER BY updated DESC"
        return self._search(jql, page_size=page_size)

    def _search(
        self, jql: str, *, page_size: int | None = None
    ) -> List[JiraIssueDTO]:
        """JQL-пошук `api/2/search` із пагінацією (`startAt`/`maxResults`).

        Цикл триває, доки зібрано всі задачі: спиняється і за досягненням `total`,
        і за порожньою/неповною сторінкою (подвійний захист від нескінченного
        циклу та від збою `_make_request`, що повертає `{}`).
        """
        results: List[JiraIssueDTO] = []
        start_at = 0
        while True:
            data: dict[str, Any] = {"jql": jql, "startAt": start_at}
            if page_size is not None:
                data["maxResults"] = page_size
            resp = self._make_request("api/2/search", method="POST", data=data)

            issues = resp.get("issues") if isinstance(resp, dict) else None
            if not issues:
                break
            for issue in issues:
                dto = self._parse_issue(issue)
                if dto is not None:
                    results.append(dto)

            start_at += len(issues)
            if start_at >= int(resp.get("total", 0) or 0):
                break
            if page_size is not None and len(issues) < page_size:
                break
        return results

    @staticmethod
    def _parse_issue(issue: dict[str, Any]) -> JiraIssueDTO | None:
        """`issue` (dict із Jira) → `JiraIssueDTO`; `None`, якщо немає `fields`.

        Null-safe: відсутні `project`/`creator`/`reporter`/`parent` тощо не валять
        парсинг (важливо для повного витягу проекту, де поля різняться).
        """
        fields: dict | None = issue.get("fields")
        if fields is None:
            return None

        project = None
        project_field: dict | None = fields.get("project")
        if project_field is not None:
            project = JiraProjectDTO(
                id=project_field.get("id"),
                key=project_field.get("key"),
                name=project_field.get("name"),
            )

        creator = None
        creator_field: dict | None = fields.get("creator")
        if creator_field is not None:
            creator = JiraUserDTO(
                key=creator_field.get("key"),
                name=creator_field.get("name"),
                full_name=creator_field.get("displayName"),
                email=creator_field.get("emailAddress"),
            )

        reporter = None
        reporter_field: dict | None = fields.get("reporter")
        if reporter_field is not None:
            reporter = JiraUserDTO(
                key=reporter_field.get("key"),
                name=reporter_field.get("name"),
                full_name=reporter_field.get("displayName"),
                email=reporter_field.get("emailAddress"),
            )

        return JiraIssueDTO(
            id=issue.get("id"),
            key=issue.get("key"),
            name=fields.get("summary"),
            jr_project_id=project.id if project is not None else None,
            epic_key=fields.get("customfield_10005", None),
            parent_key=(fields.get("parent") or {}).get("key"),
            type=(fields.get("issuetype") or {}).get("name", "Task"),
            priority=(fields.get("priority") or {}).get("name", "Medium"),
            status=(fields.get("status") or {}).get("name", "To DO"),
            jr_creator_key=creator.key if creator is not None else None,
            jr_reporter_key=reporter.key if reporter is not None else None,
            estimate_plan=fields.get("timeoriginalestimate", 0),
            estimate_fact=(fields.get("aggregateprogress") or {}).get(
                "progress", 0
            ),
            estimate_rest=fields.get("aggregatetimeestimate", 0),
            created_at=fields.get("created"),
            updated_at=fields.get("updated"),
            project=project,
            creator=creator,
            reporter=reporter,
        )

    def serch_worklogs_by_user(
        self, start: datetime, finish: datetime, user_key: str
    ) -> List[JiraWorklogDTO]:
        data = {
            "from": start.strftime("%Y-%m-%d"),
            "to": finish.strftime("%Y-%m-%d"),
            "worker": [user_key],
        }

        worklogs = self._make_request(
            "tempo-timesheets/4/worklogs/search", method="POST", data=data
        )

        result = [
            JiraWorklogDTO(
                id=worklog.get("originId"),
                jr_issues_id=worklog.get("originTaskId"),
                jr_issues_key=worklog.get("issue", {}).get("key"),
                description=worklog.get("comment"),
                jr_worker_key=worklog.get("worker"),
                started_at=worklog.get("started"),
                duration=worklog.get("timeSpentSeconds"),
                created_at=worklog.get("dateCreated"),
                updated_at=worklog.get("dateUpdated"),
            )
            for worklog in worklogs
        ]

        return result

    def create_worklog(
        self,
        worker: str,
        issue_id: int,
        comment: str,
        start: datetime,
        duration: int,
    ) -> dict:
        data = {
            "worker": worker,
            "originTaskId": issue_id,
            "comment": comment,
            "started": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "timeSpentSeconds": duration,
        }

        worklogs = self._make_request(
            "tempo-timesheets/4/worklogs", method="POST", data=data, raise_on_error=True
        )

        # Tempo на успіх повертає непорожній список створених worklog-ів. Будь-яка
        # помилка вже кинулась як TempoApiError (raise_on_error=True), тож сюди
        # доходить лише успіх; гард — на несподіваний порожній/інший шейп.
        if isinstance(worklogs, list) and worklogs:
            return dict(worklogs[0])
        if isinstance(worklogs, dict) and worklogs:
            return dict(worklogs)
        raise TempoApiError(
            "POST", "tempo-timesheets/4/worklogs", None,
            f"несподівана порожня/невалідна відповідь: {worklogs!r}",
        )

    def update_worklog(
        self,
        worklog_id: int,
        worker: str,
        issue_id: int,
        comment: str,
        start: datetime,
        duration: int,
    ) -> dict:
        """Оновити наявний Tempo-worklog (`PUT tempo-timesheets/4/worklogs/{id}`).

        Активує update-flow (D6): коли вже запушений запис змінив контент/час,
        реконсиляція кличе цей метод замість створення дубля. `worklog_id` —
        Tempo `originId` (== `WorklogSyncTask.target_id`). Тіло — те саме, що в
        `create_worklog`. Tempo повертає оновлений worklog (об'єкт або список).
        """
        data = {
            "worker": worker,
            "originTaskId": issue_id,
            "comment": comment,
            "started": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "timeSpentSeconds": duration,
        }

        result = self._make_request(
            f"tempo-timesheets/4/worklogs/{worklog_id}",
            method="PUT",
            data=data,
        )

        if isinstance(result, list):
            return dict(result[0]) if result else {}
        return dict(result) if result else {}

    def _make_request(
        self,
        path: str,
        method: str = "GET",
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        raise_on_error: bool = False,
    ) -> dict:
        if headers is None:
            headers = {}
        headers["Authorization"] = f"Bearer {self._token}"

        if params is None:
            params = {}

        try:
            response = requests.request(
                method=method,
                url=self._url + path,
                params=params,
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Тіло відповіді (де Tempo/Jira пояснює причину, напр. 400) раніше
            # відкидалось. Тепер логуємо його; для write-викликів
            # (`raise_on_error=True`) — кидаємо TempoApiError, щоб причина дійшла
            # до `api_jobs.error`/Журналу, а не маскувалась `KeyError: 0`.
            resp = getattr(e, "response", None)
            body = ""
            status = None
            if resp is not None:
                status = resp.status_code
                try:
                    body = resp.text
                except Exception:
                    body = ""
            logger.error(
                "Jira/Tempo %s %s failed: %s | status=%s body=%s",
                method, path, e, status, body,
            )
            if raise_on_error:
                raise TempoApiError(method, path, status, body) from e
            return {}
