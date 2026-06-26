## 1. Backend — реєстр тригерів і ретрай-ендпоінт

- [x] 1.1 У `app/api/routers/sync_triggers.py` додати inline work-factory для reconcile (`_do_reconcile(payload)` → `ReconcileLinksTask().run(_lo(start), _hi(end), worker_key)`) і **реєстр** `TRIGGER_WORK: dict[str, Callable[[dict|None], Awaitable[dict]]]`, що мапить кожен відомий `trigger_name` на відповідну `_do_*` (тригери без payload обгорнути lambda, що ігнорує payload).
- [x] 1.2 У `app/api/routers/api_jobs.py` додати `POST /api-jobs/{job_id}/retry` (auth): `404` якщо немає; `409` якщо `status != failed`; `422` якщо `trigger_name` не в `TRIGGER_WORK`. Імпорт `TRIGGER_WORK` зі `sync_triggers` (циклу немає — `sync_triggers` не імпортує `api_jobs`; інакше винести в `app/api/sync_registry.py`).
- [x] 1.3 Реалізувати синхронне виконання з гарантованим поверненням нової job-и (за зразком `_execute`/`_bg`): `create_job(running)` → `try work(payload)` → `mark_needs_verification`/`mark_failed` у власній сесії → прочитати нову job-у за id і повернути `APIJobDetail` (HTTP `200` у **обох** випадках; повторне падіння — не `500`).

## 2. Frontend — клієнт, стор, екран

- [x] 2.1 У `api/client.ts` додати `retryJob(id) -> ApiJobDetail` (`POST /api-jobs/{id}/retry`).
- [x] 2.2 У `stores/journal.ts` додати дію `retry(id)`: `api.retryJob(id)` → далі `load()` + `refreshNeedsCount()`; помилку — у `error` (банер).
- [x] 2.3 У `views/JournalView.vue` у колонці дій на рядку зі `status === 'failed'` додати кнопку «Перезапустити» (`icon="sync"`, `variant`/`size` як інші пер-рядкові) → `store.retry(row.id)`. НЕ чіпати верхню «Підтвердити всі»; на `needs_verification` лишити «Підтвердити».
- [x] 2.4 i18n (UK+EN): `job_retry` («Перезапустити» / «Retry»).

## 3. Перевірка

- [x] 3.1 `cd front && npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [x] 3.2 `openspec validate add-api-jobs-retry --strict` — OK.
- [x] 3.3 Бекенд наживо: `POST /api-jobs/{id}/retry` (синтетичні рядки + прибирання, реальні `failed`-джоби не чіпались, бо всі — `push-to-tempo`/`reconcile-links` із зовнішніми Tempo-записами) → усі гілки PASS: happy-path (нова `needs_verification`-джоба, стара лишається `failed`, `200` з `APIJobDetail`), повторне падіння → `200` з новою `failed` (не `500`), не-`failed` → `409`, невідомий тригер → `422`, без auth → `401`, неіснуючий id → `404`; alembic head лишився `69dde0d17ff2`.
- [ ] 3.4 Браузерний QA `/journal` (на користувача): кнопка «Перезапустити» лише на `failed`-рядках, повторює саме той рядок, оновлює список/зведення/навбейдж; верхня кнопка ретраю не запускає.
