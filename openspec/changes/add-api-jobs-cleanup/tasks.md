## 1. Backend — конфіг і DAO

- [x] 1.1 У `app/config.py` (`CeleryConfig`) додати `auto_verify_days: int = 7` і `job_ttl_days: int = 90` (env `APP__CELERY__AUTO_VERIFY_DAYS`/`APP__CELERY__JOB_TTL_DAYS`).
- [x] 1.2 У `app/dao/api_job_dao.py` додати `verify_matching(db, *, trigger_name, start, end, verified_by) -> int` — один атомарний `UPDATE ... WHERE status=needs_verification AND <фільтри>`, ставить `status=verified`/`verified_at=now()`/`verified_by`, повертає `rowcount`.
- [x] 1.3 Додати `auto_verify_older_than(db, older_than: datetime) -> int` (`UPDATE` `needs_verification`→`verified`, `verified_by="system"`, де `finished_at < older_than`) і `delete_terminal_older_than(db, older_than: datetime) -> int` (`DELETE` `status IN (verified, failed)` де `finished_at < older_than`).
- [x] 1.4 Додати `status_summary(db, *, trigger_name, start, end) -> dict[str,int]` — `COUNT(*) GROUP BY status` за періодом+тригером (ігнорує фільтр статусу); усі 4 ключі присутні (нулі для відсутніх).

## 2. Backend — ендпоінт verify-all і summary у списку

- [x] 2.1 У `schemas/api_jobs.py` додати `APIJobStatusSummary` (4 поля-лічильники) і `verified` у `VerifyAllResponse`; розширити `APIJobListResponse` полем `summary: APIJobStatusSummary`.
- [x] 2.2 У `routers/api_jobs.py` `list_api_jobs` додатково кликати `status_summary` і повертати `summary` (період+тригер, без статус-фільтра).
- [x] 2.3 Додати `POST /api-jobs/verify-all` (query `start`/`end`/`trigger_name`, auth) → `verify_matching(verified_by=current.username)` → `{verified: <int>}`.

## 3. Backend — планове прибирання (Celery beat)

- [x] 3.1 У `app/tasks/celery_tasks.py` додати таску `beat.cleanup_api_jobs` — **без** `api_jobs`-аудиту: свіжа сесія через місток, `auto_verify_older_than(now-AUTO_VERIFY_DAYS)` потім `delete_terminal_older_than(now-JOB_TTL_DAYS)`, лог кількостей.
- [x] 3.2 У `app/celery_app.py` додати beat-тік `daily-cleanup-api-jobs` (`crontab(hour=2, minute=0)`) на цю таску.

## 4. Frontend — типи, клієнт, стор

- [x] 4.1 У `api/types.ts` додати `ApiJobStatusSummary`, поле `summary` у `ApiJobListResponse`, `VerifyAllResponse { verified: number }`.
- [x] 4.2 У `api/client.ts`: `apiJobs` тип відповіді отримує `summary`; додати `verifyAllJobs({ start, end, trigger_name }) -> VerifyAllResponse`.
- [x] 4.3 У `stores/journal.ts` додати `summary`-стан (оновлюється в `load()`); дію `verifyAll()` — `verifyAllJobs` із поточними `period`+`triggerFilter`, далі `load()` + `refreshNeedsCount()`.

## 5. Frontend — екран `/journal`

- [x] 5.1 У `views/JournalView.vue` прибрати верхній `SyncBtn` «Оновити з джерела»; додати кнопку «Підтвердити всі» (`store.verifyAll()`), неактивну коли `summary.needs_verification === 0`.
- [x] 5.2 Додати в тулбар компактне зведення лічильників по статусах (з `store.summary`).
- [x] 5.3 CSS у `data.css`: бейдж статусу `white-space: nowrap` (+ за потреби ширша колонка `status`); стилі зведення-чипів.
- [x] 5.4 i18n (UK+EN): `job_verify_all` («Підтвердити всі»), підписи зведення (переюз `s_*`), тост/підказка результату; прибрати мертві ключі, якщо лишаються.

## 6. Перевірка

- [x] 6.1 `cd front && npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [x] 6.2 `openspec validate add-api-jobs-cleanup --strict` — OK.
- [x] 6.3 Бекенд наживо: `POST /api-jobs/verify-all` (підтверджує лише `needs_verification` за фільтром, повертає к-сть); `GET /api-jobs` повертає `summary`; DAO `auto_verify_older_than`/`delete_terminal_older_than` на синтетичних даних — PASS; alembic head лишився `69dde0d17ff2`.
- [ ] 6.4 Браузерний QA `/journal` (на користувача): «Підтвердити всі» закриває needs_verification і оновлює навбейдж; зведення видно; бейдж в один рядок; екран не виглядає порожнім.
