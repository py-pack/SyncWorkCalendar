## MODIFIED Requirements

### Requirement: Current user endpoint

Система SHALL надавати `GET /auth/me`, який повертає
`{username, email, worker_key, is_active, expires_at, sync_prefs}` із поточного
валідного токена та рядка користувача. Поля `email` і `is_active` додано для
read-only показу на екрані «Профіль» (`frontend-profile`): self-edit їх **не**
змінює (`email` — Google-ідентичність, `is_active` — щоб користувач не вимкнув сам
себе). `sync_prefs` — повний обʼєкт перемикачів автосинку з дефолтами (відсутні
ключі / `NULL` → `false`).

#### Scenario: Authenticated me

- **WHEN** клієнт `GET /auth/me` із валідним токеном
- **THEN** відповідь `200 OK` із `{username: <sub>, email: <e-mail|null>,
  worker_key: <claim>, is_active: <bool>, expires_at: <ISO 8601>, sync_prefs: <obj>}`

#### Scenario: Missing or invalid token

- **WHEN** клієнт `GET /auth/me` без `Authorization` або з невалідним токеном
- **THEN** відповідь `401 Unauthorized`
