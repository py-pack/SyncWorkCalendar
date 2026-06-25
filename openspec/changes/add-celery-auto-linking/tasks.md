## 1. Залежності та конфіг

- [x] 1.1 Додати `celery[redis]` у `api/pyproject.toml`; `uv sync` (оновити `uv.lock`)
- [x] 1.2 Додати у `app/config.py` секції `redis` (`APP__REDIS__URL`) і `celery`
      (`APP__CELERY__TIMEZONE`, дефолт `UTC`); часи beat — фіксовані константи в коді
- [x] 1.3 Прокинути `APP__REDIS__*` у спільний `.env`/`api/.env.template`

## 2. Celery-застосунок і таски

- [x] 2.1 Створити `app/celery_app.py` (інстанс `Celery`, broker = `APP__REDIS__URL`,
      без окремого result backend, автодискавері тасок)
- [x] 2.2 Винести спільне ядро `api_jobs`-аудиту з `jobs_wrapper.run_job`, щоб
      використовувати його і поза HTTP (з Celery-таски)
- [x] 2.3 Реалізувати безпечний async→Celery місток: кожна таска через
      `asyncio.run` зі **свіжим** engine/sessionmaker і `dispose()` на виході
- [x] 2.4 Celery-таски-обгортки над наявними методами: `sync_timecamp_entries`,
      `sync_jira_issues_all`, `sync_tempo_worklogs` (`update_worklog`)
- [x] 2.5 Налаштувати воркер `--pool=prefork --max-tasks-per-child=N` (підстраховка
      від loop-binding asyncpg)

## 3. Реконсиляція лінків (`backend-auto-linking`)

- [x] 3.1 `JRWorklogDAO.find_match(jr_issues_id, jr_worker_key, started_at, duration)`
      — пошук наявного Tempo-worklog-а для дедупу
- [x] 3.2 Таска `reconcile_links(period, worker_key)`: upsert `WorklogSyncTask` за
      `source_id`, резолв `issue_id`, постановка пушу/оновлення (ідемпотентно)
- [x] 3.3 Перелінк при зміні матчу (`issue_key`/`issue_id`), **без** авто-відлінку,
      коли матч зник
- [x] 3.4 Інтегрувати дедуп (3.1) у пуш: збіг у `jr_worklogs` → `target_id` +
      `created` без HTTP-виклику
- [x] 3.5 Активувати update-flow: `JiraService.update_worklog` (Tempo
      `PUT tempo-timesheets/4/worklogs/{id}`) + переходи `created → pre_update →
      update → updated` при розбіжності контенту/часу
- [x] 3.6 Гейтити пуш/оновлення per-user прапором `auto_push_tempo`

## 4. Beat-розклад

- [x] 4.1 Описати beat-schedule (таймзона з `APP__CELERY__TIMEZONE`, дефолт `UTC`):
      `01:00` — TimeCamp entries + Jira issues; `01:30` — Tempo worklogs; після
      кожного витягу — `reconcile_links`
- [x] 4.2 Beat ітерує активних `api_users` з `worker_key` і ставить per-user таски,
      поважаючи відповідні `sync_prefs`
- [x] 4.3 Глобальні (не-per-user) витяги проектів/задач — один раз за тік

## 5. Per-user `sync_prefs` (`api-users-management` / `api-auth`)

- [x] 5.1 Додати `api_users.sync_prefs` (JSONB, **nullable**, дефолт `NULL`, без
      `server_default`) у модель
- [x] 5.2 `alembic revision --autogenerate` (від head `10b7dc50b00f`) + `upgrade head`
- [x] 5.3 Хелпер читання `sync_prefs` із дефолтами (відсутність/`NULL`/відсутній ключ
      → `false`)
- [x] 5.4 `PATCH /users/me/sync-prefs` (часткове злиття, `extra=forbid` → 422)
- [x] 5.5 Додати `sync_prefs` у відповідь `GET /auth/me`

## 6. Тригер реконсиляції (`api-sync-triggers`)

- [x] 6.1 `POST /sync/reconcile-links` (опц. `{start,end}`) — `enqueue`
      `reconcile_links`, `worker_key` із JWT, `400` без `worker_key`, повертає `job_id`
- [x] 6.2 Перевести опційне фонове виконання важких тригерів на `enqueue` у чергу
      (замість `BackgroundTasks`), зберігши синхронний режим за замовчуванням

## 7. Docker (`container-orchestration`)

- [x] 7.1 Додати сервіс `redis` (named volume, host-порт `11332`) у `docker-compose.yml`
- [x] 7.2 Додати сервіси `worker` (`celery -A app.celery_app worker`) і `beat`
      (`celery -A app.celery_app beat`) на образі `./api`, без портів, depends_on
      `redis`+`db`
- [x] 7.3 Прокинути `APP__REDIS__URL`/`APP__DB__*` у `worker`/`beat`; конфіги — у
      `docker/` за потреби; оновити `Makefile`-шорткати за потреби

## 8. Перевірка

- [x] 8.1 Smoke: `docker compose up` піднімає `redis`/`worker`/`beat`; beat-тік ставить
      задачі; воркер виконує і пише `api_jobs`
- [x] 8.2 `POST /sync/reconcile-links` → задача в черзі → `WorklogSyncTask`
      створюється/перелінковується; дедуп проти `jr_worklogs` не плодить дублів
- [x] 8.3 Зміна опису вже-`created` запису → оновлення Tempo-worklog
      (`pre_update → update → updated`); видалення не відбувається
- [x] 8.4 `PATCH /users/me/sync-prefs` вимикає автосинк → beat/таски пропускають
      користувача; `GET /auth/me` віддає `sync_prefs`
- [x] 8.5 `openspec validate add-celery-auto-linking --strict` — OK
