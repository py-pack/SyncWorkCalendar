"""Інстанс Celery — точка входу воркера й beat (`-A app.celery_app`).

Брокер — `Redis` (`APP__REDIS__URL`); окремий result backend **не** вмикаємо:
джерело істини про статус — `api_jobs` (менше TTL-сміття в Redis, простіший
дебаг). Таски реєструються через `include` (модуль `app.tasks.celery_tasks`).

Beat-розклад — **фіксовані константи** (D9): `01:00` витяг TimeCamp+Jira,
`01:30` витяг Tempo; після кожного витягу диспетчер ставить per-user
`reconcile_links`. `02:00` — прибирання `api_jobs` (авто-verify + TTL-видалення,
maintenance без аудиту). Конфігурується лише таймзона (`APP__CELERY__TIMEZONE`,
дефолт `UTC`); усі часи — в UTC.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "sync_work",
    broker=settings.redis.url,
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(
    timezone=settings.celery.timezone,
    enable_utc=True,
    # Статус відстежуємо в api_jobs, тож Celery-результати не зберігаємо.
    result_backend=None,
    task_track_started=True,
    # Не «з'їдати» завдання тихо, якщо брокер недоступний при старті.
    broker_connection_retry_on_startup=True,
    # Підстраховка від loop-binding asyncpg (D3): періодичний ресет воркер-процесу.
    worker_max_tasks_per_child=100,
)

# Beat-розклад: щодоби витяг + реконсиляція (диспетчери ітерують користувачів і
# поважають per-user sync_prefs всередині — capability `async-task-queue`).
celery_app.conf.beat_schedule = {
    "daily-pull-timecamp-jira": {
        "task": "beat.pull_timecamp_jira",
        "schedule": crontab(hour=1, minute=0),
    },
    "daily-pull-tempo": {
        "task": "beat.pull_tempo",
        "schedule": crontab(hour=1, minute=30),
    },
    # Прибирання `api_jobs` після нічних синків: авто-verify старих
    # needs_verification + TTL-видалення термінальних (capability `async-task-queue`).
    "daily-cleanup-api-jobs": {
        "task": "beat.cleanup_api_jobs",
        "schedule": crontab(hour=2, minute=0),
    },
}
