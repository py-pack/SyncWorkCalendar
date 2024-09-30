import re
import time
from src.dao import JRProjectDAO, KeyTemplateDAO


class SyncTaskService:
    cache_timestamp = None
    cache_ttl = 60 * 60 * 2

    project_key: list = None
    project_templates: list[dict[str, str | re.Pattern]] = None

    project_task_pattern = re.compile(r'(?P<project_key>[A-Za-z]{2,8})-(?P<task_num>\d{1,4})')

    @classmethod
    def match_task(cls, description: str) -> None | str:
        cls._init_cache()

        projecct_task_match = cls.project_task_pattern.search(description)
        if projecct_task_match:
            project_key = projecct_task_match.group('project_key')
            task_num = projecct_task_match.group('task_num')

            if project_key in cls.project_key:
                return f"{project_key}-{task_num}"

        for template in cls.project_templates:
            if template["template"].search(description):
                return template["key"]

        return None

    @classmethod
    def _init_cache(cls):
        if cls.project_key is None or cls._check_cach():
            cls.project_key = JRProjectDAO.all_keys_sync()

        if cls.project_templates is None or cls._check_cach():
            key_dao = KeyTemplateDAO()
            cls.project_templates = key_dao.get_templates()

    @classmethod
    def _check_cach(cls) -> bool:
        return cls.cache_timestamp is None or (time.time() - cls.cache_timestamp > cls.cache_ttl)
