import httpx
import logging
import time
from app.config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
TIMEOUT = httpx.Timeout(15.0, connect=2.0)

def explain(event: dict, anomalies: list[str]) -> str:
    prompt = f"""
    You are a financial transaction analyst.

    Transaction:
    Amount in minor units: {event["amountMinor"]}
    Currency: {event["currency"]}
    Balance after: {event["balanceAfterMinor"]}

    Detected anomalies:
    {anomalies}

    Explain why these findings deserve review
    in 2-3 sentences.

    Do not claim fraud has occurred.
    Do not invent additional transaction history.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try: 
            response = httpx.post(
                f"{OLLAMA_URL}/api/generate",
                    json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=TIMEOUT
            )

            response.raise_for_status()
            return response.json()["response"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning("Ollama rejected request: %s", e)
                return None
            logger.warning("Ollama error (attempt %d): %s", attempt, e)
        except httpx.TransportError as e:
            logger.warning("Ollama unreachable (attempt %d): %s", attempt, e)

        if attempt < MAX_ATTEMPTS:
            time.sleep(0.5* attempt)
    return None

