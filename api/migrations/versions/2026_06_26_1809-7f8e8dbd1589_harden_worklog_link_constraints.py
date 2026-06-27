"""harden_worklog_link_constraints

Зміцнює явний місток TimeCamp↔Tempo у `worklog_sync_tasks`:
1. data-fix (до констрейнтів): дедуп WST за `source_id` (лишити один) +
   занулення дангл-`target_id`;
2. унікальний індекс на `source_id` (один WST на TimeCamp-запис);
3. FK `target_id → jr_worklogs.id` з `ON DELETE SET NULL`.

На `source_id` FK НЕ накладається (D3): історію WST не чіпаємо каскадом при
зникненні TimeCamp-запису. Осиротілі за `source_id` WST лишаються.

Revision ID: 7f8e8dbd1589
Revises: 69dde0d17ff2
Create Date: 2026-06-26 18:09:11.226097

"""

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f8e8dbd1589"
down_revision: Union[str, None] = "69dde0d17ff2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


log = logging.getLogger("alembic.runtime.migration")

# Пріоритет «найбільш просунутого» статусу при дедупі за source_id:
# рядок із реальним worklog-ом (created/updated) і завершенішим станом
# переважає над початковими (pre_create/create). Тай-брейк — менший id.
_STATUS_RANK_SQL = """
    CASE status::text
        WHEN 'updated' THEN 6
        WHEN 'update' THEN 5
        WHEN 'pre_update' THEN 4
        WHEN 'created' THEN 3
        WHEN 'create' THEN 2
        WHEN 'pre_create' THEN 1
        WHEN 'sync' THEN 0
        ELSE 0
    END
"""


def upgrade() -> None:
    bind = op.get_bind()

    # --- 1. Data-fix (ДО констрейнтів) -------------------------------------
    # (а) Дедуп WST за source_id: лишаємо один (із target_id і найпросунутішим
    #     статусом), решту видаляємо. Це ЄДИНЕ видалення WST у міграції —
    #     чистимо саме некоректну, задвоєну історію (D5). Осиротілі за
    #     source_id (без tc_entries) НЕ чіпаємо — FK на source_id немає.
    dedup_result = bind.execute(
        sa.text(
            f"""
            DELETE FROM worklog_sync_tasks
            WHERE id IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY source_id
                               ORDER BY (target_id IS NULL) ASC,
                                        {_STATUS_RANK_SQL} DESC,
                                        id ASC
                           ) AS rn
                    FROM worklog_sync_tasks
                ) ranked
                WHERE rn > 1
            )
            """
        )
    )
    log.info(
        "harden-worklog-link: видалено задвоєних WST за source_id: %s",
        dedup_result.rowcount,
    )

    # (б) Занулити дангл-target_id (вказує на неіснуючий jr_worklogs.id) —
    #     інакше FK target_id не накладеться.
    dangling_result = bind.execute(
        sa.text(
            """
            UPDATE worklog_sync_tasks
            SET target_id = NULL
            WHERE target_id IS NOT NULL
              AND target_id NOT IN (SELECT id FROM jr_worklogs)
            """
        )
    )
    log.info(
        "harden-worklog-link: занулено дангл-target_id: %s",
        dangling_result.rowcount,
    )

    # --- 2. Унікальний індекс на source_id ---------------------------------
    # Наявний індекс ix_worklog_sync_tasks_source_id був НЕ унікальним —
    # пересоздаємо як UNIQUE (один WST на TimeCamp-запис, D1).
    op.drop_index(
        "ix_worklog_sync_tasks_source_id", table_name="worklog_sync_tasks"
    )
    op.create_index(
        "ix_worklog_sync_tasks_source_id",
        "worklog_sync_tasks",
        ["source_id"],
        unique=True,
    )

    # --- 3. FK target_id → jr_worklogs (SET NULL) --------------------------
    # FK НА source_id НЕ накладаємо (D3 — історію не чіпаємо каскадом).
    op.create_foreign_key(
        "fk_worklog_sync_tasks_target_id_jr_worklogs",
        "worklog_sync_tasks",
        "jr_worklogs",
        ["target_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Знімаємо констрейнти у зворотному порядку. Data-fix не відновлюється —
    # це чистка саме некоректних (задвоєних) рядків.
    op.drop_constraint(
        "fk_worklog_sync_tasks_target_id_jr_worklogs",
        "worklog_sync_tasks",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_worklog_sync_tasks_source_id", table_name="worklog_sync_tasks"
    )
    op.create_index(
        "ix_worklog_sync_tasks_source_id",
        "worklog_sync_tasks",
        ["source_id"],
        unique=False,
    )
