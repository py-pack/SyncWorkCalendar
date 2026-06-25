## Context

`api_jobs` — лог кожного виклику синку зі state machine
`running → needs_verification → verified` / `running → failed` (capability
`api-jobs`). Обгортка `app/api/jobs_wrapper.py` (`create_job`/
`run_existing_job`/`run_job`) і DAO `app/dao/api_job_dao.py`
(`create_running`/`mark_needs_verification`/`mark_failed`/`mark_verified`/
`get_by_id`/`list_filtered`). `Celery beat` уже існує (`app/celery_app.py`:
`01:00` TimeCamp+Jira, `01:30` Tempo; таймзона `APP__CELERY__TIMEZONE`, усі часи
в UTC). Конфіг — `app/config.py` (`CeleryConfig` має лише `timezone`).

Проблема: успішні job-и осідають у `needs_verification` і накопичуються (306
рядків), бо їх ніхто не закриває; навбейдж росте. Підтверджено grep-ом: жодна
логіка не читає/не гейтить на `verified` — це суто аудит. `rework-journal-screen`
полагодив серіалізацію й уніфікував екран, але retention лишив поза скоупом
(саме ця зміна). DB має CHECK `verified_at_only_when_verified`
(`verified_at IS NULL OR status='verified'`) — будь-який verify MUST виставляти
`verified_at` разом зі `status=verified`.

## Goals / Non-Goals

**Goals:**
- Зупинити безмежне зростання `needs_verification` (авто-verify за віком) і
  таблиці `api_jobs` (TTL-видалення термінальних рядків).
- Дати ручне масове закриття (`POST /api-jobs/verify-all` за фільтрами) + кнопку
  «Підтвердити всі» на `/journal`.
- Прибрати оманливу кнопку «Оновити з джерела»; покращити вигляд (бейдж без
  переносу, зведення лічильників замість порожнечі).

**Non-Goals:**
- Жодних змін моделі/схеми БД, **без alembic** (head `69dde0d17ff2`).
- Скасування/повтор job-а, ручне видалення окремих рядків з UI.
- Окремий довший TTL для `failed` (поки термінальні чистяться спільним `M`).
- «Мова синку» (`SyncState`/`SyncFilter`/`SyncTri`) — статус job-а 4-становий.

## Decisions

**D1. Авто-verify за віком — окрема планова таска, перехід лише
`needs_verification → verified`.**
Нова `Celery`-таска `beat.cleanup_api_jobs` авто-підтверджує job-и зі
`status=needs_verification` AND `finished_at < now() - N днів`
(`APP__CELERY__AUTO_VERIFY_DAYS`, дефолт `7`), ставлячи `status=verified`,
`verified_at=now()`, `verified_by="system"`. `WHERE status=needs_verification`
гарантує дотримання state machine (інші статуси не зачіпає). DAO
`auto_verify_older_than(db, older_than) -> int`.
*Чому за віком, а не одразу при успіху:* лишаємо вікно для людського огляду
свіжих синків; рутинні старі — самозакриваються. *Альтернатива* (verify одразу в
`run_existing_job`) відкинута — прибрала б людський крок і ускладнила б код
аудиту.

**D2. TTL-видалення — лише термінальні рядки.**
Та сама таска видаляє `status IN (verified, failed)` AND
`finished_at < now() - M днів` (`APP__CELERY__JOB_TTL_DAYS`, дефолт `90`).
`running` і `needs_verification` **ніколи** не видаляються (незавершене/неоглянуте
не втрачаємо). DAO `delete_terminal_older_than(db, older_than) -> int`. Послідовно
**після** D1 у межах одного тіку, тож авто-verify-нуте з часом теж стане
видаленним. *Трейд-оф:* видаляються й старі `failed` (втрата error-історії >90 днів)
— прийнятно за рішенням користувача; окремий довший TTL для `failed` — поза скоупом.

**D3. Maintenance-таска НЕ обгортається в `api_jobs`-аудит.**
На відміну від sync-тасок (усі йдуть через `run_audited_task`/`jobs_wrapper`),
прибирання `api_jobs` саме **не** створює рядок `api_jobs` — інакше maintenance
плодив би job-и, які потім сам же чистить (рекурсія/шум). Таска лише логує
(`logger`) к-сть авто-verify-нутих і видалених. Beat-тік — щодоби ~`02:00`
(фіксована константа, після нічних синків `01:00`/`01:30`), таймзона зі спільного
`APP__CELERY__TIMEZONE`. Per-user `sync_prefs` тут **не** застосовні (це глобальна
maintenance, не per-user синк).

**D4. Масовий verify — один атомарний `UPDATE` за фільтрами.**
`POST /api-jobs/verify-all` із query-фільтрами `start`/`end` (за `started_at`,
опційно) і `trigger_name` (опційно); `status` завжди `needs_verification`. DAO
`verify_matching(db, *, trigger_name, start, end, verified_by) -> int` робить один
`UPDATE ... WHERE status=needs_verification AND <фільтри> RETURNING`-`rowcount`,
ставлячи `status=verified`/`verified_at=now()`/`verified_by=<user>`. Повертає
`{verified: <int>}`. Без поштучного циклу (швидко й атомарно). Дзеркалить набір
фільтрів `GET /api-jobs`, тож кнопка «Підтвердити всі» діє рівно на поточну
вибірку (мінус пагінація).

**D5. Frontend — «Підтвердити всі» замість «Оновити з джерела».**
Верхню дію `SyncBtn`-«Оновити з джерела» (оманлива — це лише `store.load()`)
прибираємо; натомість кнопка **«Підтвердити всі»** кличе `store.verifyAll()`
(`POST /api-jobs/verify-all` з поточними `period`+`triggerFilter`), після чого
`load()` (релоад списку + зведення) і `refreshNeedsCount()`. Окремий ручний
re-read не потрібен — релоад відбувається після дії, а зведення/навбейдж
оновлюються там само. Кнопка дизейблиться, коли в поточній вибірці немає
`needs_verification` (видно зі `summary`).

**D6. Зведення лічильників — `summary` у відповіді `GET /api-jobs`.**
`GET /api-jobs` додає `summary: {running, needs_verification, verified, failed}`
— `COUNT(*) GROUP BY status` за фільтром **періоду+тригера** (ігноруючи фільтр
статусу, щоб зведення показувало повну картину періоду). Прецедент — `summary` у
`WorklogSyncTasksResponse`. Фронт показує його компактними чипами в тулбарі
(`running`/`needs_verification`/`verified`/`failed`) — заповнює порожнечу й дає
огляд. *Альтернатива* (окремий ендпоінт лічильників) відкинута — зайвий round-trip;
список і так вантажиться разом.

**D7. Бейдж статусу без переносу.**
`white-space: nowrap` на бейджі статусу (+ за потреби трохи ширша колонка
`status`), щоб «Потребує перевірки» не ламалось у два рядки. Чисто CSS/розмітка.

## Risks / Trade-offs

- **[Авто-verify ховає успіхи від огляду]** → Тільки `needs_verification`
  (успіхи); `failed` **ніколи** не авто-verify-иться й лишається видимим. Вікно
  огляду — `N`=7 днів (конфіг). Низький ризик.
- **[TTL видаляє старі `failed` — втрата error-історії]** → Лише >`M`=90 днів
  (конфіг); за потреби окремий довший TTL для `failed` — майбутнє. Прийнятно.
- **[Масовий verify зачепить більше, ніж видно на сторінці]** → Свідомо: діє на
  весь фільтр періоду+тригера, не лише поточну сторінку; `status` жорстко
  `needs_verification`, тож термінальних не чіпає. Кнопка показує намір; за потреби
  звузити — звузити період/тригер.
- **[Регрес шейпу `GET /api-jobs` (додавання `summary`)]** → Адитивно (нове поле),
  наявні споживачі (`items`/`total`) не ламаються; навбейдж-виклик
  (`?status=needs_verification&limit=1`) лишається валідним.
- **[Maintenance-таска без аудиту — менше видимості]** → Свідомо (D3); логування
  через `logger` достатньо, аудит maintenance створив би рекурсію.
