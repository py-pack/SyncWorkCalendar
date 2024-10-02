"""update column started_at jr_worklogs

Revision ID: b4117e0c3dd4
Revises: 6a1b0bf819e8
Create Date: 2024-10-02 22:17:37.421471

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4117e0c3dd4"
down_revision: Union[str, None] = "6a1b0bf819e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "jr_worklogs",
        "started_at",
        existing_type=sa.DATE(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    pass
