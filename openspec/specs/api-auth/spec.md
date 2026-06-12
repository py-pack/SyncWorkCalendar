# api-auth Specification

## Purpose

JWT-based authentication for the REST API. Logins are validated against the
`api_users` table; the API never creates users automatically. Issued tokens
carry user identity and `worker_key` claims, and all non-public routes require
a valid Bearer token.

## Requirements

### Requirement: Login via credentials from `api_users` table

Система SHALL приймати `POST /auth/login` з тілом `{username, password}` і
повертати JWT Bearer токен, якщо у таблиці `api_users` існує рядок із
`username = <input>` AND `is_active = TRUE`, а `password` після
`bcrypt`-перевірки збігається з `password_hash` цього рядка. Токен
підписується HS256 із `APP__API__JWT_SECRET` і має TTL
`APP__API__JWT_TTL_HOURS` (дефолт 24 години).

#### Scenario: Successful login

- **WHEN** клієнт `POST /auth/login` з валідними `username`+`password`
- **THEN** відповідь `200 OK` з тілом `{access_token: <jwt>, token_type: "bearer", expires_in: <seconds>}`

#### Scenario: Wrong password

- **WHEN** клієнт `POST /auth/login` з валідним `username` (існує у `api_users`) і неправильним `password`
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Invalid credentials"}`

#### Scenario: Unknown username

- **WHEN** клієнт `POST /auth/login` з `username`, якого немає у `api_users`
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Invalid credentials"}` (одне й те саме повідомлення для
  wrong password і unknown username, щоб не дати enum-ити імена)

#### Scenario: Inactive user

- **WHEN** клієнт `POST /auth/login` з валідними credentials, але `api_users.is_active = FALSE` для цього `username`
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Invalid credentials"}` (та сама відповідь, щоб не давати
  розрізнення між «нема юзера» і «деактивований»)

#### Scenario: Missing JWT secret at boot

- **WHEN** додаток стартує і `APP__API__JWT_SECRET` порожній або не заданий
- **THEN** запуск падає з помилкою на старті, до прийому першого запиту

### Requirement: API does not create users automatically

Система MUST NOT створювати жодних рядків у `api_users` автоматично — ні
на старті, ні через HTTP-endpoint. Початковий і всі наступні користувачі
заводяться через окрему backend-консольну команду, що буде додана в
наступній зміні (`add-user-management-cli`). На етапі цієї зміни заведення
користувачів — ручний INSERT у `api_users` (наприклад, через PyCharm
DataGrip) або через CLI з майбутньої зміни.

#### Scenario: Empty users table at boot

- **GIVEN** `api_users` таблиця порожня (свіжий деплой)
- **WHEN** додаток стартує
- **THEN** запуск проходить успішно; усі публічні endpoint-и (`/healthz`, `/docs`) працюють; будь-який
  `POST /auth/login` повертає `401 Unauthorized` поки немає жодного користувача

#### Scenario: No HTTP endpoint creates users

- **GIVEN** додаток запущений із валідними `api_users`
- **WHEN** клієнт шукає endpoint типу `POST /auth/register`, `POST /api-users` чи будь-який інший, що міг би створити
  рядок у `api_users`
- **THEN** такого endpoint-а в API немає — `404 Not Found`. Управління користувачами — лише через окремий CLI

### Requirement: JWT claims include user identity and worker_key

Видан токен SHALL містити claims, що ідентифікують користувача та його
`worker_key` (Jira key, по якому будуть створюватись Tempo-worklog-и).

#### Scenario: Worker key embedded in token

- **WHEN** видано JWT після успішного логіну для `api_users.id = N`, `username = "alice"`, `worker_key = "alice-key"`
- **THEN** payload токена містить `sub = "alice"`, `user_id = N`, `worker_key = "alice-key"`, `exp = <utc seconds>`,
  `iat = <utc seconds>`

#### Scenario: Worker key is null

- **GIVEN** `api_users.worker_key IS NULL` для `username`
- **WHEN** видано JWT після логіну
- **THEN** payload містить `worker_key = null`; sync-trigger-и, які вимагають worker_key
  (`POST /sync/jira/worklogs`, `/sync/worklog-tasks/push-to-tempo`), MUST повертати
  `400 Bad Request` із `{detail: "user has no worker_key configured"}` для такого токена

### Requirement: Protected routes require Bearer token

Система SHALL вимагати заголовок `Authorization: Bearer <token>` для всіх endpoint-ів, крім публічних: `/auth/login`,
`/auth/refresh`, `/healthz`, `/docs`, `/redoc`, `/openapi.json`. Відсутній або невалідний токен MUST давати відповідь
`401 Unauthorized`.

#### Scenario: Missing Authorization header

- **WHEN** клієнт викликає `GET /tc-projects` без заголовка `Authorization`
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Not authenticated"}`

#### Scenario: Expired token

- **WHEN** клієнт викликає захищений endpoint із токеном, у якого `exp` < now
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Token expired"}`

#### Scenario: Malformed token

- **WHEN** клієнт викликає захищений endpoint із токеном, що не валідується HS256-підписом
- **THEN** відповідь `401 Unauthorized` із тілом `{detail: "Invalid token"}`

#### Scenario: Health check is public

- **WHEN** клієнт викликає `GET /healthz` без токена
- **THEN** відповідь `200 OK` із тілом `{status: "ok"}`

### Requirement: Refresh token endpoint

Система SHALL надавати `POST /auth/refresh`, який приймає валідний (не прострочений) Bearer токен у заголовку та
повертає новий токен із продовженим `exp`. Прострочений refresh-запит → `401`.

#### Scenario: Refresh before expiry

- **WHEN** клієнт `POST /auth/refresh` із валідним токеном
- **THEN** відповідь `200 OK` із новим JWT, `exp` = now + `JWT_TTL_HOURS`, `iat` оновлено

#### Scenario: Refresh expired token

- **WHEN** клієнт `POST /auth/refresh` із токеном, у якого `exp` < now
- **THEN** відповідь `401 Unauthorized`, новий токен не видається

### Requirement: Current user endpoint

Система SHALL надавати `GET /auth/me`, який повертає `{username, worker_key, expires_at}` із поточного валідного токена.

#### Scenario: Authenticated me

- **WHEN** клієнт `GET /auth/me` із валідним токеном
- **THEN** відповідь `200 OK` із `{username: <sub>, worker_key: <claim>, expires_at: <ISO 8601>}`
