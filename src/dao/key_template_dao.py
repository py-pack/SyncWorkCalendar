import re

from sqlalchemy import select

from .base_dao import BaseDAO
from src.models import KeyTemplate
from src.core import sync_sessin

from src.utils import convert_str_to_regex


class KeyTemplateDAO(BaseDAO):
    model = KeyTemplate

    def get_templates(self) -> list[dict[str, str | re.Pattern]]:
        with sync_sessin() as db:
            model = db.execute(select(self.model))
            templates = model.scalars().all()

            result = [{
                "key": template.issue_key,
                "template": convert_str_to_regex(template.template),
            } for template in templates]

            return result
