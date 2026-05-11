# Database — Tech Docs

Документація по локальній Postgres БД `db_swc`. Усе тут — снапшоти живої
БД, отримані через PyCharm DataGrip MCP. Не редагувати без звірки з MCP.

## Файли

- **[schema.md](schema.md)** — повний ground-truth довідник: таблиці,
  колонки, типи, ключі, індекси, enum-и, sequences, soft-links, quirks.
- **[erd.md](erd.md)** — Mermaid-діаграми: ER, потік даних, state-machine
  `worklog_sync_status_task_enum`.

## Як інтроспектувати БД наживо

Скіл `db-introspection` (`.claude/skills/db-introspection/SKILL.md`,
дзеркало `.agents/skills/db-introspection/SKILL.md`) містить готові виклики
MCP-інструментів JetBrains для отримання DDL, прев'ю даних і списків
об'єктів.

## Правило синхронізації

Якщо змінюєш:

- модель у `src/models/*.py`,
- alembic-ревізію у `migrations/versions/`,
- DAO-поведінку, що впливає на зв'язки між таблицями,
- enum-значення в коді або в БД,

— оновлюй **обидва файли** в цій теці тією ж комітом, плюс рядок
`alembic head` у вступі `schema.md`.

Деталі — секція «Sync rule» у `SKILL.md` скіла `db-introspection`.
