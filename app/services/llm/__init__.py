


from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider(provider_name: str, model_name: str):
	"""
	Factory function to get the appropriate LLM provider.
	"""
	providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider
    }
	provider_name = provider_name.lower()
	provider = providers.get(provider_name)
	if provider:
		return provider(model_name)
	else:
		raise ValueError(f"Unknown provider: {provider_name}")
