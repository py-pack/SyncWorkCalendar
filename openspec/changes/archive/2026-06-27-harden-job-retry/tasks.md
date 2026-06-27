## 1. Backend — атомарний рестарт

- [x] 1.1 У `app/dao/api_job_dao.py` додати `retry_claim(db, job_id) -> bool`:
  один `UPDATE api_jobs SET status='running', started_at=now(), finished_at=NULL,
  error=NULL, result=NULL WHERE id=:id AND status='failed'`; повертає
  `rowcount == 1` (чи захоплено рядок).
- [x] 1.2 Переписати `retry_api_job` у `app/api/routers/api_jobs.py`: `get_by_id`
  → `404` якщо нема; `retry_claim` → `409` (`"job is not in failed status"`)
  якщо `False`; перевірка `TRIGGER_WORK.get(trigger_name)` → якщо нема, закрити
  той самий рядок `mark_failed("trigger is not retryable")` і повернути `422`.
- [x] 1.3 Виконати роботу `await work(payload)` і закрити **той самий** `job_id`
  через власні короткі сесії: успіх → `mark_needs_verification`, виняток →
  `mark_failed`; **без** re-raise (повертаємо `APIJobDetail` того самого рядка,
  не `500`). Прибрати виклик `create_job` з цього шляху.
- [x] 1.4 Перечитати рядок (`get_by_id`) і повернути `APIJobDetail` з тим самим
  `id` у обох гілках.

## 2. Frontend — pending-стан кнопки

- [x] 2.1 У `front/src/views/JournalView.vue` додати на кнопку «Перезапустити»
  pending-стан: спінер + `disabled` доки триває `store.retry(id)` (переюз
  `components/data/SyncBtn.vue` через `action`-проп або локальний `ref` стану
  по `id` рядка).
- [x] 2.2 Переконатися, що `stores/journal.ts → retry(id)` лишається сумісним:
  після відповіді `load()` оновлює список/зведення/навбейдж; помилка → банер
  `error`, без падіння таблиці.
- [x] 2.3 `npm run build` (`vue-tsc` + `vite`) — чисто.

## 3. Верифікація

- [x] 3.1 Backend наживо (контейнер `api`): на синтетичному `failed`-рядку
  безпечного тригера (напр. `sync.worklog-tasks.prepare` на порожньому
  майбутньому періоді) — `retry` повертає `200` із **тим самим** `id` у
  `needs_verification`; нового рядка немає.
- [x] 3.2 Паралельний/повторний `retry` під час `running` → `409`; не-`failed`
  → `409`; неіснуючий `id` → `404`; без auth → `401`; невідомий тригер → `422`
  (рядок стає `failed`). Синтетику прибрати.
- [x] 3.3 `openspec validate harden-job-retry --strict` — OK.
- [x] 3.4 Браузерний QA `/journal` (на користувача): клік «Перезапустити» дає
  спінер; повторний клік не відправляє другий запит; після завершення рядок
  оновлюється на місці. **Підтверджено користувачем — працює.**
