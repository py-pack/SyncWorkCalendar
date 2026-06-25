"""Per-user перемикачі автосинку (`api_users.sync_prefs`).

Один JSONB-стовпець із булевими ключами замість N колонок (D7). Авторитетне
джерело для Celery-тасок і beat. Дефолт усього — **`false`** (автосинк opt-in):
відсутність колонки (`NULL`) чи окремого ключа читається як вимкнено.
"""

# Канонічний перелік перемикачів. Порядок зберігаємо стабільним (відповідь API).
SYNC_PREF_KEYS: tuple[str, ...] = (
    "auto_timecamp_pull",  # плановий витяг TimeCamp-записів (глобальний)
    "auto_jira_pull",  # плановий витяг Jira-задач (глобальний)
    "auto_tempo_pull",  # плановий витяг Tempo-worklog-ів (per-user)
    "auto_linking",  # реконсиляція матчів TimeCamp↔Tempo (per-user)
    "auto_push_tempo",  # авто-створення/оновлення Tempo-відмітки (per-user)
)


def normalize_sync_prefs(raw: dict | None) -> dict[str, bool]:
    """`sync_prefs` із БД (може бути `None`) → повний об'єкт із дефолтами `false`."""
    raw = raw or {}
    return {key: bool(raw.get(key, False)) for key in SYNC_PREF_KEYS}


def merge_sync_prefs(
    current: dict | None, patch: dict[str, bool]
) -> dict[str, bool]:
    """Часткове злиття `patch` у наявні `sync_prefs`; результат — повний об'єкт."""
    merged = normalize_sync_prefs(current)
    for key, value in patch.items():
        if key in SYNC_PREF_KEYS and value is not None:
            merged[key] = bool(value)
    return merged
