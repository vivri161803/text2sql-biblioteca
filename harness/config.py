"""Configurazione dell'esperimento."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
DATASET_PATH = ROOT / "dataset" / "dataset.json"
RESULTS_DIR = ROOT / "results"
GENERATIONS_PATH = RESULTS_DIR / "generations.jsonl"
JUDGMENTS_PATH = RESULTS_DIR / "judgments.jsonl"

# Modelli valutati (f), tutti gratuiti su OpenRouter.
MODELS = {
    "piccolo": "nvidia/nemotron-3.5-lightning:free",
    # Versione a pagamento (~0,05 $ in tutto): quella gratuita passa solo da Google AI Studio.
    "medio": "google/gemma-4-31b-it",
    "grande": "nvidia/nemotron-3-ultra-550b-a55b:free",
}

# Preferenze di instradamento OpenRouter per modello.
# Per Gemma si escludono i fornitori Google, così non viene usata la chiave Google
# collegata all'account (bloccata perché segnalata come trapelata).
PROVIDER_PREFS = {
    "google/gemma-4-31b-it": {"ignore": ["google-ai-studio", "google-vertex"]},
}

# Giudice (g): famiglia diversa dai modelli valutati.
JUDGE_MODEL = "google/gemini-3.1-flash-lite"

# Metodi di prompting: file in prompts/ -> etichetta usata nei report.
PROMPTS = {
    "p1_schema": "1 - Schema",
    "p2_schema_descrizioni": "2 - Schema + descrizioni",
    "p3_cot": "3 - + CoT",
    "p4_fewshot": "4 - + Few-shot",
}

GEN_MAX_TOKENS = 8000      # margine per i modelli che ragionano prima di rispondere
JUDGE_MAX_TOKENS = 1000
FREE_MIN_INTERVAL_S = 3.2  # ~19 richieste/minuto in totale sui modelli gratuiti
