"""Create Jira User

Revision ID: b06c330985ba
Revises: c40c9aa08896
Create Date: 2024-09-02 18:57:34.874611

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b06c330985ba"
down_revision: Union[str, None] = "c40c9aa08896"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jr_users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),

        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("jr_users")
