"""Entry point for the HTTP API.

Run with:

    poetry run python run_api.py

or, for hot reload during development:

    poetry run uvicorn src.api.app:app --reload
"""
import uvicorn

from src.config import settings


def main() -> None:
    settings.require_api_ready()
    uvicorn.run(
        "src.api.app:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
