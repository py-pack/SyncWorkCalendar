# Project Brief — Sync Work Calendar

## Призначення

**Sync Work Calendar** — внутрішня утиліта для синхронізації відпрацьованого
часу. Вона забирає таймер-записи з `TimeCamp`, зіставляє їх із задачами `Jira`
і автоматично створює `worklog` у `Tempo Timesheets` (плагін до `Jira`).
Мета — прибрати ручне переписування часу між системами.

## Зовнішні системи

- **TimeCamp** — джерело таймер-записів (entries). API: `https://app.timecamp.com/third_party/api/`.
- **Jira (on-prem)** — джерело задач та проектів. API: `https://leadsdoit.io/jira/rest/api/2/`.
- **Tempo Timesheets** — плагін у `Jira`, через який створюються worklog-и.
  API: `https://leadsdoit.io/jira/rest/tempo-timesheets/4/`.

## Ключові операції

1. Завантаження проектів і таймер-записів `TimeCamp` у локальну БД.
2. Завантаження проектів, задач і worklog-ів `Jira` у локальну БД.
3. Парсинг `description` entry → визначення `issue_key` через шаблони (`KeyTemplate`).
4. Створення `WorklogSyncTask` для синхронізації entries → Tempo worklog-и.
5. Викликання `Tempo` API для створення worklog-ів та зберігання `target_id`.

## Користувач

Поточний робочий процес — один користувач (працівник), його `key` у `Jira`
зберігається в змінній оточення `APP__CURRENT_USER`. Маршрути `FastAPI` та
веб-інтерфейс наразі **не реалізовані** — запуск відбувається з `main.py` або
через ноутбук `main.ipynb`.

## Сучасний стан (Memory Bank ініціалізовано 2026-05-11)

- Логіка синхронізації працює end-to-end через `WorllogSyncTask` (typo у назві файлу/класу збережено).
- Поточна гілка: `main`. Стейджинг — `M main.ipynb` (зміна періоду запуску).
- HTTP-сервер `FastAPI` оголошений у залежностях, але не піднятий.

Деталі архітектури — у `systemPatterns.md`, технічні рамки — у `techContext.md`,
поточний фокус — у `activeContext.md`.

## Roadmap (довгостроковий vision)

Траєкторія проекту, від найближчого до найдальшого:

1. **REST API над існуючими тасками (поточний етап).** Single-user JWT,
   read-endpoints стану синхронізації, ручні sync-trigger-и, журнал
   `api_jobs` із проміжним кроком `needs_verification`. Активна зміна —
   [`add-rest-api`](../../openspec/changes/add-rest-api/). Поточний
   скоуп — в `activeContext.md`.
2. **Сервіс автоматичної періодичної синхронізації.** Той самий рушій
   синку, але запускається з розкладу без ручного `POST /sync/**`.
   Конкретний планувальник (cron, APScheduler, окремий worker) ще не
   обрано — рішення зафіксуємо окремою зміною, коли підійдемо.
3. **Власний трекер часу замість TimeCamp.** Замінити зовнішній `TimeCamp`
   на внутрішнє рішення для введення часу і зберегти синхронізацію з
   `Jira` через `Tempo Timesheets`. Pipeline `worklog_sync_tasks`
   (`pre_create → create → created`) переюзаємо.
4. **Multi-user масштаб (4–100 користувачів).** Декілька працівників,
   кожен зі своїм `worker_key` (`Jira key`) і власним джерелом entries.
   Архітектурні зачіпки під це закладаємо вже на етапі 1 (див.
   `decisinLog.md` → D-009).

Етапи 2–4 — vision, не зобовʼязання; послідовність і точний скоуп можуть
змінюватись.
