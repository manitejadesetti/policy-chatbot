from fastapi import APIRouter, HTTPException, Query

from app.services.llm.grok_provider import GroqProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.rag_service import RAGService, ModelNotFoundError, QuotaExceededError, GenerationError

_PROVIDERS = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
}

router = APIRouter()

try:
    _rag = RAGService()
except EnvironmentError as e:
    _rag = None
    _rag_init_error = str(e)
else:
    _rag_init_error = None


@router.get("/providers", tags=["chat"])
async def list_providers():
    """Return the list of supported LLM providers."""
    return {"providers": list(_PROVIDERS.keys())}


@router.get("/models", tags=["chat"])
async def list_models(provider: str = Query(default="groq", description="LLM provider name")):
    """Return available chat models for the given provider."""
    provider_key = provider.lower()
    if provider_key not in _PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{provider}'. Supported: {', '.join(_PROVIDERS)}.",
        )
    try:
        models = _PROVIDERS[provider_key]().list_models()
        return {"models": models}
    except EnvironmentError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/limits", tags=["chat"])
async def get_limits(
    provider: str = Query(default="groq", description="LLM provider name"),
    model: str = Query(..., description="Model ID"),
):
    """Probe the provider API and return current remaining rate-limit info."""
    provider_key = provider.lower()
    if provider_key not in _PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{provider}'. Supported: {', '.join(_PROVIDERS)}.",
        )
    try:
        limits = _PROVIDERS[provider_key](model_name=model).probe_limits()
        return limits
    except EnvironmentError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/send", tags=["chat"])
async def chat_endpoint(request: dict):
    if _rag is None:
        raise HTTPException(status_code=503, detail=_rag_init_error)

    user_message = request.get("message", "")
    if not user_message:
        raise HTTPException(status_code=422, detail="message field is required.")

    model_name = request.get("model") or None
    provider_key = (request.get("provider") or "groq").lower()

    if provider_key not in _PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{provider_key}'. Supported: {', '.join(_PROVIDERS)}.",
        )

    try:
        result = _rag.generate_response(
            user_message,
            model_name=model_name,
            provider_class=_PROVIDERS[provider_key],
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except QuotaExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except GenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "reply": result["reply"],
        "requests_remaining": result["requests_remaining"],
        "requests_limit": result["requests_limit"],
        "remaining_rpm": result["remaining_rpm"],
    }
