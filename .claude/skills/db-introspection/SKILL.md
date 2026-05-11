---
name: db-introspection
description: Inspect the local PostgreSQL database (db_swc) of Sync Work Calendar — list schemas/tables, get DDL with columns/types/keys/indexes, preview rows. Use the PyCharm MCP as the primary source (live DB) and Alembic migrations + SQLAlchemy models as the offline fallback. Use when the user asks about DB structure, table/column types, constraints, indexes, sample data, or any question that needs ground-truth schema info.
---

# DB Introspection — Sync Work Calendar

Як швидко й точно отримати структуру/дані локальної Postgres БД проекту
(`db_swc`, контейнер `leadsdoit/postgres:17.7`, host-port `11101 → 5432`).

Три джерела, у порядку пріоритету:

1. **Тех-доки в `docs/technical/database/`** — готовий ground-truth-снапшот
   живої БД: повна таблиця колонок/типів/індексів (`schema.md`), Mermaid
   ER-діаграма, потік даних і state-machine (`erd.md`). Найшвидший
   look-up, без виклику IDE. Деталі — §0 нижче.
2. **PyCharm MCP** (`mcp__pycharm__*`) — читає **живу БД** через JetBrains
   DataGrip-конект. Використовуй для верифікації, коли є підозра, що
   тех-доки застаріли, або щоб подивитись прев'ю даних.
3. **Alembic + SQLAlchemy моделі** — офлайн-фолбек, якщо PyCharm не запущений
   або БД не піднята. Показує **намір** (як має бути за міграціями), а не
   фактичний стан.

> Спершу читай тех-доки. MCP — для звірки / preview-даних. Alembic — лише
> офлайн або коли потрібна історія змін.

---

## 0. Тех-доки по БД

Розташування: [docs/technical/database/](../../../docs/technical/database/).

| Файл                                                         | Що всередині                                                                            |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| [`README.md`](../../../docs/technical/database/README.md)    | індекс теки + правило синхронізації                                                     |
| [`schema.md`](../../../docs/technical/database/schema.md)    | повна таблиця колонок (тип, NN, default, нотатки), keys/indices, enum-и, sequences, soft-links, quirks |
| [`erd.md`](../../../docs/technical/database/erd.md)          | Mermaid ER-діаграма, data-flow, state-machine `worklog_sync_status_task_enum`           |

На що покладатись:

- «Які колонки/типи у таблиці X?» — `schema.md` §2-5.
- «Як таблиці зв'язані між собою?» — `erd.md` §1 (ER) або `schema.md` §8 (soft-links).
- «Як заповнюється `worklog_sync_tasks` і куди йде далі?» — `erd.md` §2 (flow).
- «Які значення enum статусу?» — `schema.md` §6 або `erd.md` §3.
- «Що з тех-боргом по БД?» — `schema.md` §9.

Поточний `alembic head`, записаний у `schema.md` — `b4117e0c3dd4` (на 2026-05-11).
Якщо коментар у файлі розходиться з `alembic current` — доки застаріли,
див. §8 «Sync rule».

---

## 1. Готовий контекст підключення

У `.idea/dataSources.xml` сконфігуровано один data source `Sync work`:

- **connectionId**: `a4683dbc-3bc0-4db3-b85b-e4d17a1bb9c6`
- **DBMS**: PostgreSQL
- **JDBC URL**: `jdbc:postgresql://localhost:11101/db_swc`
- **databaseName**: `db_swc`
- **schemaName**: `public` (єдина завантажена схема)

Якщо `connectionId` змінився — спершу виклич
`mcp__pycharm__list_database_connections({ projectPath })` і візьми звідти.

Для всіх викликів передавай `projectPath: "/Users/user/code/4.other/3.sync.work"` —
це знижує неоднозначність вибору MCP-сесії.

---

## 2. Доступні MCP-інструменти

| Tool                                          | Призначення                                       |
| --------------------------------------------- | ------------------------------------------------- |
| `mcp__pycharm__list_database_connections`     | Усі data source-и проекту (id, dbms)              |
| `mcp__pycharm__test_database_connection`      | Перевірка живості коннекта                        |
| `mcp__pycharm__list_database_schemas`         | Схеми у вибраному коннекті                        |
| `mcp__pycharm__list_schema_object_kinds`      | Які kind-и об'єктів підтримує DBMS                |
| `mcp__pycharm__list_schema_objects`           | Об'єкти схеми (table/view/routine/sequence/...) |
| `mcp__pycharm__get_database_object_description` | DDL: колонки, типи, PK/FK, індекси (hierarchical text) |
| `mcp__pycharm__preview_table_data`            | CSV-прев'ю рядків (`maxRowCount`, default 100)    |
| `mcp__pycharm__list_recent_sql_queries`       | Нещодавні/поточні запити коннекта                 |

### Підтримувані object kinds для Postgres

`aggregate`, `collation`, `foreign-table`, `materialized-view`, `object-type`,
`operator`, `operator-class`, `operator-family`, `routine`, `sequence`, `table`,
`view`.

### Поточні таблиці у `public`

`alembic_version`, `jr_issues`, `jr_projects`, `jr_users`, `jr_worklogs`,
`key_templates`, `tc_entries`, `tc_projects`, `worklog_sync_tasks`.

---

## 3. Типові сценарії

### Швидкий one-liner: «опиши таблицю `tc_entries`»

```jsonc
mcp__pycharm__get_database_object_description({
  projectPath: "/Users/user/code/4.other/3.sync.work",
  connectionId: "a4683dbc-3bc0-4db3-b85b-e4d17a1bb9c6",
  databaseName: "db_swc",
  schemaName: "public",
  kind: "table",
  objectName: "tc_entries"
})
```

Повертає колонки з типами, NOT NULL, дефолтами, PK, FK, унікальні та звичайні
індекси у вигляді ієрархічного тексту.

### «Які взагалі таблиці є»

```jsonc
mcp__pycharm__list_schema_objects({
  projectPath, connectionId,
  databaseName: "db_swc",
  schemaName: "public",
  kind: "table"
})
```

Опусти `kind`, щоб отримати все підряд (включно з view, sequence, routine).

### «Покажи дані з `worklog_sync_tasks`»

```jsonc
mcp__pycharm__preview_table_data({
  projectPath, connectionId,
  databaseName: "db_swc",
  schemaName: "public",
  tableName: "worklog_sync_tasks",
  maxRowCount: 50      // default 100, не передавай 0/від'ємне
})
```

CSV у відповіді. Зручно для перевірки фактичних значень (наприклад,
`status`, `target_id`, `meta`).

### Знайти `connectionId` з нуля

```jsonc
mcp__pycharm__list_database_connections({ projectPath })
// → бери id того коннекта, де name == "Sync work"
```

### Перевірити, що БД жива

```jsonc
mcp__pycharm__test_database_connection({ projectPath, id: connectionId })
```

Якщо повертає помилку — БД не запущена. Підняти:

```sh
docker compose up -d db
```

---

## 4. Послідовність дій (workflow)

1. **Знаєш ім'я таблиці** → одразу `get_database_object_description`.
2. **Не знаєш імен** → `list_schema_objects` (опціонально з `kind`).
3. **Потрібні приклади даних** → `preview_table_data` (малий `maxRowCount`).
4. **MCP мовчить чи помиляється** → `test_database_connection`, потім
   або підняти docker-compose, або переходь на Alembic-фолбек (нижче).

Не дублюй виклики: вже отримав опис таблиці — не запитуй повторно у тій самій
розмові, кешуй в контексті.

---

## 5. Alembic / SQLAlchemy фолбек

Коли MCP недоступний, або потрібна історія змін, або робота «по коду».

### Де що лежить

- `alembic.ini` → `script_location = migrations`.
- `migrations/env.py` бере URL із `settings.db.url` і `target_metadata = Base.metadata`.
- `migrations/versions/*.py` — файли ревізій. Іменування:
  `%Y_%m_%d_%H%M-<rev>_<slug>.py`.
- Поточний head (станом на Memory Bank): `b4117e0c3dd4`
  (`update_column_started_at_jr_worklogs`).
- ORM-моделі: `src/models/*.py`, кожна успадковує `Base` із `src/models/base.py`.
  Імена таблиць — `camel_case_to_snake_case(cls.__name__) + "s"`
  (виняток: `TCEntry → tc_entries`).

### Як читати

- **Цілісна поточна схема** → читай моделі в `src/models/` (це і є
  `target_metadata`). Колонки, типи, relationship-и, події SQLAlchemy.
- **Як саме виглядає DDL** → знайди останню ревізію, що чіпає таблицю:

  ```sh
  grep -rln "<table_name>" migrations/versions/
  ```

  Найновіша за датою у назві — найрелевантніша. Старі ревізії можуть бути
  частково перезаписані наступними.

- **Хронологія змін колонки/таблиці** → `grep` по всіх ревізіях і читай у
  порядку дат у назвах файлів. Кожна ревізія має `down_revision`, що утворює
  лінійний ланцюг.

- **Звірити Alembic з фактичною БД** (якщо є підозра на drift):

  ```sh
  alembic current        # яка ревізія застосована до БД
  alembic heads          # яка остання в коді
  alembic history -i     # повний лінійний log
  ```

  Якщо `current ≠ heads` — БД відстає, треба `alembic upgrade head`.

### Обмеження фолбеку

- Моделі та міграції — **намір**. Якщо хтось руками робив `ALTER TABLE` у БД,
  цього тут не побачиш. Для ground-truth все одно потрібен MCP/`psql`.
- Великі рефактори можуть бути розкидані по кільком ревізіям — не обмежуйся
  першим попаданням `grep`.

---

## 6. Коли що обирати — швидка таблиця

| Питання                                    | Краще                          |
| ------------------------------------------ | ------------------------------ |
| «Які колонки і типи у таблиці X?»          | `docs/technical/database/schema.md` (fallback — MCP `get_database_object_description`) |
| «Як таблиці зв'язані?»                     | `docs/technical/database/erd.md` (ER + soft-links) |
| «Який data flow / state-machine?»          | `docs/technical/database/erd.md` |
| «Покажи 20 рядків з таблиці X»             | MCP `preview_table_data`       |
| «Які індекси на X?»                        | `schema.md` або MCP `get_database_object_description` |
| «Які взагалі таблиці є?»                   | `schema.md` §1 або MCP `list_schema_objects` |
| «Як змінювалась колонка Y у часі?»         | Alembic (`migrations/versions/`) |
| «Чи відстає БД від коду?»                  | `alembic current` + `alembic heads` |
| «Як описана модель у ORM (relationship-и, події)?» | `src/models/*.py`     |
| Підозра, що `schema.md` застарів           | MCP — звір живу БД з доком (§8) |
| MCP/PyCharm недоступний                    | `schema.md` + Alembic          |

---

## 7. Обмеження та правила

- **Не запускай DDL/DML** через ці інструменти — MCP-набір тут **тільки на
  читання** (preview, описи, list). Якщо треба змінити схему — створюй
  alembic-ревізію, а не правь БД руками (правило з `AGENTS.md`).
- Не передавай `maxRowCount: 0` чи від'ємне — інструмент відмовить.
- Якщо `selectedOnly: true` повертає порожній список схем — спершу відкрий
  в PyCharm Database tool window і **виділи** потрібну схему (`Tools → Database
  Tools → Manage Shown Schemas`), або виклич із `selectedOnly: false`.
- Чутливих даних у таблицях нема (worklog-и, ключі задач), але токени
  `TC`/`Jira` сидять у `.env` — їх ці інструменти не повертають.

---

## 8. Sync rule — код і доки тримаємо синхронно

Тех-доки в `docs/technical/database/` — це **снапшот**, а не автогенерація.
Якщо вони розійдуться з реальністю, вони стануть джерелом помилок гірше,
ніж їх відсутність. Тому:

**Тригери, коли доки треба оновити в тому самому коміті:**

- Нова/змінена колонка чи таблиця в `src/models/*.py`.
- Нова alembic-ревізія в `migrations/versions/` (особливо `op.add_column`,
  `op.alter_column`, `op.create_table`, `op.create_index`, `op.execute(...)`
  з DDL).
- Новий enum або зміна значень `StatusTaskEnum` (чи інших enum-ів).
- Нова soft-link залежність між таблицями (новий `primaryjoin`,
  новий `_key`-стовпчик, що логічно показує на іншу таблицю).
- Зміна state-machine у `WorllogSyncTask` (нові переходи / стани).
- Новий event-listener, що пише в `meta` чи інші колонки.

**Що саме оновлювати:**

| Зміна                                          | `schema.md` | `erd.md` |
| ---------------------------------------------- | ----------- | -------- |
| Додано/прибрано/перейменовано колонку          | §2–5 (рядок таблиці) | §1 (entity-блок) |
| Додано/прибрано таблицю                        | новий розділ + §8 soft-links | §1 entity + §2 flow |
| Додано/прибрано індекс або UNIQUE              | «Keys / indices» під таблицею | — |
| Новий soft-link                                | §8           | §1 (relationship-стрілка) |
| Нова alembic-ревізія, що змінює DDL            | §5 (alembic head) + §9 (якщо тех-борг) | — |
| Зміна enum                                     | §6           | §3 (state-diagram) |
| Зміна state-machine переходів                  | §6           | §3       |
| Новий data-flow крок (новий зовнішній API)     | (як впливає) | §2 (flow) |

**Послідовність дій:**

1. Зробити зміну в коді/міграції.
2. Прогнати alembic: `alembic upgrade head` локально.
3. Звірити з MCP — `mcp__pycharm__get_database_object_description` по
   зачепленим таблицям. Скопіювати поточний DDL.
4. Оновити `schema.md` і (за потреби) `erd.md`.
5. Якщо змінився alembic head — поновити рядок у вступі `schema.md`.
6. Закомітити доки разом із кодом/міграцією — **одним PR**.

Якщо доки не оновлено, code review мають це впіймати. Розбіжності між
доками і MCP — баг, не «застарілий док».
