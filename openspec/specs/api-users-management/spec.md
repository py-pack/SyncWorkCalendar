# api-users-management Specification

## Purpose
TBD - created by archiving change add-data-screens. Update Purpose after archive.
## Requirements
### Requirement: Список користувачів

Система SHALL надавати `GET /users`, що повертає список `api_users` із полями
`id`, `username` (відображуване ім'я), `email`, `worker_key`, `is_active`
(`last_seen` відкладено — окрема зміна; у відповіді відсутній). Endpoint MUST
вимагати валідний Bearer-токен. Поле `password_hash` MUST NOT повертатися.

#### Scenario: Перегляд користувачів

- **WHEN** авторизований клієнт `GET /users`
- **THEN** відповідь `200 OK` зі списком користувачів без `password_hash`

#### Scenario: Без токена

- **WHEN** клієнт `GET /users` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Створення користувача (invite без пароля)

Система SHALL надавати `POST /users`, що створює `api_users` з полями
`username` (відображуване ім'я), `email`, `worker_key` **без пароля** (пароль
опційний). Створений користувач входить через Google за `email`
(`api-google-auth`). `email` MUST бути унікальним (регістронезалежно), а
`username` MUST бути унікальним; дублікат будь-якого → `409 Conflict`.

#### Scenario: Запрошення без пароля

- **WHEN** клієнт `POST /users` з `username`+`email`+`worker_key` без пароля
- **THEN** відповідь `201 Created`; рядок створено з `password_hash = NULL`;
  користувач зможе увійти через Google за `email`

#### Scenario: Дубльований e-mail

- **WHEN** клієнт `POST /users` з `email`, який уже є в `api_users`
- **THEN** відповідь `409 Conflict`, рядок не створюється

#### Scenario: Дубльований username

- **WHEN** клієнт `POST /users` з `username`, який уже є в `api_users`
- **THEN** відповідь `409 Conflict`, рядок не створюється

### Requirement: Редагування користувача

Система SHALL надавати `PATCH /users/{id}`, що змінює `username`, `worker_key`,
`is_active` (увімкнути/вимкнути). Відсутній `id` → `404`. Зміна `username` на
вже зайнятий → `409 Conflict`. `password_hash` не змінюється через цей
endpoint.

#### Scenario: Деактивація

- **WHEN** клієнт `PATCH /users/{id}` із `is_active=false`
- **THEN** відповідь `200 OK`; деактивований користувач не може увійти
  (ні логін/пароль, ні Google)

#### Scenario: Зміна worker_key

- **WHEN** клієнт `PATCH /users/{id}` із новим `worker_key`
- **THEN** значення оновлюється; нові sync-операції цього користувача
  використовують новий `worker_key`

### Requirement: Видалення користувача

Система SHALL надавати `DELETE /users/{id}`. Відсутній `id` → `404`.

#### Scenario: Видалення

- **WHEN** клієнт `DELETE /users/{id}` для наявного користувача
- **THEN** відповідь `200/204`, рядок прибрано; наступний `GET /users` його
  не містить

### Requirement: nullable `password_hash` (ім'я — наявний `username`)

Колонка `api_users.password_hash` SHALL стати **nullable**, щоб підтримати
invite-флоу без пароля (вхід лише через Google). Окрема колонка `name` MUST
NOT додаватися — відображуваним ім'ям слугує наявний `username`
(`NOT NULL`, `UNIQUE`). Логін/пароль для користувача без `password_hash` MUST
повертати `401` (немає чим автентифікуватись паролем).

#### Scenario: Логін користувача без пароля

- **GIVEN** користувач створений без пароля (`password_hash = NULL`)
- **WHEN** клієнт `POST /auth/login` з його `username`/будь-яким паролем
- **THEN** відповідь `401 Unauthorized` (вхід лише через Google за e-mail)

### Requirement: RBAC-ролі відкладено

Управління користувачами на цьому етапі MUST NOT впроваджувати RBAC: ролі
(`admin`/`member`/`viewer`) не персиститься і не перевіряється. Усі
`/users`-endpoint-и доступні будь-якому авторизованому користувачу
(single-user адмін-контекст). Енфорс ролей — окрема майбутня зміна.

#### Scenario: Немає перевірки ролі

- **WHEN** будь-який авторизований користувач викликає `/users`-endpoint
- **THEN** доступ надається без перевірки ролі (RBAC — поза цією зміною)

### Requirement: Per-user налаштування автосинку (`sync_prefs`)

Кожен `api_users` SHALL мати налаштування автосинку `sync_prefs` (JSONB,
**nullable**, дефолт `NULL` — без `server_default`) із булевими ключами:
`auto_timecamp_pull`, `auto_jira_pull`, `auto_tempo_pull`, `auto_linking`,
`auto_push_tempo`. Відсутність колонки/ключа MUST читатись як **`false`** (автосинк
opt-in — вмикається лише явно). Ці прапори **авторитетні** для Celery-тасок і beat
(capability `async-task-queue` / `backend-auto-linking`).

#### Scenario: Дефолти, коли prefs порожні

- **GIVEN** користувач із `sync_prefs = NULL` (або без потрібного ключа)
- **WHEN** зчитуються його налаштування автосинку
- **THEN** усі прапори читаються як `false` (автоматика вимкнена за замовчуванням),
  і beat/таски такого користувача **пропускають**

### Requirement: Читання і зміна власних `sync_prefs`

Система SHALL надавати `PATCH /users/me/sync-prefs`, що частково зливає передані
ключі у `sync_prefs` поточного користувача (за JWT). Невідомі ключі MUST
відхилятись (`extra = forbid` → `422`). Endpoint вимагає валідний Bearer-токен.

#### Scenario: Вимкнення одного автосинку

- **GIVEN** авторизований користувач
- **WHEN** він викликає `PATCH /users/me/sync-prefs` з `{auto_push_tempo: false}`
- **THEN** відповідь `200 OK`; у `sync_prefs` ключ `auto_push_tempo = false`, інші
  ключі лишаються незмінними

#### Scenario: Невідомий ключ

- **WHEN** тіло містить ключ поза переліком (`{foo: true}`)
- **THEN** відповідь `422 Unprocessable Entity`; `sync_prefs` не змінюється

#### Scenario: Без токена

- **WHEN** клієнт викликає `PATCH /users/me/sync-prefs` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Self-service редагування власного профілю

Система SHALL надавати `PATCH /users/me`, що редагує поля **поточного** користувача
(за JWT). Дозволено редагувати всі профільні поля, **крім** `email` і `is_active`:
ці два MUST бути відхилені (`422`) або проігноровані на self-edit — `email` лишається
адмінським (ключ match-by-email Google-входу), `is_active` — щоб користувач не вимкнув
сам себе. Принаймні `username` і `worker_key` MUST бути редагованими. Пароль цим
endpoint-ом **не** змінюється (окремий `PATCH /users/me/password`). Endpoint MUST
вимагати валідний Bearer-токен.

#### Scenario: Зміна власних username/worker_key

- **WHEN** авторизований користувач `PATCH /users/me` з новими `username`/`worker_key`
- **THEN** відповідь `200 OK`; поля оновлюються для поточного користувача

#### Scenario: Спроба змінити email або is_active

- **WHEN** тіло містить `email` або `is_active`
- **THEN** ці поля **не** застосовуються (відхилення `422` або ігнор); користувач не
  може змінити e-mail чи деактивувати себе

#### Scenario: Без токена

- **WHEN** клієнт `PATCH /users/me` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Self-service зміна власного пароля

Система SHALL надавати `PATCH /users/me/password`, що змінює пароль **поточного**
користувача (за JWT). Для користувача з наявним паролем тіло MUST містити поточний і
новий пароль, і поточний звіряється; для invite-користувача з `NULL`-хешем поточний
пароль не вимагається — endpoint **встановлює** перший пароль (після чого можливий
логін за паролем). Новий хеш — той самий формат `bcrypt` (`$2b$`). Endpoint MUST
вимагати валідний Bearer-токен. Зміна чужого пароля цим endpoint-ом неможлива.

#### Scenario: Зміна наявного пароля

- **GIVEN** користувач із наявним паролем
- **WHEN** він `PATCH /users/me/password` з коректним поточним і новим паролем
- **THEN** відповідь `200 OK`; наступний логін працює з новим паролем

#### Scenario: Невірний поточний пароль

- **WHEN** користувач передає невірний поточний пароль
- **THEN** відповідь `400/401`; пароль не змінюється

#### Scenario: Встановлення першого пароля (invite-користувач)

- **GIVEN** користувач із `password_hash = NULL` (входив лише через Google)
- **WHEN** він `PATCH /users/me/password` з новим паролем
- **THEN** відповідь `200 OK`; `password_hash` встановлюється, логін за паролем стає
  можливим

#### Scenario: Без токена

- **WHEN** клієнт `PATCH /users/me/password` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

