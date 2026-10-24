import httpx
from app.config import OLLAMA_URL, OLLAMA_MODEL

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

    # TODO: shorter timeout + retry; consumer must keep working when Ollama is down (optional dependency)
    response = httpx.post(
        f"{OLLAMA_URL}/api/generate",
            json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        },
        timeout=60.0
    )

    response.raise_for_status()
    return response.json()["response"]