"""Verifica il dataset sul database di prova.

Controlla che ogni soluzione attesa sia eseguibile e restituisca almeno una riga,
che le soluzioni alternative (strategie) diano lo stesso risultato e che gli
esempi few-shot del prompt p4 siano eseguibili.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.build_db import build  # noqa: E402
from harness.db_utils import compare, format_result, has_top_level_order_by, run_query  # noqa: E402


def main() -> int:
    build()
    data = json.loads((ROOT / "dataset" / "dataset.json").read_text(encoding="utf-8"))
    problems = 0
    for q in data["domande"]:
        sols = q["soluzioni"]
        results = {s: run_query(sql) for s, sql in sols.items()}
        first = next(iter(sols))
        print(f"\n=== {q['id']} (pattern {q['pattern']}) {q['domanda']}")
        print(format_result(results[first]))
        for s, r in results.items():
            if not r.ok:
                print(f"  !! {s}: errore {r.error}"); problems += 1
            elif not r.rows:
                print(f"  !! {s}: nessuna riga"); problems += 1
        for s in list(sols)[1:]:
            same, why = compare(results[first], results[s], has_top_level_order_by(sols[first]))
            print(f"  {first} vs {s}: {'OK' if same else '!! ' + why}")
            problems += not same

    print("\n=== Esempi few-shot (prompts/p4_fewshot.txt)")
    p4 = (ROOT / "prompts" / "p4_fewshot.txt").read_text(encoding="utf-8")
    for i, sql in enumerate(re.findall(r"```sql\n(.*?)```", p4, re.S), 1):
        r = run_query(sql)
        status = "OK" if r.ok and r.rows else "!!"
        problems += status != "OK"
        print(f"  Esempio {i}: {status} {len(r.rows)} righe {r.error or ''}")

    print(f"\nProblemi trovati: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
