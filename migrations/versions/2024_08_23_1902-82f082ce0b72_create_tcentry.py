"""Create TcEntry

Revision ID: 82f082ce0b72
Revises: a8cf9e93c99e
Create Date: 2024-08-23 19:02:22.019220

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "82f082ce0b72"
down_revision: Union[str, None] = "a8cf9e93c99e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tc_entries",
        sa.Column("id", sa.Integer(), nullable=False),

        sa.Column("tc_project_id", sa.Integer(), nullable=True),

        sa.Column("description", sa.String(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),

        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column(
            "duration",
            sa.Integer(),
            sa.Computed(
                "EXTRACT(EPOCH FROM end_at - start_at)",
            ),
            nullable=False,
        ),

        sa.Column("modify_at", sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint("id", name=op.f("pk_tc_entries")),
    )


def downgrade() -> None:
    op.drop_table("tc_entries")
