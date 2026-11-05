"""Esecuzione delle query sul database di prova e confronto dei risultati."""
from __future__ import annotations

import datetime as dt
import decimal
import itertools
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "biblioteca.duckdb"


@dataclass
class QueryResult:
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _norm(v):
    """Rende confrontabili valori di tipo diverso (Decimal/float, date/stringhe)."""
    if isinstance(v, (decimal.Decimal, float)):
        return round(float(v), 4)
    if isinstance(v, (dt.date, dt.time, dt.datetime)):
        return v.isoformat()
    return v


def run_query(sql: str, db_path: Path = DB_PATH, max_rows: int = 200) -> QueryResult:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [tuple(_norm(v) for v in r) for r in cur.fetchmany(max_rows)]
        return QueryResult(cols, rows)
    except Exception as e:  # errori di sintassi, colonne inesistenti, dialetto...
        return QueryResult(error=f"{type(e).__name__}: {e}".splitlines()[0][:500])
    finally:
        con.close()


def has_top_level_order_by(sql: str) -> bool:
    """True se la query termina con un ORDER BY (fuori dalle sottoquery)."""
    depth, last = 0, -1
    s = sql.upper()
    for m in re.finditer(r"\(|\)|\bORDER\s+BY\b", s):
        tok = m.group(0)
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
        elif depth == 0:
            last = m.start()
    return last >= 0


def _key(row):
    return tuple((type(v).__name__ != "NoneType", str(v)) for v in row)


def compare(expected: QueryResult, generated: QueryResult, ordered: bool) -> tuple[bool, str]:
    """Confronta due risultati ignorando i nomi delle colonne.

    Le colonne possono comparire in ordine diverso; l'ordine delle righe conta
    solo se la soluzione attesa ha un ORDER BY.
    """
    if not generated.ok:
        return False, f"la query generata non è eseguibile ({generated.error})"
    if not expected.ok:
        return False, f"la soluzione attesa non è eseguibile ({expected.error})"
    ne, ng = len(expected.columns), len(generated.columns)
    if ne != ng:
        return False, f"numero di colonne diverso (attese {ne}, ottenute {ng})"
    if len(expected.rows) != len(generated.rows):
        return False, f"numero di righe diverso (attese {len(expected.rows)}, ottenute {len(generated.rows)})"
    perms = itertools.permutations(range(ng)) if ng <= 6 else [tuple(range(ng))]
    for perm in perms:
        gen_rows = [tuple(r[i] for i in perm) for r in generated.rows]
        if ordered:
            if [_key(r) for r in gen_rows] == [_key(r) for r in expected.rows]:
                return True, "risultati identici (stesso ordine)"
        elif Counter(map(_key, gen_rows)) == Counter(map(_key, expected.rows)):
            return True, "risultati identici (stesse righe)"
    if ordered:
        exp_set = Counter(map(_key, expected.rows))
        for perm in (itertools.permutations(range(ng)) if ng <= 6 else [tuple(range(ng))]):
            if Counter(_key(tuple(r[i] for i in perm)) for r in generated.rows) == exp_set:
                return False, "stesse righe ma in ordine diverso"
    return False, "righe diverse"


def format_result(res: QueryResult, limit: int = 15) -> str:
    """Rappresentazione testuale compatta, da passare al giudice."""
    if not res.ok:
        return f"ERRORE: {res.error}"
    lines = [" | ".join(res.columns)]
    lines += [" | ".join("NULL" if v is None else str(v) for v in r) for r in res.rows[:limit]]
    if len(res.rows) > limit:
        lines.append(f"... ({len(res.rows)} righe in totale)")
    return "\n".join(lines) if res.rows else lines[0] + "\n(nessuna riga)"
