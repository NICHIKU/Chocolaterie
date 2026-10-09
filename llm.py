import logging
import os
import random
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Par défaut : Ollama installé sur votre machine (aucun réglage nécessaire)
BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")
BIG_MODEL = os.getenv("LLM_MODEL_BIG", "llama3.2:3b")
SMALL_MODEL = os.getenv("LLM_MODEL_SMALL", "llama3.2:1b")

# Paramètres de robustesse pour la production / debugging
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = float(os.getenv("LLM_RETRY_DELAY_SECONDS", "1"))
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
EXTRA_LATENCY = float(os.getenv("EXTRA_LATENCY", "0"))
FAIL_RATE = float(os.getenv("FAIL_RATE", "0"))


def _normalize_usage(usage):
    if usage is None:
        return 0, 0
    return (
        getattr(usage, "prompt_tokens", 0),
        getattr(usage, "completion_tokens", 0),
    )


def _simulate_failure():
    """Option de test : simulate a temporary failure in dev/tests."""
    if EXTRA_LATENCY > 0:
        time.sleep(EXTRA_LATENCY)
    if FAIL_RATE > 0 and random.random() < FAIL_RATE:
        raise RuntimeError("Panne simulée : 503 service unavailable")


def _model_candidates(requested_model):
    candidates = []
    for model in [requested_model, BIG_MODEL, SMALL_MODEL]:
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def _format_error(exc):
    msg = str(exc)
    if not msg:
        msg = exc.__class__.__name__
    return msg


def chat(model, messages, max_tokens=1500, temperature=None):
    """Retourne (texte, usage). Peut lever une exception en cas d'échec total du modèle.

    La fonction conserve la signature existante, tout en ajoutant :
    - retry automatique
    - fallback vers un autre modèle si le premier échoue
    - logs utiles
    - simulation d'erreur optionnelle pour le debug
    """
    temperature = DEFAULT_TEMPERATURE if temperature is None else float(temperature)
    last_error = None

    for candidate_model in _model_candidates(model):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                _simulate_failure()
                from openai import OpenAI

                client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=180)
                response = client.chat.completions.create(
                    model=candidate_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                usage = response.usage
                content = response.choices[0].message.content
                prompt_tokens, completion_tokens = _normalize_usage(usage)

                logger.info("Réponse LLM OK via modèle %s", candidate_model)
                return content, {
                    "model": candidate_model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                }

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Échec LLM sur %s (tentative %s/%s): %s",
                    candidate_model,
                    attempt,
                    MAX_RETRIES,
                    _format_error(exc),
                )

                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue

        logger.warning("Échec définitif avec le modèle %s. Tentative sur un autre modèle si disponible.", candidate_model)

    if last_error is not None:
        raise RuntimeError(
            f"Impossible d'obtenir une réponse du modèle LLM. Dernière erreur : {_format_error(last_error)}"
        ) from last_error

    raise RuntimeError("Impossible d'obtenir une réponse du modèle LLM.")


