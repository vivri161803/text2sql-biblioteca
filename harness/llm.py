"""Client OpenRouter con limite di frequenza per i modelli gratuiti e nuovi tentativi."""
from __future__ import annotations

import os
import random
import threading
import time

import requests
from dotenv import load_dotenv

from .config import FREE_MIN_INTERVAL_S, PROVIDER_PREFS, ROOT

URL = "https://openrouter.ai/api/v1/chat/completions"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


class DailyLimitError(RuntimeError):
    """Raggiunto il limite giornaliero dei modelli gratuiti: si riprende domani."""


class OpenRouter:
    def __init__(self) -> None:
        load_dotenv(ROOT / ".env")
        self._key = os.environ["API_KEY"]
        self._free_lock = threading.Lock()
        self._free_last = 0.0

    def _throttle(self, model: str) -> None:
        # OpenRouter limita le richieste ai modelli gratuiti a ~20/minuto per account.
        if not model.endswith(":free"):
            return
        with self._free_lock:
            wait = self._free_last + FREE_MIN_INTERVAL_S - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._free_last = time.monotonic()

    def chat(self, model: str, prompt: str, max_tokens: int, retries: int = 6) -> dict:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        if model in PROVIDER_PREFS:
            body["provider"] = PROVIDER_PREFS[model]
        headers = {"Authorization": f"Bearer {self._key}", "X-Title": "Text2SQL eval"}
        last_err = ""
        for attempt in range(retries):
            self._throttle(model)
            try:
                r = requests.post(URL, headers=headers, json=body, timeout=600)
            except requests.RequestException as e:
                last_err = f"rete: {e}"
            else:
                if r.status_code == 200:
                    data = r.json()
                    if "error" in data:
                        last_err = f"errore provider: {data['error']}"
                    else:
                        choice = data["choices"][0]
                        msg = choice.get("message") or {}
                        content = msg.get("content") or ""
                        out = {
                            "content": content,
                            "reasoning": msg.get("reasoning"),
                            "finish_reason": choice.get("finish_reason"),
                            "usage": data.get("usage"),
                            "provider": data.get("provider"),
                        }
                        # Una risposta vuota può essere un errore temporaneo: si riprova una volta.
                        if content.strip() or attempt >= 1:
                            return out
                        last_err = f"risposta vuota (finish_reason={out['finish_reason']})"
                elif r.status_code == 429 and "per-day" in r.text:
                    raise DailyLimitError(r.text[:300])
                elif r.status_code in RETRY_STATUS:
                    last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                else:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            time.sleep(min(90, 4 * 2 ** attempt) + random.random() * 2)
        raise RuntimeError(f"{model}: tentativi esauriti ({last_err})")
