"""Add table worklog sync task

Revision ID: 6a1b0bf819e8
Revises: 305acbc3994b
Create Date: 2024-09-29 15:07:35.517435

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6a1b0bf819e8"
down_revision: Union[str, None] = "305acbc3994b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worklog_sync_tasks",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),

        sa.Column(
            "status",
            sa.Enum(
                "pre_create", "create", "created",
                "pre_update", "update", "updated", "sync",
                name="worklog_sync_status_task_enum",
            ),
            nullable=False,
        ),
        sa.Column("source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("target_id", sa.Integer(), nullable=True, index=True),

        sa.Column("worker_key", sa.String(), nullable=False),
        sa.Column("issue_key", sa.String(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=True, index=True),

        sa.Column("content", sa.String(), nullable=True),
        sa.Column("started_at", sa.Date(), nullable=False),

        sa.Column("time_spent", sa.Integer(), nullable=False),

        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("worklog_sync_tasks")
    sa.Enum(name="worklog_sync_status_task_enum").drop(op.get_bind())
