"""Environment configuration helpers for the RosterIQ backend."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_environment() -> None:
    """Load environment variables from the project .env file when present."""

    load_dotenv(dotenv_path=ENV_FILE, override=False)


load_environment()
