"""Createt TCProject

Revision ID: a8cf9e93c99e
Revises:
Create Date: 2024-08-23 18:49:46.538136

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import false

revision: str = "a8cf9e93c99e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tc_projects",
        sa.Column("id", sa.Integer(), nullable=False),

        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),

        sa.Column("level", sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=false()),
        sa.Column("is_sync", sa.Boolean(), nullable=False, server_default=false()),

        sa.Column("issue_key", sa.String(), nullable=True),
        sa.Column("color", sa.String(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint("id", name=op.f("pk_tc_projects")),
        sa.UniqueConstraint("name", name=op.f("uq_tc_projects_name")),
    )


def downgrade() -> None:
    op.drop_table("tc_projects")
