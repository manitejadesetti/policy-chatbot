

from app.services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        # Initialize OpenAI-specific settings here

    def generate_response(self, prompt: str) -> str:
        # Implement OpenAI-specific response generation logic here
        return f"Use Gemini AI I don't have money to spend on this: {prompt}"