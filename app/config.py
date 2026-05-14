
import os
from dotenv import load_dotenv

_ENV_PATH = os.path.expanduser("~/.policy-chatbot.env")

_ENV_FALLBACK = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    ".env",
)

# Load dotenv (idempotent – calling multiple times is safe)
load_dotenv(_ENV_PATH)
load_dotenv(_ENV_FALLBACK)


def get_env(key: str, default: str | None = None) -> str | None:
    """Retrieve an environment variable."""
    return os.getenv(key, default)
