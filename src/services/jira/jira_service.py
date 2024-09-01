from typing import List
import requests

from .dto import JiraProjectDTO


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
