## Why

Екран `/journal` щойно полагоджено й уніфіковано (`rework-journal-screen`), але
лишається структурна проблема: успішні sync-job-и осідають у статусі
`needs_verification` і **накопичуються безмежно** (на момент аналізу — **306**
рядків), бо нічого їх не закриває. Навбейдж біля «Журнал» рахує саме
`needs_verification` і росте без меж. Аналіз коду підтвердив: від статусу
`verified` **нічого** в системі не залежить (нічого не гейтить наступні синки) —
це суто аудит/лічильник. Тож «потребує перевірки» для рутинних автосинків — це
шум, який ніхто не закриває вручну, а таблиця `api_jobs` росте необмежено.

## What Changes

- **Авто-verify за віком (backend):** нова планова `Celery`-таска MUST
  авто-підтверджувати `needs_verification`-job-и, старші за `N` днів (дефолт
  `7`, конфіг `APP__CELERY__AUTO_VERIFY_DAYS`), ставлячи `verified_by="system"`.
  Свіжі (молодші за TTL) лишаються для людського огляду; `running`/`failed` не
  чіпаються. Перехід лише `needs_verification → verified` (поважає state machine).
- **TTL-видалення старих рядків (backend):** та сама планова таска MUST видаляти
  **термінальні** job-и (`verified` АБО `failed`), старші за `M` днів (дефолт
  `90`, конфіг `APP__CELERY__JOB_TTL_DAYS`). `running` і `needs_verification`
  **ніколи** не видаляються. Журнал лишається історією до TTL.
- **Масовий verify (backend):** новий ендпоінт `POST /api-jobs/verify-all`, що
  підтверджує **всі** `needs_verification`, які підпадають під фільтри
  (`start`/`end` за `started_at`, опційно `trigger_name`; `status` завжди
  `needs_verification`); повертає `{verified: <int>}`, `verified_by` = поточний
  користувач. Атомарний bulk-`UPDATE` (без поштучного циклу).
- **Зведення лічильників (backend):** `GET /api-jobs` MUST додатково повертати
  `summary` — кількість job-ів по кожному статусу
  (`running`/`needs_verification`/`verified`/`failed`) за поточним фільтром
  періоду+тригера (ігноруючи фільтр статусу), за прецедентом `summary` у
  `GET /worklog-sync-tasks`.
- **Кнопка «Підтвердити всі» (frontend):** на `/journal` верхню кнопку «Оновити з
  джерела» (зараз просто `store.load()` — назва оманлива, журнал сам є логом
  синків) MUST замінити на **«Підтвердити всі»** → `POST /api-jobs/verify-all` з
  поточними фільтрами (період + тригер) → після успіху релоад списку й навбейджа.
- **Візуальне полірування (frontend):** бейдж статусу (напр. «Потребує перевірки»)
  MUST NOT переноситись у два рядки (`white-space: nowrap`); у тулбар додати
  компактне зведення лічильників по статусах (з `summary`) — корисний
  at-a-glance огляд, що заповнює порожнечу екрана.

## Capabilities

### New Capabilities
<!-- Нових capability немає. -->

### Modified Capabilities
- `api-jobs`: новий `POST /api-jobs/verify-all` (масовий verify за фільтрами);
  `GET /api-jobs` додає `summary` (лічильники по статусах); розширення life-cycle
  retention — авто-`needs_verification → verified` (`verified_by="system"`) за TTL
  і видалення термінальних рядків за TTL.
- `frontend-sync-journal`: верхня дія — «Підтвердити всі» замість оманливого
  «Оновити з джерела»; зведення лічильників у тулбарі; бейдж статусу без переносу.
- `async-task-queue`: нова планова maintenance-таска прибирання `api_jobs`
  (авто-verify + TTL-видалення) у beat-розкладі (щодоби, окремий тік).

## Impact

- **Backend (`api/`):** `app/config.py` (`CeleryConfig` +
  `auto_verify_days`/`job_ttl_days`); `app/celery_app.py` (новий beat-тік
  ~`02:00`); `app/tasks/celery_tasks.py` (нова таска `beat.cleanup_api_jobs` —
  **без** `api_jobs`-аудиту, це maintenance, не синк); `app/dao/api_job_dao.py`
  (`verify_matching`, `auto_verify_older_than`, `delete_terminal_older_than`);
  `app/api/routers/api_jobs.py` + `schemas/api_jobs.py` (ендпоінт `verify-all`,
  `summary` у відповіді списку). **Без alembic** (head `69dde0d17ff2`): колонки
  `verified_by/verified_at/finished_at/status` уже є, `verified_by="system"` —
  рядок, нових колонок немає.
- **Frontend (`front/`):** `api/types.ts` (`ApiJobListResponse.summary`,
  `VerifyAllResponse`), `api/client.ts` (`verifyAllJobs`, `apiJobs` повертає
  `summary`), `stores/journal.ts` (`summary`-стан, дія `verifyAll`),
  `views/JournalView.vue` (кнопка «Підтвердити всі» + зведення), i18n (UK+EN),
  CSS у `data.css` (бейдж `nowrap` + зведення). Без нових залежностей.
- **Залежність:** будується **поверх** `rework-journal-screen` (спільні файли
  `JournalView.vue`/`journal.ts`/`api_jobs.py`) — її слід заархівувати **першою**.
- **«Мова синку»** (`SyncState`/`SyncFilter`) тут **не** застосовується (статус
  job-а — 4-станова машина життєвого циклу).
- **Поза скоупом:** скасування/повтор job-а, ручне видалення окремих рядків з UI,
  окремий довший TTL для `failed` (поки термінальні чистяться спільним `M`).
