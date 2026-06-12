# AGENTS.md — Sync Work Calendar

## Memory Bank (обов'язково)

На початку **кожної** задачі прочитай усі Markdown-файли в
`docs/memory-bank/`. Це канонічне джерело загального контексту проекту:

- `projectbrief.md` — призначення, зовнішні системи, межі функціоналу.
- `productContext.md` — користувацький сценарій і UX-обмеження.
- `activeContext.md` — поточний фокус, відкриті питання, найближчі кроки.
- `systemPatterns.md` — архітектура, шари, state-machine, DAO-патерни.
- `techContext.md` — стек, конфіги, команди, БД, міграції.
- `progress.md` — що працює / не реалізовано / тех-борги.
- `decisinLog.md` — журнал ключових рішень із причинами.

Для робіт із Memory Bank (ініціалізація, апдейт, аудит) використовуй скіл
`memory-bank-manager`. Не дублюй у `AGENTS.md` той загальний контекст, який
вже описаний у Memory Bank — додавай посилання.

## Розкладка монорепо (роутинг)

- **`api/`** — Python-бекенд (FastAPI/SQLAlchemy/Alembic/CLI, пакет `app`).
  Робочі правила бекенду — у [`api/AGENTS.md`](api/AGENTS.md).
- **`front/`** — веб-фронтенд (Vue 3 + Vite + TypeScript). Робочі правила
  фронту — у [`front/AGENTS.md`](front/AGENTS.md).

Спільне на корені: `docs/memory-bank/`, `docs/technical/`, `openspec/`,
Docker (`docker-compose.yml`, per-folder `Dockerfile`), кореневий `Makefile`.

## Скіли

Загальні скіли — глобальні, спільні на корені. Per-folder орієнтири — це
**легкі вказівники** в `api/AGENTS.md`/`CLAUDE.md` та
`front/AGENTS.md`/`CLAUDE.md`; окремих `.claude/skills/` у підтеках не тримаємо.
(Раніше діяло правило «жодних локальних скілів» — переглянуто, див.
`decisinLog.md`.)

## OpenSpec

Проект під OpenSpec. Структура — `openspec/changes/` + `openspec/specs/`.
Робочий цикл:

- `/openspec-explore` — продумати ідею до пропозиції.
- `/openspec-propose <name>` — створити `proposal.md` + `design.md` + `tasks.md`
  у `openspec/changes/<name>/`.
- `/openspec-apply-change` — виконати таски.
- `/openspec-archive-change` — закрити і перенести у `openspec/changes/archive/`.

## Запуск

Деталі команд (uv, Alembic, Docker, Vite) — у `techContext.md`. Кореневий
`Makefile` тримає шорткати для обох частин (`make serve`, `make front-dev`
тощо).
