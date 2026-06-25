## ADDED Requirements

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
