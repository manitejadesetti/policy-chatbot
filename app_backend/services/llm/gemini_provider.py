from app_backend.services.llm.base import LLMProvider
import google.generativeai as generativeai
from google.api_core import exceptions as google_exceptions
import requests as http
import os

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

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response format: {data}") from e

