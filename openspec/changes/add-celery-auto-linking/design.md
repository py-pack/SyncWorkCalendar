## Context

Бекенд (`api/`, пакет `app`) уже має готовий конвеєр синку TimeCamp↔Tempo, але
весь він **синхронний і ручний**:

- `TimeCampUpdateTask` тягне записи; SQLAlchemy-event `change_tc_entry_description`
  на **кожен set опису** рахує `meta.task` через `SyncTaskService.match_task`.
- `WorllogSyncTask.create_task_for_sync → before_create → create_worklogs` будує
  `worklog_sync_tasks` (`pre_create → create → created`) і пушить у Tempo.
- `UpdateJiraTask.update_worklog` тягне реальні Tempo-worklog-и в `jr_worklogs`.
- HTTP-тригери `POST /sync/**` обгорнуті в `run_job` (`api_jobs`:
  `running → needs_verification | failed`), опційно `?background=true` через
  FastAPI `BackgroundTasks` (живе лише в процесі `api`, не виживає рестарт).

Розриви, які закриває ця зміна (підтверджено аналізом коду):

1. `before_create`/`create_worklogs` **не звіряють** запис проти `jr_worklogs` →
   ризик дублів у Tempo.
2. Матчинг переобчислюється лише на set опису, але **ніщо не перелінковує** наявний
   `WorklogSyncTask`, якщо задача в описі змінилась.
3. Немає **планувальника** і **тривкої черги** — фон тримається на
   `BackgroundTasks`.

Інфраструктура: монорепо, `docker-compose.yml` на корені (`api`/`front`/`db`),
host-порти за схемою `TT-AA-S` (продукт `33`). Конвенції Docker — `docker/`-конфіги,
`Redis → named volume` ([[docker-infra-conventions]]).

## Goals / Non-Goals

**Goals:**

- Тривка черга (`Celery` + `Redis`) і планувальник (`beat`) у власних контейнерах.
- Авто-реконсиляція лінків TimeCamp↔Tempo на **створення і зміну** опису; дедуп
  проти `jr_worklogs`; авто-створення/оновлення Tempo-відмітки до кінцевого стану.
- Beat-розклад: щодоби витяг TimeCamp/Jira (`01:00`) і Tempo (`01:30`) + реконсиляція.
- Per-user перемикачі автосинку, які поважають таски й beat.
- Зберегти `api_jobs`-аудит і всі наявні ендпоінти (зміни **additive**).

**Non-Goals:**

- Frontend (екран `/tempo`, UI перемикачів) — окрема зміна `rework-tempo-screen`.
- Повний RBAC / per-user OAuth-токени на Jira/TimeCamp (лишається `APP__*__TOKEN`).
- Видалення Tempo-worklog-ів (`delete`) і відлінкування — **свідомо поза скоупом**
  (правило «не відлінковуємо автоматично»).
- Заміна HTTP-тригерів — вони лишаються; черга йде **поряд**.

## Decisions

### D1. Брокер — Redis, окремий сервіс, порт `11332`

`Redis` як брокер Celery; персистентність — **іменований Docker volume** (конвенція).
Host-порт за схемою `TT-AA-S`: тип БД `11`, продукт `33`, індекс `2` →
**`11332`** (postgres лишається `11331`). Конфіг — `APP__REDIS__URL`
(дефолт `redis://redis:6379/0`).
**Result backend:** не вмикаємо окремо — джерело істини про статус лишається
`api_jobs`; Redis тримає лише чергу (менше TTL-сміття, простіший дебаг).
*Альтернатива:* RabbitMQ — відкинуто (зайва вага; Redis уже в конвенціях проекту).

### D2. Топологія контейнерів — окремі `worker` і `beat`

Два сервіси на тому самому образі, що `api` (`./api/Dockerfile`):
`worker` (`celery -A app.celery_app worker`) і `beat`
(`celery -A app.celery_app beat`). **Не** використовуємо `worker -B`: суміщений
beat припустимий лише для дев-одиничного воркера й дублює розклад при масштабуванні.
Обидва без exposed-портів; залежать від `redis` і `db`; монтують `./api` для
дев-hot-reload (як `api`). Конфіги — у `docker/` за потреби.
*Альтернатива:* один контейнер `worker -B` — простіше, але крихко; відкинуто.

### D3. Celery-таски — тонкі обгортки над наявними async-методами

Celery-таски **не дублюють** логіку: вони викликають наявні корутини
(`TimeCampUpdateTask`, `UpdateJiraTask`, `WorllogSyncTask`) через `asyncio.run(...)`
і переюзовують **той самий** `api_jobs`-аудит (винести спільне ядро `run_job` так,
щоб воно працювало і поза HTTP). Кожна таска створює власний event-loop.
*Наслідок:* async-engine (`async_session_maker`) прив'язаний до loop — кожна таска
**створює свіжий sessionmaker / диспоузить engine** наприкінці (див. Risks).

### D4. Авто-лінкування — через реконсиляцію, не з ORM-event

ORM-event `change_tc_entry_description` лишається як є (рахує `meta.task` синхронно;
з нього ставити в чергу не можна — немає Celery-контексту й це порушило б межі шарів).
Натомість нова **idempotent-таска `reconcile_links(period, worker_key)`**:

1. Для кожного TimeCamp-запису періоду перевіряє поточний матч (`meta.task` →
   fallback `tc_project.issue_key`).
2. **Upsert `WorklogSyncTask`**: якщо немає — створює (`pre_create`); якщо є, але
   `issue_key` більше не збігається з матчем — **перелінковує** (оновлює
   `issue_key`/`issue_id`); якщо матчу немає взагалі — **лишає** наявний звʼязок
   (ніколи не відлінковує авто).
3. Резолвить задачі (`before_create`-логіка) і **ставить у чергу** `push`/`update`.

Тригериться: (а) після кожного витягу даних (TimeCamp/Tempo), (б) глобальною кнопкою
«звʼязати все» (тепер `enqueue`), (в) beat-розкладом.
*Чому не event-driven на рівні рядка:* реконсиляція періоду простіша, ідемпотентна,
переживає пропущені події й ребут; зміна опису підхоплюється наступним проходом
(ручним або плановим).

### D5. Дедуп проти Tempo — `JRWorklogDAO.find_match`

Перед пушем `reconcile`/`push` звіряє кандидата з `jr_worklogs` за
`(jr_issues_id, jr_worker_key, started_at, duration)`. Якщо знайдено — записуємо
`WorklogSyncTask.target_id` наявного worklog-а і ставимо `status = created` **без**
HTTP-виклику в Tempo. Це закриває розрив №1.
*Толерантність* (округлення часу/часові зони) — див. Open Questions; для v1 — точний
збіг хвилин і секунд тривалості.

### D6. Update-flow активується (`pre_update → update → updated`)

Вимога «знайшли метч → створили **або оновили**» вмикає раніше зарезервований
ланцюг. Якщо `WorklogSyncTask` уже `created` (є `target_id`), але контент/час
розійшлися з тим, що в Tempo, — переходимо `created → pre_update → update`, кличемо
**оновлення Tempo-worklog-а** (новий метод у `JiraService` поверх Tempo
`PUT tempo-timesheets/4/worklogs/{id}`), далі `updated`. Видалення — поза скоупом.
*Свідоме розширення:* частина колишньої `add-worklog-update-flow` поглинається тут,
бо без update авто-метч на зміну опису неможливо «довести до кінця».

### D7. Per-user перемикачі — `api_users.sync_prefs` (JSONB)

Один **JSONB**-стовпець `sync_prefs` з типізованими ключами (а не N булевих колонок —
гнучкіше для майбутніх перемикачів, одна міграція):

```
sync_prefs = {
  "auto_timecamp_pull": bool,   # плановий витяг TimeCamp-записів
  "auto_jira_pull":     bool,   # плановий витяг Jira-задач
  "auto_tempo_pull":    bool,   # плановий витяг Tempo-worklog-ів
  "auto_linking":       bool,   # реконсиляція матчів TimeCamp↔Tempo
  "auto_push_tempo":    bool    # авто-створення/оновлення Tempo-відмітки
}
```

Колонка **nullable, дефолт `NULL`** (без `server_default`). Відсутня колонка/ключ
читається як **`false`** — автосинк **opt-in**: вмикається лише явно. Beat і таски
обробляють користувача за конкретним автосинком **тільки** якщо відповідний прапор
явно `true`; `NULL`/відсутність → пропуск. Запис/читання — через API (D8).
*Чому opt-in (зміна рішення):* авто-пуш створює реальні worklog-и в Tempo — безпечніше
не вмикати масово; користувач свідомо вмикає потрібне в профілі.
*Альтернатива:* окрема таблиця `user_sync_prefs` — відкинуто (1:1 із користувачем,
JSONB достатньо).

### D8. API per-user prefs

`/auth/me` додає поле `sync_prefs` (повний обʼєкт із дефолтами). Зміна — `PATCH
/users/me/sync-prefs` (часткове злиття переданих ключів; `extra="forbid"` на
невідомі ключі). Адмінська зміна чужих prefs — поза скоупом v1.

### D9. Beat — ітерація по активних користувачах

Beat-задачі не мають JWT, тож worker_key беруть з БД: для кожного `api_users` з
`is_active = true` і непорожнім `worker_key`, у якого **явно** ввімкнено відповідний
`sync_prefs`-прапор, **ставлять окрему таску** з його `worker_key`. Дані, не
привʼязані до користувача (TimeCamp/Jira projects, issues), синкаються раз глобально.

**Час і таймзона:** часи розкладу — **фіксовані константи** (не env): `01:00` —
TimeCamp entries + Jira issues; `01:30` — Tempo worklogs (ширший проміжок, щоб витяг
гарантовано завершився до Tempo-кроку); обидва ланцюги завершуються `reconcile_links`.
**Таймзона** — через env `APP__CELERY__TIMEZONE` (дефолт `UTC` = UTC+0); це
`Celery`-налаштування `timezone`/`enable_utc`. Усе зберігається й порівнюється в UTC;
якщо знадобиться локальна зона — змінюється лише ця env-змінна.

## Risks / Trade-offs

- **asyncpg + Celery prefork (event-loop binding):** глобальний async-engine,
  створений в одному loop, ламається при виклику з іншого. → *Mitigation:* кожна
  таска робить `asyncio.run` із **свіжим** engine/sessionmaker і `dispose()` на
  виході; `worker --pool=prefork` із `--max-tasks-per-child` як підстраховка.
- **Авто-запис у Tempo — реальний зовнішній сайд-ефект:** помилковий метч створить
  «живий» worklog. → *Mitigation:* автосинк **opt-in** (`sync_prefs` дефолт `false`/
  `NULL`, D7) — масово нічого не пушиться, доки користувач не ввімкне; дедуп (D5) проти
  дублів; правило «не відлінковуємо»; усе йде через `api_jobs`-аудит.
- **Дубль через стале `jr_worklogs`:** якщо Tempo не витягнуто свіжо, дедуп промахне.
  → *Mitigation:* beat тягне Tempo перед реконсиляцією; ручна кнопка «Забрати з
  Tempo» (зміна 2); `source_id`-унікальність WST лишається першим барʼєром.
- **Перекриття beat-проходів / гонки з ручним синком:** → *Mitigation:* один `beat`-
  контейнер; статус-гарди (`pre_create/create/created`) та `source_id`-унікальність
  роблять таски ідемпотентними; за потреби — Redis-lock на період+worker.
- **Зростання обсягу (update-flow):** D6 додає Tempo `PUT` і нові переходи. →
  *Mitigation:* окрема вимога в спеці + сценарії; delete лишається поза скоупом.

## Migration Plan

1. Додати `celery[redis]` у `api/pyproject.toml`; `app/celery_app.py` + модуль тасок.
2. `docker-compose.yml`: сервіси `redis` (named volume, `11332`), `worker`, `beat`.
3. `alembic revision` для `api_users.sync_prefs` (JSONB, **nullable**, дефолт `NULL`,
   без `server_default`); `upgrade head` (поточний head `10b7dc50b00f`).
4. Викотити `worker`/`beat`; перевірити enqueue з HTTP-тригера й beat-тік.
5. **Rollback:** прибрати сервіси `worker`/`beat`/`redis` і enqueue-гілку — HTTP-
   тригери й ручний конвеєр працюють як раніше; `sync_prefs` лишається невживаним
   (downgrade-ревізія дропає колонку).

## Resolved (рішення користувача 2026-06-24)

- **Таймзона/час дедупу:** усе в **UTC**. Додаємо env `APP__CELERY__TIMEZONE`
  (дефолт `UTC` = UTC+0); якщо щось зміниться — правимо лише змінну.
- **Дефолт `sync_prefs`:** колонка **nullable, дефолт `NULL`**; відсутність/`NULL` →
  **`false`** (автосинк opt-in). Вмикається явно в профілі.
- **Beat-час:** **фіксуємо константами** (без конфігу часів); проміжок між витягами
  розширено (`01:00` → `01:30`).

## Open Questions

- **Толерантність дедупу** за `started_at`/`duration`: точний збіг хвилин/секунд (v1)
  чи вікно ±хвилини? Уточнити на QA реальними даними (часи вже в UTC).
