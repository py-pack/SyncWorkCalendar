"""Add table jira worklog

Revision ID: 305acbc3994b
Revises: 18ab6105da41
Create Date: 2024-09-21 16:33:19.151775

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "305acbc3994b"
down_revision: Union[str, None] = "18ab6105da41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jr_worklogs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),

        sa.Column("jr_issues_id", sa.Integer(), nullable=False, index=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),

        sa.Column("jr_worker_key", sa.String(), nullable=True, index=True),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False, server_default="0"),

        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("jr_worklogs")
