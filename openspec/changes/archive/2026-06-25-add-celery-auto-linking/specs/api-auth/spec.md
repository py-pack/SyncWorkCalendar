## MODIFIED Requirements

### Requirement: Current user endpoint

Система SHALL надавати `GET /auth/me`, який повертає `{username, worker_key,
expires_at, sync_prefs}` із поточного валідного токена. Поле `sync_prefs` —
повний обʼєкт per-user перемикачів автосинку з дефолтами (відсутні ключі або
`sync_prefs = NULL` → `false`), джерело — `api_users.sync_prefs` (capability
`api-users-management`).

#### Scenario: Authenticated me

- **WHEN** клієнт `GET /auth/me` із валідним токеном
- **THEN** відповідь `200 OK` із `{username: <sub>, worker_key: <claim>, expires_at:
  <ISO 8601>, sync_prefs: {auto_timecamp_pull, auto_jira_pull, auto_tempo_pull,
  auto_linking, auto_push_tempo}}`
