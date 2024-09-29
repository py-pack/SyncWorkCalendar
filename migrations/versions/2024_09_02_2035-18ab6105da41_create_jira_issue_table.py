"""Create jira issue table

Revision ID: 18ab6105da41
Revises: b06c330985ba
Create Date: 2024-09-02 20:35:30.674677

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "18ab6105da41"
down_revision: Union[str, None] = "b06c330985ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jr_issues",

        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),

        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),

        sa.Column("jr_project_id", sa.Integer(), nullable=False, index=True),

        sa.Column("epic_key", sa.String(), nullable=True, index=True),
        sa.Column("parent_key", sa.String(), nullable=True, index=True),

        sa.Column("type", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),

        sa.Column("jr_creator_key", sa.String(), nullable=True, index=True),
        sa.Column("jr_reporter_key", sa.String(), nullable=True, index=True),

        sa.Column("estimate_plan", sa.Integer(), nullable=False, default=0),
        sa.Column("estimate_fact", sa.Integer(), nullable=False, default=0),
        sa.Column("estimate_rest", sa.Integer(), nullable=False, default=0),

        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("jr_issues")
