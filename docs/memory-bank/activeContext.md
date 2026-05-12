# Active Context

## Дата оновлення

2026-05-11 — Memory Bank ініціалізовано на основі поточного стану `main`.

## Поточний фокус

**Активна OpenSpec-зміна:** [`add-rest-api`](../../openspec/changes/add-rest-api/)
— REST API на FastAPI поверх існуючих тасків. Стан: артефакти готові
(`proposal.md`, `design.md`, `specs/{api-auth,api-sync-status,api-sync-triggers,api-tc-projects-management}/spec.md`,
`tasks.md`), валідовано через `openspec validate add-rest-api`. Готово до
imple­ment-фази через `/openspec-apply-change`.

Скоп зміни — single-user JWT auth, read-endpoint-и стану синхронізації,
REST-обгортки навколо `TimeCampUpdateTask` / `UpdateJiraTask` /
`WorllogSyncTask` і PATCH для `tc_projects.is_sync` / `issue_key`.

Поряд лежить незакомічена правка `main.ipynb` (період запуску
`2026-04-08 .. 2026-04-13`), яка відображає експлуатаційний запуск, не
нову розробку.

## Як це вписується в roadmap

`add-rest-api` — етап 1 траєкторії, описаної в
[`projectbrief.md`](projectbrief.md). Майбутні етапи (автоматичний
планувальник, власний трекер замість TimeCamp, multi-user масштаб) на
поточний скоуп змін не впливають, але мотивують multi-user-ready вибори
в `decisinLog.md` → D-009.

## Нещодавні зміни (за git log)

- `bbb67bd` — оновлення залежностей та адаптація тасків.
- `6cc9094` — фікс типу колонки `created_at` для `jr_worklogs` (DateTime).
- `e94bed8` — реалізація створення worklog-ів у `Jira` через `Tempo`.
- `0384620` — додано стадію `before_create` для `WorllogSyncTask`.
- `eda6333` — основний сервіс `create_task_for_sync` + рефакторинг таблиць.

Ці зміни вже відображені в коді й моделях — окремих міграцій для них додавати
не потрібно (остання міграція — `b4117e0c3dd4`, 2024-10-02).

## Активні відкриті питання

- **HTTP-шар у роботі.** Рішення прийнято через OpenSpec `add-rest-api`
  (див. `openspec/changes/add-rest-api/design.md`). Імплементація ще не
  стартувала — `src/api/` порожній.
- **Сценарій оновлення worklog-ів.** Статуси `pre_update/update/updated` в
  `StatusTaskEnum` зарезервовані, але не використовуються. Потрібно вирішити,
  коли і за яким триггером оновлювати раніше синхронізовані записи.
- **Назва `worllog_sync_task.py`.** Файл і клас містять одрук (`worllog` замість
  `worklog`). Перейменування зачепить імпорти — поки не виправлено.

## Найближчі кроки (як орієнтир для агентів)

1. Перед будь-якою правкою — прочитати всі файли в `docs/memory-bank/`.
2. Для нових міграцій — `alembic revision --autogenerate` після правки моделей
   (див. `techContext.md`).
3. Якщо змінюється логіка `BaseDAO._sync` — пам'ятати, що вона **видаляє**
   моделі, відсутні у DTO-списку (див. `systemPatterns.md`).

## Що ще не покрите Memory Bank

- Немає документації для веб-інтерфейсу/API (бо їх і не існує).
- Тестове покриття відсутнє; рішення про фреймворк тестів не прийняте.
