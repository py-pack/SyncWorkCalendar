## ADDED Requirements

### Requirement: Дворівнева розкладка інструкцій агентів

Інструкції для агентів SHALL бути дворівневими: спільний контекст лишається
на корені, а кожна тека `api/` і `front/` має власні `AGENTS.md` та
`CLAUDE.md` під свій стек.

#### Scenario: Per-folder файли інструкцій існують

- **WHEN** перевіряється структура після зміни
- **THEN** присутні `api/AGENTS.md`, `api/CLAUDE.md`,
  `front/AGENTS.md`, `front/CLAUDE.md`

#### Scenario: Кореневі інструкції роутять у підтеки

- **WHEN** агент читає кореневі `AGENTS.md`/`CLAUDE.md`
- **THEN** вони вказують читати Memory Bank і направляють у відповідний
  `api/` або `front/` файл інструкцій залежно від області роботи
- **AND** не дублюють загальний контекст, який уже є в Memory Bank

#### Scenario: Per-folder інструкції відповідають стеку

- **WHEN** читається `api/AGENTS.md` і `front/AGENTS.md`
- **THEN** api-файл описує Python/`uv`/Alembic/FastAPI-нюанси, а
  front-файл — Vue/TypeScript/Vite-нюанси

### Requirement: Локальні вказівники на скіли per-folder

Локальні скіли per-folder SHALL бути реалізовані як **легкі вказівники** —
короткі нотатки/посилання у `api/AGENTS.md`/`CLAUDE.md` та
`front/AGENTS.md`/`CLAUDE.md` на потрібні глобальні скіли плюс стек-специфіка.
Повноцінних директорій `.claude/skills/` усередині `api/`/`front/` SHALL NOT
бути. Загальні (project-wide) скіли SHALL лишатися спільними на корені.

#### Scenario: Вказівники присутні, без повноцінних скіл-директорій

- **WHEN** перевіряється структура `api/` і `front/`
- **THEN** їхні `AGENTS.md`/`CLAUDE.md` містять легкі вказівники на релевантні
  скіли та стек-специфіку
- **AND** усередині `api/`/`front/` немає директорій `.claude/skills/`

#### Scenario: Зміна конвенції зафіксована

- **WHEN** читається `docs/memory-bank/decisinLog.md`
- **THEN** там є запис, що попереднє правило "скіли глобальні, локальних
  копій не тримаємо" свідомо переглянуто на користь per-folder легких
  вказівників, із причиною
