import json
import logging
import re

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.core.config import settings

logger = logging.getLogger(__name__)


class RetryableOpenRouterError(RuntimeError):
    pass

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string", "description": "Concise explanation of the persisted recommendation."},
        "why_best": {"type": "array", "items": {"type": "string"}},
        "cost_explanation": {"type": "string", "description": "Explain only supplied stored or extrapolated cost evidence."},
        "model_explanation": {"type": "string", "description": "Explain how the two trained models and rules contributed."},
        "tradeoffs": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"option": {"type": "string"}, "benefit": {"type": "string"}, "limitation": {"type": "string"}}, "required": ["option", "benefit", "limitation"]}},
        "optimization_priorities": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "why_best", "cost_explanation", "model_explanation", "tradeoffs", "optimization_priorities", "assumptions"],
}


def _fallback(context: dict, status: str, warning: str | None = None) -> dict:
    winner = context["decision"]["recommended_option"]
    cost = context["decision"]["estimated_cost"]
    content = {
        "summary": f"{winner.replace('_', ' ').title()} has the highest rules-and-model fit score for the supplied workload.",
        "why_best": [item.get("note", "") for item in context["decision"].get("reasons", []) if item.get("note")][:4],
        "cost_explanation": f"The evidence-based USD monthly range is {cost.get('min')} to {cost.get('max')}; the language model does not calculate prices." if cost.get("min") is not None else "No pricing evidence was available, so no cost was invented.",
        "model_explanation": "The LogisticRegression classifier predicts architecture fit and the RandomForestRegressor predicts starting resources. Rules, budget fit, and stored pricing produce the final rank.",
        "tradeoffs": [{"option": row["display_name"], "benefit": f"Fit score {row['score']}/100", "limitation": (row.get("weaknesses") or ["Validate with production monitoring."])[0]} for row in context["decision"].get("alternatives", [])],
        "optimization_priorities": [item["title"] for item in context.get("cost_optimization", {}).get("actions", [])],
        "assumptions": context["decision"].get("assumptions", []),
    }
    return {"status": status, "source": "DETERMINISTIC_TEMPLATE", "model": None, "configured_model": settings.openrouter_model, "routed_model": None, "content": content, "usage": {}, "warning": warning}


def _message_text(data: dict) -> str:
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text = "".join(str(item.get("text") or item.get("content") or "") for item in content if isinstance(item, dict))
        if text:
            return text
    raise ValueError("OpenRouter response did not contain assistant text")


def _json_content(text: str) -> dict:
    cleaned = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return json.loads(match.group(1) if match else cleaned)


@retry(retry=retry_if_exception_type((RetryableOpenRouterError,httpx.TimeoutException,httpx.NetworkError)),stop=stop_after_attempt(settings.openrouter_retry_attempts),wait=wait_exponential_jitter(initial=1,max=5),reraise=True)
def _send(request: dict, headers: dict) -> httpx.Response:
    response=httpx.post(f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",headers=headers,json=request,timeout=settings.openrouter_timeout_seconds)
    if response.status_code in {408,409,429,500,502,503,504}:
        raise RetryableOpenRouterError(f"OpenRouter temporarily unavailable ({response.status_code})")
    response.raise_for_status()
    return response


def explain(context: dict) -> dict:
    """Explain immutable decision evidence through OpenRouter; never recalculate it."""
    if not settings.llm_enabled:
        return _fallback(context, "DISABLED", "LLM_ENABLED is false; deterministic explanation used.")
    if not settings.openrouter_api_key:
        return _fallback(context, "NOT_CONFIGURED", "OPENROUTER_API_KEY is not configured; deterministic explanation used.")
    system = (
        "You explain a completed web-hosting recommendation. Use only supplied JSON facts. "
        "Never change ranks, scores, resource sizes, prices, savings, or confidence. Never invent a provider price. "
        "Explain how the LogisticRegression classifier, RandomForestRegressor resource model, deterministic rules, stored pricing, and budget produced the decision. State uncertainty plainly."
    )
    request = {
        "model": settings.openrouter_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(context, separators=(",", ":"), default=str)}],
        "max_tokens": settings.openrouter_max_tokens,
        "temperature": 0.2,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "hosting_decision_explanation", "strict": True, "schema": SCHEMA}},
        "provider": {"require_parameters": True, "allow_fallbacks": True},
    }
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json", "X-OpenRouter-Title": settings.openrouter_app_title}
    if settings.openrouter_http_referer or settings.frontend_url:
        headers["HTTP-Referer"] = settings.openrouter_http_referer or settings.frontend_url
    try:
        response = _send(request,headers)
        data = response.json()
        content = _json_content(_message_text(data))
        return {"status": "GENERATED", "source": "OPENROUTER_CHAT_COMPLETIONS", "model": settings.openrouter_model, "configured_model": settings.openrouter_model, "routed_model": data.get("model"), "content": content, "usage": data.get("usage") or {}, "warning": None}
    except Exception as exc:
        logger.warning("OpenRouter explanation failed; deterministic explanation retained", extra={"error_type": type(exc).__name__})
        return _fallback(context, "FAILED", "OpenRouter explanation was unavailable; deterministic explanation used.")
