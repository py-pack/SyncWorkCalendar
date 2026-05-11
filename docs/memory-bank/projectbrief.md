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
