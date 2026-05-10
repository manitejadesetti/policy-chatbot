from app.services.llm.base import LLMProvider

from groq import Groq, APIConnectionError, APIStatusError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
import os


# Ensure .env is loaded from the correct location
load_dotenv("app/.env")


class GroqProvider(LLMProvider):
    def __init__(self, model_name: str = None):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
        self.client = Groq(api_key=api_key)
        super().__init__(model_name)

    # Model ID substrings that indicate non-chat models (audio, TTS, guard/classification)
    _NON_CHAT_PATTERNS = ("whisper", "prompt-guard", "orpheus")

    def list_models(self) -> list[dict]:
        try:
            response = self.client.models.list()
            return [
                {
                    "id": m.id,
                    "display_name": m.id,
                    "owned_by": m.owned_by,
                    "context_window": m.context_window,
                    "max_completion_tokens": m.max_completion_tokens,
                }
                for m in response.data
                if m.active and not any(p in m.id for p in self._NON_CHAT_PATTERNS)
            ]
        except AuthenticationError:
            raise EnvironmentError("Invalid Groq API key.")
        except RateLimitError:
            raise RuntimeError("Groq API rate limit exceeded. Try again later.")
        except APIConnectionError as e:
            raise RuntimeError(f"Could not connect to Groq API: {e}") from e
        except APIStatusError as e:
            raise RuntimeError(f"Groq API error {e.status_code}: {e.message}") from e
        
    def load_model(self, model_name: str):
        # Groq's client doesn't require pre-loading models, but we can validate the model name here
        try:
            model = self.client.models.retrieve(model_name)
            if any(p in model.id for p in self._NON_CHAT_PATTERNS):
                raise ValueError(f"Model '{model_name}' does not support chat completion.")
            return model
        except AuthenticationError:
            raise EnvironmentError("Invalid Groq API key.")
        except RateLimitError:
            raise RuntimeError("Groq API rate limit exceeded. Try again later.")
        except APIConnectionError as e:
            raise RuntimeError(f"Could not connect to Groq API: {e}") from e
        except APIStatusError as e:
            if e.status_code == 404:
                raise ValueError(f"Model '{model_name}' not found.") from e
            else:
                raise RuntimeError(f"Groq API error {e.status_code}: {e.message}") from e

    def generate_response(self, prompt: str) -> str:
        if not self.model_name:
            raise RuntimeError("No model name specified for generate_response.")
        try:
            raw = self.client.with_raw_response.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            completion = raw.parse()
            remaining = raw.headers.get("x-ratelimit-remaining-requests")
            limit = raw.headers.get("x-ratelimit-limit-requests")
            self.requests_remaining = int(remaining) if remaining is not None else None
            self.requests_limit = int(limit) if limit is not None else None
            return completion.choices[0].message.content
        except AuthenticationError:
            raise EnvironmentError("Invalid Groq API key.")
        except RateLimitError:
            raise RuntimeError("Groq API rate limit exceeded. Try again later.")
        except APIConnectionError as e:
            raise RuntimeError(f"Could not connect to Groq API: {e}") from e
        except APIStatusError as e:
            raise RuntimeError(f"Groq API error {e.status_code}: {e.message}") from e

    def probe_limits(self) -> dict:
        """Make a minimal chat completion call to read current rate-limit headers."""
        if not self.model_name:
            raise RuntimeError("model_name required for probe_limits.")
        try:
            raw = self.client.with_raw_response.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "."}],
                max_tokens=1,
            )
            return {
                "remaining": int(v) if (v := raw.headers.get("x-ratelimit-remaining-requests")) else None,
                "limit": int(v) if (v := raw.headers.get("x-ratelimit-limit-requests")) else None,
                "reset": raw.headers.get("x-ratelimit-reset-requests"),
            }
        except RateLimitError:
            raise RuntimeError("Groq API rate limit exceeded. Try again later.")
        except AuthenticationError:
            raise EnvironmentError("Invalid Groq API key.")
        except (APIConnectionError, APIStatusError) as e:
            raise RuntimeError(str(e)) from e