"""Harness di valutazione Text2SQL.

Fase 1 (gen):   x -> f -> f(x) per ogni modello x prompt x caso.
Fase 2 (judge): g(f(x), y) = giudizio 0/1 + motivazione, con i risultati
                dell'esecuzione sul database di prova come prova a supporto.

Ogni risposta viene salvata subito in results/*.jsonl: rilanciando lo script
si riprende da dove ci si era fermati (utile per i limiti dei modelli gratuiti).

Esempi:
    python -m harness.run                       # tutto
    python -m harness.run --cases P0-1,P3-1     # solo alcune domande
    python -m harness.run --models piccolo --prompts p1_schema --phase gen
"""
from __future__ import annotations

import argparse
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import (DATASET_PATH, GEN_MAX_TOKENS, GENERATIONS_PATH, JUDGE_MAX_TOKENS,
                     JUDGE_MODEL, JUDGMENTS_PATH, MODELS, PROMPTS, PROMPTS_DIR, RESULTS_DIR)
from .db_utils import compare, format_result, has_top_level_order_by, run_query
from .llm import DailyLimitError, OpenRouter

_write_lock = threading.Lock()


# ---------------------------------------------------------------- dati

def load_cases() -> list[dict]:
    """Un caso per ogni coppia (domanda, strategia)."""
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    cases = []
    for q in data["domande"]:
        for strategia, sql in q["soluzioni"].items():
            cases.append({
                "case_id": q["id"] if strategia == "-" else f"{q['id']}/{strategia}",
                "question_id": q["id"],
                "pattern": q["pattern"],
                "pattern_nome": data["pattern"][str(q["pattern"])],
                "strategia": None if strategia == "-" else strategia,
                "domanda": q["domanda"],
                "soluzione_attesa": sql,
            })
    return cases


def build_prompt(prompt_key: str, case: dict, strategie: dict) -> str:
    template = (PROMPTS_DIR / f"{prompt_key}.txt").read_text(encoding="utf-8")
    text = template.replace("{{DOMANDA}}", case["domanda"])
    if case["strategia"]:
        return text.replace("{{STRATEGIA}}", strategie[case["strategia"]])
    return text.replace("{{STRATEGIA}}\n", "")


def extract_sql(text: str) -> str:
    """Prende l'ultimo blocco ```sql``` della risposta; in mancanza, il testo da SELECT/WITH in poi."""
    blocks = re.findall(r"```[ \t]*(?:sql|SQL)?[ \t]*\n(.*?)```", text, re.S)
    if blocks:
        return blocks[-1].strip()
    m = re.search(r"^\s*(WITH|SELECT)\b.*", text, re.S | re.I | re.M)
    return (m.group(0) if m else text).strip()


def load_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path, record: dict) -> None:
    with _write_lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def key(r: dict) -> tuple:
    return (r["modello_taglia"], r["prompt"], r["case_id"])


# ---------------------------------------------------------------- fase 1: generazione

def generate(client: OpenRouter, size: str, prompt_key: str, case: dict, strategie: dict) -> dict:
    prompt = build_prompt(prompt_key, case, strategie)
    try:
        resp = client.chat(MODELS[size], prompt, GEN_MAX_TOKENS)
        error = None
    except DailyLimitError:
        raise
    except Exception as e:
        resp, error = {"content": "", "reasoning": None, "finish_reason": None, "usage": None}, str(e)
    return {
        "modello_taglia": size, "modello": MODELS[size], "prompt": prompt_key, **case,
        "prompt_testo": prompt,
        "risposta": resp["content"],
        "ragionamento_modello": resp.get("reasoning"),
        "finish_reason": resp.get("finish_reason"),
        "usage": resp.get("usage"),
        "errore_chiamata": error,
        "sql_generato": extract_sql(resp["content"]) if resp["content"] else "",
    }


def run_generation(client, sizes, prompt_keys, cases, workers: int) -> None:
    strategie = json.loads((PROMPTS_DIR / "strategie.json").read_text(encoding="utf-8"))
    # Una generazione è valida solo se riuscita e fatta con il modello attualmente configurato.
    done = {key(r) for r in load_jsonl(GENERATIONS_PATH)
            if not r.get("errore_chiamata") and r["modello"] == MODELS[r["modello_taglia"]]}
    todo = [(s, p, c) for s in sizes for p in prompt_keys for c in cases
            if (s, p, c["case_id"]) not in done]
    print(f"[gen] da fare: {len(todo)} (già fatte: {len(done)})")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate, client, s, p, c, strategie): (s, p, c["case_id"]) for s, p, c in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                rec = fut.result()
            except DailyLimitError as e:
                print(f"[gen] limite giornaliero raggiunto: {e}. Rilancia domani per continuare.")
                pool.shutdown(cancel_futures=True)
                return
            append_jsonl(GENERATIONS_PATH, rec)
            flag = "ERRORE " + rec["errore_chiamata"][:80] if rec["errore_chiamata"] else "ok"
            print(f"[gen] {i}/{len(todo)} {'/'.join(futures[fut])}: {flag}")


# ---------------------------------------------------------------- fase 2: giudizio

def parse_judgment(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if obj.get("esito") not in (0, 1, "0", "1"):
        return None
    obj["esito"] = int(obj["esito"])
    return obj


def judge(client: OpenRouter, gen: dict, template: str) -> dict:
    expected = run_query(gen["soluzione_attesa"])
    generated = run_query(gen["sql_generato"]) if gen["sql_generato"] else None
    if generated is None:
        same, why = False, "nessuna query generata"
        res_gen = "(nessuna query)"
    else:
        same, why = compare(expected, generated, has_top_level_order_by(gen["soluzione_attesa"]))
        res_gen = format_result(generated)
    prompt = (template
              .replace("{{DOMANDA}}", gen["domanda"])
              .replace("{{STRATEGIA}}", gen["strategia"] or "nessuna")
              .replace("{{ATTESA}}", gen["soluzione_attesa"])
              .replace("{{GENERATA}}", gen["sql_generato"] or "(vuota)")
              .replace("{{RIS_ATTESA}}", format_result(expected))
              .replace("{{RIS_GENERATA}}", res_gen)
              .replace("{{CONFRONTO}}", ("UGUALI: " if same else "DIVERSI: ") + why))
    verdict, raw = None, ""
    for _ in range(3):
        raw = client.chat(JUDGE_MODEL, prompt, JUDGE_MAX_TOKENS)["content"]
        verdict = parse_judgment(raw)
        if verdict:
            break
    return {
        "modello_taglia": gen["modello_taglia"], "prompt": gen["prompt"], "case_id": gen["case_id"],
        "sql_giudicato": gen["sql_generato"],
        "giudice": JUDGE_MODEL,
        "esecuzione_uguale": same, "esecuzione_dettaglio": why,
        "esecuzione_errore": generated.error if generated is not None else "nessuna query",
        "esito": verdict["esito"] if verdict else None,
        "strategia_rispettata": verdict.get("strategia_rispettata") if verdict else None,
        "motivazione": verdict.get("motivazione") if verdict else f"giudizio non leggibile: {raw[:300]}",
    }


def run_judging(client, sizes, prompt_keys, case_ids, workers: int) -> None:
    template = (PROMPTS_DIR / "giudice.txt").read_text(encoding="utf-8")
    gens = {key(g): g for g in load_jsonl(GENERATIONS_PATH)}  # l'ultima generazione vince
    # Un giudizio vale solo per l'SQL che ha effettivamente valutato.
    done = {key(j) for j in load_jsonl(JUDGMENTS_PATH)
            if j.get("esito") is not None and key(j) in gens
            and j.get("sql_giudicato") == gens[key(j)]["sql_generato"]}
    failed = [k for k, g in gens.items() if g.get("errore_chiamata")]
    todo = [g for k, g in gens.items()
            if k not in done and not g.get("errore_chiamata")
            and k[0] in sizes and k[1] in prompt_keys and k[2] in case_ids]
    print(f"[judge] da fare: {len(todo)} (già fatti: {len(done)}, "
          f"saltati perché la chiamata al modello è fallita: {len(failed)})")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(judge, client, g, template): key(g) for g in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                rec = fut.result()
            except Exception as e:
                print(f"[judge] {'/'.join(futures[fut])}: ERRORE {e}")
                continue
            append_jsonl(JUDGMENTS_PATH, rec)
            print(f"[judge] {i}/{len(todo)} {'/'.join(futures[fut])}: esito={rec['esito']} "
                  f"(esecuzione {'uguale' if rec['esecuzione_uguale'] else 'diversa'})")


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=["gen", "judge", "all"], default="all")
    ap.add_argument("--models", default=",".join(MODELS), help="es. piccolo,medio")
    ap.add_argument("--prompts", default=",".join(PROMPTS), help="es. p1_schema,p3_cot")
    ap.add_argument("--cases", default="", help="id delle domande, es. P0-1,P3-1 (default: tutte)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    sizes = args.models.split(",")
    prompt_keys = args.prompts.split(",")
    cases = load_cases()
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["question_id"] in wanted]
    RESULTS_DIR.mkdir(exist_ok=True)
    client = OpenRouter()
    if args.phase in ("gen", "all"):
        run_generation(client, sizes, prompt_keys, cases, args.workers)
    if args.phase in ("judge", "all"):
        run_judging(client, sizes, prompt_keys, {c["case_id"] for c in cases}, args.workers)


if __name__ == "__main__":
    main()
