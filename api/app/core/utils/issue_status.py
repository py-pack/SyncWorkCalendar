"""Похідна «активність» Jira-задачі за вільним рядком `status`.

`JRIssue.status` — локалізований вільний рядок (кастомні воркфлоу), тож
«завершеність» визначаємо звіркою з константним сетом «done»-статусів
(EN+UK). Сет навмисно винесено в одну константу для легкого розширення;
прапор лише візуальний (тьмяність у UI), нічого не блокує (D3).
"""

# «Завершені» статуси (lower-case, trimmed): EN + локалізовані UK-відповідники.
DONE_STATUSES: frozenset[str] = frozenset(
    {
        "done",
        "closed",
        "resolved",
        "cancelled",
        "canceled",
        "won't do",
        "wont do",
        "готово",
        "закрито",
        "виконано",
        "скасовано",
        "вирішено",
    }
)


def is_issue_active(status: str | None) -> bool:
    """`True`, якщо статус **не** в «done»-сеті.

    Порівняння case-insensitive + trim. `None`/порожній статус вважаємо
    активним (немає підстав тьмянити).
    """
    if status is None:
        return True
    return status.strip().lower() not in DONE_STATUSES
