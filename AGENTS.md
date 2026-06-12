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

## Робочі правила

- Перед правкою моделей чи DAO — звір зі стейт-машиною `WorklogSyncTask`
  у `systemPatterns.md` та з рішеннями `D-005`, `D-006` у `decisinLog.md`.
- Будь-яка зміна `src/models/*` має супроводжуватись alembic-ревізією:
  `alembic revision --autogenerate -m "<slug>"`. Не редагуй старі ревізії.
- Не запускай `BaseDAO.sync_all` для часткових даних worklog/entry — це full
  replace. Користуйся `sync_all_between` або `update_by_keys`.
- При додаванні нового `JRProject` ключа не покладайся на `SyncTaskService`
  кеш — TTL 2 год (`D-003`).

## OpenSpec

Проект під OpenSpec. Структура — `openspec/changes/` + `openspec/specs/`.
Робочий цикл:

- `/openspec-explore` — продумати ідею до пропозиції.
- `/openspec-propose <name>` — створити `proposal.md` + `design.md` + `tasks.md`
  у `openspec/changes/<name>/`.
- `/openspec-apply-change` — виконати таски.
- `/openspec-archive-change` — закрити і перенести у `openspec/changes/archive/`.

Скіли глобальні; локальних копій у `.claude/skills/` чи `.agents/skills/`
не створюємо.

## Запуск

Деталі команд (uv, Alembic, Docker) — у `techContext.md`.
