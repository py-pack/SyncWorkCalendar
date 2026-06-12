"""Entry point for the HTTP API.

Run from the ``api/`` directory with:

    uv run python run_api.py

or, for hot reload during development:

    uv run uvicorn app.api.app:app --reload
"""
import uvicorn

from app.config import settings


def main() -> None:
    settings.require_api_ready()
    uvicorn.run(
        "app.api.app:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
