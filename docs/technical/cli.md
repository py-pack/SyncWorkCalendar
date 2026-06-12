# CLI-модуль (`src/cli`)

Технічна довідка по консольному інтерфейсу застосунку. `src/cli` — це
**Artisan-style CLI** на `argparse` з **авто-реєстрацією команд**: кожна
команда живе окремим файлом у `src/cli/commands/`, а модуль сам знаходить
і підключає її до парсера. Зразок узгоджений із `dom-ex.bot`
(`activeContext.md`).

Призначення — операційні дії над застосунком, які не належать ні HTTP-шару
(`src/api`), ні разовим скриптам (`main.py`/`main.ipynb`). Поточна
команда — `add_user` (заводить запис `api_users`), що знімає попередню
залежність від ручного `INSERT` першого користувача.

## 1. Структура модуля

```
src/cli/
├── __init__.py            # порожній (маркер пакета)
├── __main__.py            # точка входу: будує парсер, запускає команду
└── commands/
    ├── __init__.py        # register_all() — авто-дискавері команд
    └── add_user.py        # одна команда = один файл із register()
```

Запуск через `python -m src.cli <command>` — Python виконує
`src/cli/__main__.py`.

## 2. Точка входу — `__main__.py`

```python
def main():
    parser = argparse.ArgumentParser(description="Artisan-style CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_all(subparsers)              # підключає всі команди

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)                   # делегує в handler команди
    else:
        parser.print_help()
```

Ключові моменти:

- `subparsers` із `required=True` — без під-команди `argparse` сам видасть
  помилку і `usage`.
- Кожна команда привʼязує свій callback через
  `parser.set_defaults(func=...)`. `main()` не знає назв команд — він просто
  викликає `args.func(args)`, якщо атрибут є.
- Гілка `else` (`print_help`) — підстраховка; за `required=True`
  на практиці майже недосяжна.

## 3. Авто-реєстрація — `commands/__init__.py`

`register_all(subparsers)` сканує теку `commands/` й підключає кожен
командний модуль:

```python
def register_all(subparsers):
    commands_dir = pathlib.Path(__file__).parent

    for file in os.listdir(commands_dir):
        if file.endswith(".py") and not file.startswith(("_", "__")):
            module_name = file[:-3]                  # add_user.py → add_user
            full_module = f"{__name__}.{module_name}"

            module = importlib.import_module(full_module)
            if hasattr(module, "register"):
                module.register(subparsers)
```

Контракт авто-дискавері:

- Береться будь-який `*.py`, що **не** починається з `_` чи `__`
  (тобто `__init__.py` та приватні хелпери ігноруються).
- Імʼя файлу = імʼя команди (`add_user.py` → під-команда `add_user`).
- Модуль підключається лише якщо в ньому є функція `register` — інакше
  тихо пропускається (без помилки).
- Порядок залежить від `os.listdir` (порядок ФС, не сортований). Для
  `argparse` це не критично — під-команди незалежні.

> Наслідок: **щоб додати команду, достатньо покласти файл** у
> `commands/` — правити `__main__.py` чи реєстр не треба.

## 4. Контракт команди

Кожен командний файл експонує функцію `register(subparsers)`, яка:

1. створює свій під-парсер (`subparsers.add_parser(<name>, ...)`),
2. описує аргументи (`add_argument`),
3. привʼязує handler через `parser.set_defaults(func=<callable>)`.

`func` отримує розпарсений `argparse.Namespace` і виконує роботу.

## 5. Команда `add_user`

Заводить користувача HTTP API (`api_users`) з bcrypt-хешем пароля.

```python
def register(subparsers):
    parser = subparsers.add_parser("add_user", help="Add API user")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--worker-key", dest="worker_key")

    def handle(args):
        asyncio.run(_handle(args))        # async → sync міст

    parser.set_defaults(func=handle)


async def _handle(args):
    username = args.username or input("Username: ")
    password = args.password or getpass("Password: ")
    worker_key = args.worker_key

    async with get_async_asession() as db:
        if await APIUserDAO.get_by_username(db, username):
            print(f"❌ User '{username}' already exists")
            return

        user = await APIUserDAO.create_user(
            db,
            username=username,
            password_hash=hash_password(password),
            worker_key=worker_key,
        )
        await db.flush()
        print(f"✅ User {user.username} — created with ID: {user.id}")
```

Поведінка та деталі:

- **Інтерактивний фолбек.** `--username`/`--password` опційні; без них
  команда питає `input()` / `getpass()` (пароль не відображається в
  терміналі).
- **`--worker-key`** мапиться на `args.worker_key` (через `dest=`).
  Це Jira key користувача; опційний (`NULL` дозволено). Без нього
  ламаються лише worklog-sync endpoint-и — деталі в
  [api-reference.md](api-reference.md) §2.
- **Async-міст.** `handle` загортає `asyncio.run(_handle(...))`, бо
  `argparse`-callback синхронний, а DAO/сесія — async.
- **Ідемпотентність по username.** Перед вставкою — перевірка
  `get_by_username`; дубль не створюється, друкується `❌` і вихід.
- **Хешування.** `hash_password` — прямий `bcrypt` із `src/api/auth.py`
  (формат `$2b$`); `passlib` прибрано через несумісність із `bcrypt` 5.x
  на Python 3.14 (`decisinLog.md` → D-011).
- **Транзакція.** `get_async_asession()` робить **commit на нормальному
  виході** і **rollback при винятку** (`src/core/db_helper.py`). Тому
  `add_user` не викликає `commit` явно. `await db.flush()` потрібен лише
  щоб БД присвоїла `user.id` до друку (commit станеться вже на виході з
  контексту).

## 6. Як запускати

```sh
# повна форма
uv run python -m src.cli add_user

# з аргументами (без інтерактивних запитів)
uv run python -m src.cli add_user --username admin --worker-key TEAM-1
# пароль спитає getpass, якщо не передати --password

# шорткати Makefile
make add-user                       # = python -m src.cli add_user
make cli ARGS="add_user --username john"
```

`Makefile` тримає тонкі обгортки поверх `uv run` (`techContext.md`):
`add-user` — фіксований шорткат, `cli` — проброс довільних `ARGS`.

## 7. Як додати нову команду

1. Створити `src/cli/commands/<command_name>.py` (імʼя файлу = імʼя
   під-команди; без префікса `_`).
2. Реалізувати `register(subparsers)`: `add_parser`, аргументи,
   `set_defaults(func=...)`.
3. Якщо команда async — загорнути handler у `asyncio.run(...)`, як в
   `add_user`.
4. Для роботи з БД — брати сесію через `get_async_asession()` (commit/
   rollback автоматичні); не комітити вручну.

Реєстр і `__main__.py` чіпати не потрібно — авто-дискавері підхопить файл
на наступному запуску.

Мінімальний шаблон:

```python
def register(subparsers):
    parser = subparsers.add_parser("my_command", help="...")
    parser.add_argument("--foo")
    parser.set_defaults(func=lambda args: print(args.foo))
```

## 8. Межі та звʼязки

- CLI — **операційний інструмент**, не другий застосунок: він повторно
  використовує `src/dao`, `src/core`, `src/api.auth`. Бізнес-логіку
  тримаємо в цих шарах, а не в командах.
- Управління користувачами ширше за `add_user` (list/deactivate/
  set-password) — поза поточним кодом; план — майбутня зміна
  `add-user-management-cli` (`api-reference.md` §7).
- Legacy-точки входу (`main.py`, `main.ipynb`) лишаються окремо —
  це разові sync-скрипти, не частина CLI-реєстру (`techContext.md`).
