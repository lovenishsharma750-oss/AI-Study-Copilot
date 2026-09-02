"""Environment-backed configuration for the backend application."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

# Loading is intentionally silent. Values are never logged by this module.
load_dotenv(ENV_FILE)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


@dataclass(frozen=True)
class SupabaseSettings:
    """Required Supabase configuration values."""

    url: str
    key: str


def get_supabase_settings() -> SupabaseSettings:
    """Return required Supabase settings or raise a safe, actionable error."""
    missing = [
        name
        for name, value in (("SUPABASE_URL", SUPABASE_URL), ("SUPABASE_KEY", SUPABASE_KEY))
        if not value
    ]
    if missing:
        missing_names = ", ".join(missing)
        raise RuntimeError(
            f"Missing required Supabase configuration: {missing_names}. "
            "Set the values in the project .env file."
        )

    return SupabaseSettings(url=SUPABASE_URL, key=SUPABASE_KEY)
