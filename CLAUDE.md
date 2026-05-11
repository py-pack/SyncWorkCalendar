# CLAUDE.md

## Memory Bank

На початку **кожної задачі** прочитай усі Markdown-файли в
`docs/memory-bank/` перед тим, як вносити будь-які зміни. Це канонічне джерело
загального контексту цього репозиторію (огляд, архітектура, технічний стек,
поточний фокус, рішення, прогрес).

Файли:
- `docs/memory-bank/projectbrief.md`
- `docs/memory-bank/productContext.md`
- `docs/memory-bank/activeContext.md`
- `docs/memory-bank/systemPatterns.md`
- `docs/memory-bank/techContext.md`
- `docs/memory-bank/progress.md`
- `docs/memory-bank/decisinLog.md`

Для ініціалізації, оновлення або аудиту Memory Bank використовуй скіл
`memory-bank-manager`. Уся загальна інформація про проект має жити в
Memory Bank — не дублюй її в `CLAUDE.md`, `AGENTS.md` чи інших файлах
інструкцій. Сюди додавай лише операційні нюанси, специфічні для роботи Claude
Code, які не належать Memory Bank.
