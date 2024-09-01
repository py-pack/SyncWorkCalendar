from typing import List

import requests
from datetime import datetime, time

from src.services.time_camp.dto import TCProjectDTO, TCTaskDTO


class TCRequestService:
    def __init__(self, token: str):
        self._url = 'https://app.timecamp.com/third_party/api/'
        self._token = token

    def get_projects(self) -> List[TCProjectDTO]:
        projects = self._make_request('tasks')
        results = []

        for project_id, project in projects.items():
            results.append(
                TCProjectDTO(
                    id=project.get('task_id'),
                    name=project.get('name'),
                    parent_id=project.get('parent_id'),
                    user_id=project.get('assigned_by'),
                    level=project.get('level'),
                    color=project.get('color'),
                    add_date_at=project.get('add_date'),
                    modify_at=project.get('modify_time'),
                ))

        return results

    def get_entries(self, from_date: datetime | None = None, to_date: datetime | None = None) -> List[TCTaskDTO]:
        params = {}
        if from_date is not None:
            params['from'] = datetime.combine(from_date.date(), time.min).strftime('%Y-%m-%d %H:%M:%S')
        if to_date is not None:
            params['to'] = datetime.combine(to_date.date(), time.max).strftime('%Y-%m-%d %H:%M:%S')

        entries = self._make_request('entries', params=params)
        results = []

        for entry in entries:
            date_entry = entry.get("date", None)
            if date_entry is None:
                continue

            resultDTO = TCTaskDTO(
                id=entry.get("id"),
                tc_project_id=entry.get("task_id"),
                description=entry.get("description"),
                start_at=f"{date_entry} {entry['start_time']}",
                end_at=f"{date_entry} {entry['end_time']}",
                modify_at=entry.get("last_modify"),
            )

            results.append(resultDTO)

        return results

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
        params['format'] = 'json'

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
