import requests

from typing import List, Any
from .dto import JiraUserDTO, JiraIssueDTO, JiraProjectDTO, JiraWorklogDTO
from datetime import datetime, date


class JiraService:
    def __init__(self, token: str):
        self._url = 'https://leadsdoit.io/jira/rest/'
        self._token = token

    def get_projects(self) -> List[JiraProjectDTO]:
        projects = self._make_request('api/2/project')
        results = [JiraProjectDTO(
            id=project.get('id'),
            key=project.get('key'),
            name=project.get('name'),
            is_archved=project.get('archived'),
        ) for project in projects]
        return results

    def search_issues(self, keys: List[str]) -> List[JiraIssueDTO]:
        jql_keys = 'key in ({})'.format(','.join(keys))
        data = {
            'jql': jql_keys
        }
        search_request: dict[str, Any] = self._make_request('api/2/search', method='POST', data=data)

        issues: list[dict[str, Any]] = search_request.get('issues')
        if issues is None:
            return []

        results = []
        for issue in issues:
            fields: dict | None = issue.get('fields')
            if fields is None:
                continue

            project = None
            project_field: dict = fields.get('project')
            if project_field is not None:
                project = JiraProjectDTO(
                    id=project_field.get('id'),
                    key=project_field.get('key'),
                    name=project_field.get('name'),
                )

            creator = None
            creator_field: dict = fields.get('creator')
            if project_field is not None:
                creator = JiraUserDTO(
                    key=creator_field.get('key'),
                    name=creator_field.get('name'),
                    full_name=creator_field.get('displayName'),
                    email=creator_field.get('emailAddress'),
                )

            reporter = None
            reporter_field: dict = fields.get('reporter')
            if project_field is not None:
                reporter = JiraUserDTO(
                    key=reporter_field.get('key'),
                    name=reporter_field.get('name'),
                    full_name=reporter_field.get('displayName'),
                    email=reporter_field.get('emailAddress'),
                )

            issue_dto = JiraIssueDTO(
                id=issue.get('id'),

                key=issue.get('key'),
                name=fields.get('summary'),

                jr_project_id=project.id if project is not None else None,

                epic_key=fields.get('customfield_10005', None),
                parent_key=fields.get('parent', {}).get('key', None),

                type=fields.get('issuetype', {}).get('name', 'Task'),
                priority=fields.get('priority', {}).get('name', 'Medium'),
                status=fields.get('status', {}).get('name', 'To DO'),

                jr_creator_key=creator.key if creator is not None else None,
                jr_reporter_key=reporter.key if reporter is not None else None,

                estimate_plan=fields.get('timeoriginalestimate', 0),
                estimate_fact=fields.get('aggregateprogress', {}).get('progress', 0),
                estimate_rest=fields.get('aggregatetimeestimate', 0),

                created_at=fields.get('created'),
                updated_at=fields.get('updated'),

                project=project,
                creator=creator,
                reporter=reporter,
            )

            results.append(issue_dto)

        return results

    def serch_worklogs_by_user(self, start: datetime, finish: datetime, user_key: str) -> List[JiraWorklogDTO]:
        data = {
            "from": start.strftime('%Y-%m-%d'),
            "to": finish.strftime('%Y-%m-%d'),
            "worker": [user_key]
        }

        worklogs = self._make_request(
            'tempo-timesheets/4/worklogs/search',
            method='POST',
            data=data
        )

        result = [JiraWorklogDTO(
            id=worklog.get("originId"),
            jr_issues_id=worklog.get("originTaskId"),
            jr_issues_key=worklog.get("issue", {}).get('key'),
            description=worklog.get("comment"),
            jr_worker_key=worklog.get("worker"),
            started_at=worklog.get("started"),
            duration=worklog.get("timeSpentSeconds"),
            created_at=worklog.get("dateCreated"),
            updated_at=worklog.get("dateUpdated"),
        ) for worklog in worklogs]

        return result

    def create_worklog(self, worker: str, issue_id: int, comment: str, start: datetime, duration: int) -> dict:
        data = {
            "worker": worker,
            "originTaskId": issue_id,
            "comment": comment,
            "started": start.strftime('%Y-%m-%dT%H:%M:%S.000'),
            "timeSpentSeconds": duration,
        }

        worklogs = self._make_request(
            'tempo-timesheets/4/worklogs',
            method='POST',
            data=data
        )

        return dict(worklogs[0])

    def _make_request(
        self,
        path: str,
        method: str = 'GET',
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None
    ) -> dict:
        if headers is None:
            headers = {}
        headers['Authorization'] = f'Bearer {self._token}'

        if params is None:
            params = {}

        try:
            response = requests.request(
                method=method,
                url=self._url + path,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {}
