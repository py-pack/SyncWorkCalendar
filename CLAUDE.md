# CLAUDE.md

## Memory Bank

На початку **кожної задачі** прочитай усі Markdown-файли в
`docs/memory-bank/` перед тим, як вносити будь-які зміни. Це канонічне джерело
загального контексту цього репозиторію (огляд, архітектура, технічний стек,
поточний фокус, рішення, прогрес).

Файли:
- `docs/memory-bank/projectbrief.md`
- `docs/memory-bank/productContext.md`
- `docs/memory-bank/activeContext.md`
- `docs/memory-bank/systemPatterns.md`
- `docs/memory-bank/techContext.md`
- `docs/memory-bank/progress.md`
- `docs/memory-bank/decisinLog.md`

Для ініціалізації, оновлення або аудиту Memory Bank використовуй скіл
`memory-bank-manager`. Уся загальна інформація про проект має жити в
Memory Bank — не дублюй її в `CLAUDE.md`, `AGENTS.md` чи інших файлах
інструкцій. Сюди додавай лише операційні нюанси, специфічні для роботи Claude
Code, які не належать Memory Bank.

## Розкладка монорепо (роутинг)

Репозиторій розділено на дві частини зі своїми інструкціями:

- **`api/`** — Python-бекенд (FastAPI, SQLAlchemy, Alembic, CLI; пакет `app`).
  Працюєш у бекенді — читай [`api/CLAUDE.md`](api/CLAUDE.md) і
  [`api/AGENTS.md`](api/AGENTS.md).
- **`front/`** — веб-фронтенд (Vue 3 + Vite + TypeScript). Працюєш у фронті —
  читай [`front/CLAUDE.md`](front/CLAUDE.md) і
  [`front/AGENTS.md`](front/AGENTS.md).

На корені лишаються **спільні** для всього монорепо речі: `docs/memory-bank/`,
`docs/technical/`, `openspec/`, Docker (`docker-compose.yml`, per-folder
`Dockerfile`), кореневий `Makefile`.

## Скіли

Загальні (project-wide) скіли — глобальні, спільні на корені (`.claude/`).
Per-folder орієнтири живуть як **легкі вказівники** у `api/CLAUDE.md`/`AGENTS.md`
та `front/CLAUDE.md`/`AGENTS.md` (без окремих `.claude/skills/` усередині
підтек). Це свідома зміна попередньої конвенції — деталі в
`docs/memory-bank/decisinLog.md`.

## OpenSpec

Проект під OpenSpec — структура в `openspec/` (`changes/` + `specs/`).
Активні зміни — `openspec list`, специфікації — `openspec list --specs`.
Скіли — глобальні (`openspec-explore`, `openspec-propose`,
`openspec-apply-change`, `openspec-archive-change`); локальних копій не
тримаємо.

Перед стартом нетривіальної фічі — пропонувати через `/openspec-propose`,
розкручувати ідею через `/openspec-explore`, виконувати через
`/openspec-apply-change`, завершувати через `/openspec-archive-change`.
Memory Bank синкається автоматично (`activeContext.md`, `progress.md`).
