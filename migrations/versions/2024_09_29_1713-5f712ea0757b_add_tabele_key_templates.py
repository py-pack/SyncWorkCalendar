"""add tabele key templates

Revision ID: 5f712ea0757b
Revises: 6a1b0bf819e8
Create Date: 2024-09-29 17:13:24.626729

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5f712ea0757b"
down_revision: Union[str, None] = "6a1b0bf819e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "key_templates",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("template", sa.String(), nullable=False),
        sa.Column("issue_key", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("key_templates")
