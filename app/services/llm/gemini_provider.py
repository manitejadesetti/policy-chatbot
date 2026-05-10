from app.services.llm.base import LLMProvider
import google.generativeai as generativeai
from google.api_core import exceptions as google_exceptions
import requests as http
from dotenv import load_dotenv
import os

from app.services.rate_limit_tracker import tracker as _tracker

# Ensure .env is loaded from the correct location
load_dotenv("app/.env")

_GEMINI_REST_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _parse_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _check_gemini_status(resp: http.Response, model_name: str) -> None:
    """Raise a descriptive RuntimeError for non-2xx Gemini REST responses."""
    if resp.ok:
        return
    if resp.status_code in (401, 403):
        raise EnvironmentError("Invalid Gemini API key.")
    if resp.status_code == 404:
        raise RuntimeError(f"Model '{model_name}' not found.")
    if resp.status_code == 429:
        raise RuntimeError("Gemini API quota exceeded. Try again later.")
    if resp.status_code == 503:
        raise RuntimeError("Gemini service is currently unavailable.")
    raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:200]}")

class GeminiProvider(LLMProvider):
    # Free-tier rate limits (RPM = requests/min, RPD = requests/day).
    # Source: https://ai.google.dev/gemini-api/docs/rate-limits
    _FREE_TIER_LIMITS: dict[str, dict] = {
        "gemini-2.5-pro":          {"rpm": 5,  "rpd": 25},
        "gemini-2.5-flash":        {"rpm": 10, "rpd": 250},
        "gemini-2.0-flash":        {"rpm": 15, "rpd": 1500},
        "gemini-2.0-flash-lite":   {"rpm": 30, "rpd": 1500},
        "gemini-1.5-flash":        {"rpm": 15, "rpd": 1500},
        "gemini-1.5-flash-8b":     {"rpm": 15, "rpd": 1500},
        "gemini-1.5-pro":          {"rpm": 2,  "rpd": 50},
        "gemini-1.0-pro":          {"rpm": 15, "rpd": 1500},
    }

    def _get_limits(self, model_name: str) -> dict | None:
        """Return known free-tier limits for a model, matched by substring."""
        for key, limits in self._FREE_TIER_LIMITS.items():
            if key in model_name:
                return limits
        return None

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
        generativeai.configure(api_key=self._api_key)

    def list_models(self) -> list[dict]:
        try:
            return [
                {
                    "id": m.name,
                    "display_name": m.display_name,
                    "owned_by": "Google",
                    "context_window": getattr(m, "input_token_limit", None),
                    "max_completion_tokens": getattr(m, "output_token_limit", None),
                    "rate_limits": self._get_limits(m.name),
                }
                for m in generativeai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
        except google_exceptions.PermissionDenied:
            raise EnvironmentError("Invalid Gemini API key.")
        except google_exceptions.ResourceExhausted:
            raise RuntimeError("Gemini API quota exceeded. Try again later.")
        except google_exceptions.ServiceUnavailable:
            raise RuntimeError("Gemini service is currently unavailable.")
        except google_exceptions.GoogleAPIError as e:
            raise RuntimeError(f"Gemini API error: {e}") from e

    def generate_response(self, prompt: str) -> str:
        if not self.model_name:
            raise RuntimeError("No model name specified for generate_response.")
        url = f"{_GEMINI_REST_BASE}/{self.model_name}:generateContent"
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        try:
            resp = http.post(url, json=body, params={"key": self._api_key}, timeout=60)
        except http.exceptions.ConnectionError as e:
            raise RuntimeError(f"Could not connect to Gemini API: {e}") from e
        except http.exceptions.Timeout:
            raise RuntimeError("Gemini API request timed out.")
        _check_gemini_status(resp, self.model_name)

        # Record usage and compute remaining from server-side tracker
        tracker_key = f"gemini:{self.model_name}"
        _tracker.record(tracker_key)
        limits = self._get_limits(self.model_name)
        rpm_limit = limits["rpm"] if limits else None
        rpd_limit = limits["rpd"] if limits else None
        rem = _tracker.remaining(tracker_key, rpm_limit, rpd_limit)
        self.requests_remaining = rem["remaining_rpd"]
        self.requests_limit = rpd_limit
        self.requests_remaining_rpm = rem["remaining_rpm"]

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response format: {data}") from e

    def probe_limits(self) -> dict:
        """Return current remaining limits from the server-side tracker (no extra API call)."""
        if not self.model_name:
            raise RuntimeError("model_name required for probe_limits.")
        tracker_key = f"gemini:{self.model_name}"
        limits = self._get_limits(self.model_name)
        rpm_limit = limits["rpm"] if limits else None
        rpd_limit = limits["rpd"] if limits else None
        rem = _tracker.remaining(tracker_key, rpm_limit, rpd_limit)
        return {
            "remaining": rem["remaining_rpd"],
            "remaining_rpm": rem["remaining_rpm"],
            "limit": rpd_limit,
            "limit_rpm": rpm_limit,
            "used_rpm": rem["used_rpm"],
            "used_rpd": rem["used_rpd"],
            "reset": "resets daily / per minute",
        }