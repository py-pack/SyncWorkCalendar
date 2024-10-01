"""Add Jira Project

Revision ID: c40c9aa08896
Revises: 82f082ce0b72
Create Date: 2024-09-01 20:31:04.191607

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c40c9aa08896"
down_revision: Union[str, None] = "5f712ea0757b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jr_projects",

        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),

        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),

        sa.Column("is_archved", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_watched", sa.Boolean(), nullable=False, default=True),
    )


def downgrade() -> None:
    op.drop_table("jr_projects")
