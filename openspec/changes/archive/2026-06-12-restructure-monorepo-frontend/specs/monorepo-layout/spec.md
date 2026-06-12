## ADDED Requirements

### Requirement: Бекенд живе у `api/` як пакет `app`

Увесь Python-бекенд SHALL розташовуватись у теці `api/`, а імпортований
пакет SHALL називатися `app` (а не `src`). Точки входу, міграції та
менеджмент залежностей SHALL також лежати у `api/`. `Makefile` SHALL
лишатися на корені як точка оркестрації монорепо.

#### Scenario: Пакет імпортується під новим іменем

- **WHEN** із кореня `api/` виконується `uv run python -c "from app.api.app import app"`
- **THEN** імпорт завершується без помилок, а пакета `src` у проекті немає

#### Scenario: Точки входу та інфра-файли переїхали

- **WHEN** перевіряється структура `api/`
- **THEN** там присутні `app/`, `migrations/`, `alembic.ini`,
  `pyproject.toml`, `uv.lock`, `.python-version`, `run_api.py` і `main.py`
- **AND** на корені репозиторію цих файлів більше немає
- **AND** `Makefile` лишається на корені (не переїхав)

#### Scenario: Жодного залишкового `src.`-імпорту

- **WHEN** виконується пошук `grep -rn "src\." api --include='*.py'`
- **THEN** збігів немає (усі ~90 імпортів переписані на `app.*`)

### Requirement: Спільні матеріали лишаються на корені

Канонічний project-wide контекст SHALL лишатися на корені репозиторію і не
дублюватися в підтеках. До нього належать `docs/memory-bank/`, `openspec/`,
`docs/technical/` та загальні скіли в `.claude/`.

#### Scenario: Memory Bank і OpenSpec не переїжджають

- **WHEN** перевіряється корінь репозиторію після зміни
- **THEN** `docs/memory-bank/`, `docs/technical/` та `openspec/` лишаються на
  корені, без копій усередині `api/` чи `front/`

#### Scenario: Посилання в Memory Bank лишаються валідними

- **WHEN** із кореня перевіряються відносні посилання у файлах
  `docs/memory-bank/*.md` на `docs/technical/*` та `openspec/*`
- **THEN** усі шляхи існують і ведуть на наявні файли

### Requirement: CLI запускається під новим пакетом

Argparse-CLI SHALL запускатися як `python -m app.cli`; стара форма
`python -m src.cli` SHALL припинити існування.

#### Scenario: CLI відповідає під новим іменем

- **WHEN** із `api/` виконується `uv run python -m app.cli --help`
- **THEN** виводиться довідка CLI без помилок імпорту

### Requirement: Доменна логіка та схема БД незмінні

Переїзд SHALL бути суто структурним: SQLAlchemy-моделі, DAO, сервіси, таски
та схема БД (включно з alembic head) SHALL лишитися без змістовних змін.

#### Scenario: Alembic head не змінився

- **WHEN** після переїзду виконується `uv run alembic heads` із `api/`
- **THEN** head лишається `ef2c7288bbb0` (`add_api_layer_tables`)
- **AND** нових ревізій для самого переїзду не створено
