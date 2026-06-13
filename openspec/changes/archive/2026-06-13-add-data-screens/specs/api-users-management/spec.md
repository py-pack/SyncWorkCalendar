## ADDED Requirements

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
