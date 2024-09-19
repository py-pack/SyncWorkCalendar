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

        sa.Column("id", sa.Integer(), nullable=False),

        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),

        sa.Column("jr_project_id", sa.Integer(), nullable=False),

        sa.Column("epic_key", sa.String(), nullable=True),
        sa.Column("parent_key", sa.String(), nullable=True),

        sa.Column("type", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),

        sa.Column("jr_creator_key", sa.String(), nullable=True),
        sa.Column("jr_reporter_key", sa.String(), nullable=True),

        sa.Column("estimate_plan", sa.Integer(), nullable=False, default=0),
        sa.Column("estimate_fact", sa.Integer(), nullable=False, default=0),
        sa.Column("estimate_rest", sa.Integer(), nullable=False, default=0),

        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),

        sa.PrimaryKeyConstraint("id", name=op.f("pk_jr_issues")),
        sa.UniqueConstraint("key", name=op.f("uq_jr_issues_key")),
    )

    op.create_index(
        op.f("ix_jr_issues_epic_key"),
        "jr_issues",
        ["epic_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jr_issues_parent_key"),
        "jr_issues",
        ["parent_key"],
        unique=False,
    )

    op.create_index(
        op.f("ix_jr_issues_jr_project_id"),
        "jr_issues",
        ["jr_project_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_jr_issues_jr_creator_key"),
        "jr_issues",
        ["jr_creator_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jr_issues_jr_reporter_key"),
        "jr_issues",
        ["jr_reporter_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_jr_issues_jr_reporter_key"), table_name="jr_issues")
    op.drop_index(op.f("ix_jr_issues_jr_creator_key"), table_name="jr_issues")
    op.drop_index(op.f("ix_jr_issues_jr_project_id"), table_name="jr_issues")
    op.drop_index(op.f("ix_jr_issues_parent_key"), table_name="jr_issues")
    op.drop_index(op.f("ix_jr_issues_epic_key"), table_name="jr_issues")

    op.drop_table("jr_issues")
