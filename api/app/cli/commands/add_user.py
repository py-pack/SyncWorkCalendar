import asyncio
from getpass import getpass

from app.api.auth import hash_password
from app.core import get_async_asession
from app.dao import APIUserDAO


def register(subparsers):
    parser = subparsers.add_parser("add_user", help="Add API user")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--worker-key", dest="worker_key")

    def handle(args):
        asyncio.run(_handle(args))

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
