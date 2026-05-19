from app_backend.services.llm.base import LLMProvider

from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError
import os


class LocalLLMProvider(LLMProvider):

    def __init__(self, model_name: str = None):
        base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
        api_key = os.getenv("LOCAL_LLM_API_KEY", "not-needed")
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        if not model_name:
            model_name = os.getenv("LOCAL_LLM_MODEL", "llama3.2")
        super().__init__(model_name)

    def list_models(self) -> list[dict]:
        try:
            response = self.client.models.list()
            return [
                {
                    "id": m.id,
                    "display_name": m.id,
                }
                for m in response.data
            ]
        except APIConnectionError as e:
            raise RuntimeError(
                f"Could not connect to local LLM at {self.client.base_url}. "
                f"Make sure Ollama (or another server) is running. Details: {e}"
            ) from e
        except APIStatusError as e:
            raise RuntimeError(f"Local LLM API error {e.status_code}: {e.message}") from e

    def load_model(self, model_name: str):
        # Validate that the model is available on the local server
        try:
            self.client.models.retrieve(model_name)
        except APIConnectionError as e:
            raise RuntimeError(
                f"Could not connect to local LLM at {self.client.base_url}. "
                f"Make sure Ollama (or another server) is running. Details: {e}"
            ) from e
        except APIStatusError as e:
            if e.status_code == 404:
                raise ValueError(
                    f"Model '{model_name}' not found on the local LLM server. "
                    f"Run 'ollama pull {model_name}' to install it."
                ) from e
            raise RuntimeError(f"Local LLM API error {e.status_code}: {e.message}") from e

    def generate_response(self, prompt: str) -> str:
        if not self.model_name:
            raise RuntimeError("No model name specified for generate_response.")
        try:
            raw = self.client.with_raw_response.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            completion = raw.parse()
            return completion.choices[0].message.content
        except APIConnectionError as e:
            raise RuntimeError(
                f"Could not connect to local LLM at {self.client.base_url}. "
                f"Make sure Ollama (or another server) is running. Details: {e}"
            ) from e
        except RateLimitError:
            raise RuntimeError("Local LLM rate limit exceeded. Try again later.")
        except APIStatusError as e:
            raise RuntimeError(f"Local LLM API error {e.status_code}: {e.message}") from e