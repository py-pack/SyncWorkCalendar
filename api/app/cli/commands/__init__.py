import importlib
import os
import pathlib


def register_all(subparsers):
    commands_dir = pathlib.Path(__file__).parent

    # Проходимось по всім файлам у директорії й парсимо назви файлів,
    # по яким пізніше зареєстроємо модулі
    for file in os.listdir(commands_dir):
        if file.endswith(".py") and not file.startswith(("_", "__")):
            module_name = file[:-3]  # add_user.py → add_user
            full_module = f"{__name__}.{module_name}"

            # Створюємо модуль на льоту й регаємо його
            module = importlib.import_module(full_module)
            if hasattr(module, "register"):
                # ініціюємо модуль команди й привязуємо до argparse
                module.register(subparsers)
