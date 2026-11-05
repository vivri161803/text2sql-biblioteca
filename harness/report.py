"""Genera i deliverable a partire da results/*.jsonl.

- deliverables/risultati_text2sql.xlsx
    * Risultati: una riga per (caso, prompt, modello) con domanda, soluzione, SQL generato e giudizio
    * Griglia: successi totali e per pattern (formule COUNTIFS sul foglio Risultati)
    * Grafici: i grafici di deliverables/grafici/
    * Note: modelli, giudice, legenda
- deliverables/griglia_valutazione.md: la stessa griglia calcolata in Python (per il README)

Uso: python -m harness.report
"""
from __future__ import annotations

import json
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .charts import make_charts
from .config import GENERATIONS_PATH, JUDGE_MODEL, JUDGMENTS_PATH, MODELS, PROMPTS, ROOT
from .run import load_cases, load_jsonl

OUT_DIR = ROOT / "deliverables"
XLSX_PATH = OUT_DIR / "risultati_text2sql.xlsx"
GRID_MD_PATH = OUT_DIR / "griglia_valutazione.md"

FONT = "Arial"
HEADER_FILL = PatternFill("solid", start_color="1F3864")
SUBHEADER_FILL = PatternFill("solid", start_color="D9E1F2")
GREEN = PatternFill("solid", start_color="C6EFCE")
RED = PatternFill("solid", start_color="FFC7CE")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

COLUMNS = [  # (intestazione, larghezza)
    ("ID caso", 14), ("Pattern di difficoltà", 26), ("Strategia richiesta", 14),
    ("Domanda (x)", 50), ("Soluzione attesa (y)", 55), ("Metodo di prompt", 22),
    ("Prompt (testo inviato)", 60), ("Modello", 10), ("Modello (OpenRouter)", 34),
    ("SQL generato f(x)", 55), ("Esito giudice (1/0)", 12), ("Strategia rispettata", 12),
    ("Commento del giudice", 70), ("Confronto esecuzione (database di prova)", 40),
]
COL = {name: get_column_letter(i) for i, (name, _) in enumerate(COLUMNS, 1)}


def pattern_label(case: dict) -> str:
    return f"{case['pattern']} - {case['pattern_nome']}"


def collect_rows() -> list[dict]:
    """Unisce generazioni e giudizi nell'ordine caso -> prompt -> modello."""
    gens = {(g["modello_taglia"], g["prompt"], g["case_id"]): g for g in load_jsonl(GENERATIONS_PATH)
            if not g.get("errore_chiamata") and g["modello"] == MODELS[g["modello_taglia"]]}
    juds = {}
    for j in load_jsonl(JUDGMENTS_PATH):
        k = (j["modello_taglia"], j["prompt"], j["case_id"])
        if k in gens and j.get("esito") is not None and j.get("sql_giudicato") == gens[k]["sql_generato"]:
            juds[k] = j
    rows, missing = [], []
    for case in load_cases():
        for p in PROMPTS:
            for size in MODELS:
                k = (size, p, case["case_id"])
                if k not in gens or k not in juds:
                    missing.append(k)
                    continue
                rows.append({"case": case, "prompt": p, "size": size, "gen": gens[k], "jud": juds[k]})
    if missing:
        print(f"ATTENZIONE: {len(missing)} combinazioni senza risultato, es. {missing[:3]}")
    return rows


def style_header(cell, fill=HEADER_FILL, color="FFFFFF"):
    cell.font = Font(name=FONT, bold=True, color=color)
    cell.fill = fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = BORDER


def write_results_sheet(ws, rows):
    for i, (name, width) in enumerate(COLUMNS, 1):
        style_header(ws.cell(row=1, column=i, value=name))
        ws.column_dimensions[get_column_letter(i)].width = width
    for r, row in enumerate(rows, 2):
        c, g, j = row["case"], row["gen"], row["jud"]
        strat = j.get("strategia_rispettata")
        values = [
            c["case_id"], pattern_label(c), c["strategia"] or "-", c["domanda"], c["soluzione_attesa"],
            PROMPTS[row["prompt"]], g["prompt_testo"], row["size"], g["modello"],
            g["sql_generato"] or "(nessuna query)", j["esito"],
            "-" if strat is None else ("sì" if strat else "no"),
            j["motivazione"],
            ("uguale" if j["esecuzione_uguale"] else "diverso") + f": {j['esecuzione_dettaglio']}",
        ]
        for col, v in enumerate(values, 1):
            cell = ws.cell(row=r, column=col, value=v)
            cell.font = Font(name=FONT, size=9)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = BORDER
        ws.row_dimensions[r].height = 110
    last = len(rows) + 1
    esito = f"{COL['Esito giudice (1/0)']}2:{COL['Esito giudice (1/0)']}{last}"
    ws.conditional_formatting.add(esito, CellIsRule(operator="equal", formula=["1"], fill=GREEN))
    ws.conditional_formatting.add(esito, CellIsRule(operator="equal", formula=["0"], fill=RED))
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{last}"
    return last


def write_grid_sheet(ws, last, patterns):
    rng = lambda name: f"Risultati!${COL[name]}$2:${COL[name]}${last}"  # noqa: E731
    M, P, PAT, E = rng("Modello"), rng("Metodo di prompt"), rng("Pattern di difficoltà"), rng("Esito giudice (1/0)")
    prompts = list(PROMPTS.values())
    sizes = list(MODELS)
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 26

    def title(r, text):
        cell = ws.cell(row=r, column=1, value=text)
        cell.font = Font(name=FONT, bold=True, size=12)

    def num(cell, fmt="0"):
        cell.font = Font(name=FONT)
        cell.number_format = fmt
        cell.alignment = Alignment(horizontal="center")
        cell.border = BORDER

    # --- Tabella 1: successi totali (modello x prompt)
    title(1, "Successi totali per modello e metodo di prompt (casi superati / casi valutati)")
    r0 = 3
    style_header(ws.cell(row=r0, column=1, value="Modello"))
    for j, p in enumerate(prompts, 2):
        style_header(ws.cell(row=r0, column=j, value=p))
        ws.column_dimensions[get_column_letter(j)].width = 22
    style_header(ws.cell(row=r0, column=len(prompts) + 2, value="Totale modello"))
    ws.column_dimensions[get_column_letter(len(prompts) + 2)].width = 16
    for i, s in enumerate(sizes, r0 + 1):
        style_header(ws.cell(row=i, column=1, value=s), SUBHEADER_FILL, "000000")
        for j in range(2, len(prompts) + 2):
            num(ws.cell(row=i, column=j,
                        value=f'=COUNTIFS({M},$A{i},{P},{get_column_letter(j)}${r0},{E},1)'))
        num(ws.cell(row=i, column=len(prompts) + 2,
                    value=f"=SUM(B{i}:{get_column_letter(len(prompts) + 1)}{i})"))
    tot = r0 + len(sizes) + 1
    style_header(ws.cell(row=tot, column=1, value="Totale prompt"), SUBHEADER_FILL, "000000")
    for j in range(2, len(prompts) + 3):
        L = get_column_letter(j)
        num(ws.cell(row=tot, column=j, value=f"=SUM({L}{r0 + 1}:{L}{tot - 1})"))

    # --- Tabella 2: percentuali
    r1 = tot + 2
    title(r1, "Accuratezza (%) per modello e metodo di prompt")
    style_header(ws.cell(row=r1 + 1, column=1, value="Modello"))
    for j, p in enumerate(prompts, 2):
        style_header(ws.cell(row=r1 + 1, column=j, value=p))
    style_header(ws.cell(row=r1 + 1, column=len(prompts) + 2, value="Totale modello"))
    for i, s in enumerate(sizes, r1 + 2):
        style_header(ws.cell(row=i, column=1, value=s), SUBHEADER_FILL, "000000")
        for j in range(2, len(prompts) + 2):
            L = get_column_letter(j)
            num(ws.cell(row=i, column=j,
                        value=f'=IFERROR({L}{r0 + 1 + i - r1 - 2}/COUNTIFS({M},$A{i},{P},{L}${r1 + 1}),0)'), "0.0%")
        Lt = get_column_letter(len(prompts) + 2)
        num(ws.cell(row=i, column=len(prompts) + 2,
                    value=f'=IFERROR({Lt}{r0 + 1 + i - r1 - 2}/COUNTIFS({M},$A{i}),0)'), "0.0%")

    # --- Tabella 3: successi per pattern (modello+prompt x pattern)
    r2 = r1 + len(sizes) + 4
    title(r2, "Successi per pattern di difficoltà (casi superati; tra parentesi nella riga 'Casi' il numero di casi per cella)")
    hdr = r2 + 1
    style_header(ws.cell(row=hdr, column=1, value="Modello"))
    style_header(ws.cell(row=hdr, column=2, value="Metodo di prompt"))
    for j, pat in enumerate(patterns, 3):
        style_header(ws.cell(row=hdr, column=j, value=pat))
        ws.column_dimensions[get_column_letter(j)].width = max(ws.column_dimensions[get_column_letter(j)].width or 0, 20)
    style_header(ws.cell(row=hdr, column=len(patterns) + 3, value="Totale"))
    r = hdr + 1
    for s in sizes:
        for p in prompts:
            style_header(ws.cell(row=r, column=1, value=s), SUBHEADER_FILL, "000000")
            style_header(ws.cell(row=r, column=2, value=p), SUBHEADER_FILL, "000000")
            for j in range(3, len(patterns) + 3):
                L = get_column_letter(j)
                num(ws.cell(row=r, column=j,
                            value=f'=COUNTIFS({M},$A{r},{P},$B{r},{PAT},{L}${hdr},{E},1)'))
            num(ws.cell(row=r, column=len(patterns) + 3,
                        value=f"=SUM(C{r}:{get_column_letter(len(patterns) + 2)}{r})"))
            r += 1
    style_header(ws.cell(row=r, column=1, value="Casi"), SUBHEADER_FILL, "000000")
    style_header(ws.cell(row=r, column=2, value="per cella"), SUBHEADER_FILL, "000000")
    for j in range(3, len(patterns) + 3):
        L = get_column_letter(j)
        num(ws.cell(row=r, column=j,
                    value=f'=COUNTIFS({M},$A${hdr + 1},{P},$B${hdr + 1},{PAT},{L}${hdr})'))
    num(ws.cell(row=r, column=len(patterns) + 3, value=f"=SUM(C{r}:{get_column_letter(len(patterns) + 2)}{r})"))

    # --- Tabella 4: accuratezza per pattern e modello (tutti i prompt insieme)
    r3 = r + 2
    title(r3, "Accuratezza (%) per pattern e modello (tutti i prompt insieme)")
    style_header(ws.cell(row=r3 + 1, column=1, value="Modello"))
    for j, pat in enumerate(patterns, 3):
        style_header(ws.cell(row=r3 + 1, column=j, value=pat))
    for i, s in enumerate(sizes, r3 + 2):
        style_header(ws.cell(row=i, column=1, value=s), SUBHEADER_FILL, "000000")
        for j in range(3, len(patterns) + 3):
            L = get_column_letter(j)
            num(ws.cell(row=i, column=j,
                        value=f'=IFERROR(COUNTIFS({M},$A{i},{PAT},{L}${r3 + 1},{E},1)/COUNTIFS({M},$A{i},{PAT},{L}${r3 + 1}),0)'),
                "0.0%")
    ws.freeze_panes = "C1"


def write_charts_sheet(ws, pngs):
    """Inserisce i grafici PNG uno sotto l'altro."""
    row = 1
    for png in pngs:
        img = XLImage(str(png))
        img.width, img.height = img.width // 2, img.height // 2  # PNG a 200 dpi
        ws.add_image(img, f"B{row + 1}")
        row += img.height // 20 + 3  # ~20 px per riga


def write_notes_sheet(ws):
    lines = [
        ("Esperimento Text2SQL – base di dati Biblioteca", True),
        ("", False),
        ("Modelli valutati (f), via OpenRouter:", True),
        *[(f"  {k}: {v}", False) for k, v in MODELS.items()],
        ("Giudice (g):", True),
        (f"  {JUDGE_MODEL}", False),
        ("", False),
        ("Legenda colonne del foglio Risultati:", True),
        ("  Esito giudice: 1 = query generata equivalente alla soluzione attesa, 0 = non equivalente.", False),
        ("  Strategia rispettata: per i pattern 3, 5 e 6, se la query usa la strategia richiesta (non influisce sull'esito).", False),
        ("  Confronto esecuzione: confronto automatico dei risultati sul database DuckDB di prova, fornito al giudice come prova.", False),
        ("", False),
        ("Il foglio Griglia è calcolato con formule COUNTIFS sul foglio Risultati.", False),
        ("Dataset, fonti e prompt: cartelle dataset/ e prompts/ del progetto.", False),
    ]
    ws.column_dimensions["A"].width = 120
    for i, (text, bold) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = Font(name=FONT, bold=bold)


def python_grid(rows, patterns):
    """Stessa griglia calcolata in Python: serve al README e a verificare le formule."""
    tot = defaultdict(lambda: [0, 0])
    for row in rows:
        lab = pattern_label(row["case"])
        for k in [(row["size"], row["prompt"]), (row["size"], row["prompt"], lab), (row["size"], lab),
                  (row["size"],), (row["prompt"],), (lab,), ()]:
            tot[k][0] += row["jud"]["esito"]
            tot[k][1] += 1
    return tot


def write_markdown(rows, patterns, grid):
    def cell(k):
        s, n = grid[k]
        return f"{s}/{n} ({100 * s / n:.0f}%)" if n else "-"

    prompts = list(PROMPTS)
    out = ["# Griglia di valutazione", "",
           f"Modelli: {', '.join(f'{k} = `{v}`' for k, v in MODELS.items())}. Giudice: `{JUDGE_MODEL}`.", "",
           "## Successi totali (modello × metodo di prompt)", "",
           "| Modello | " + " | ".join(PROMPTS[p] for p in prompts) + " | Totale |",
           "|---|" + "---|" * (len(prompts) + 1)]
    for s in MODELS:
        out.append(f"| {s} | " + " | ".join(cell((s, p)) for p in prompts) + f" | {cell((s,))} |")
    out.append("| **Totale** | " + " | ".join(cell((p,)) for p in prompts) + f" | **{cell(())}** |")
    out += ["", "## Successi per pattern (modello × pattern, tutti i prompt)", "",
            "| Modello | " + " | ".join(patterns) + " |", "|---|" + "---|" * len(patterns)]
    for s in MODELS:
        out.append(f"| {s} | " + " | ".join(cell((s, pat)) for pat in patterns) + " |")
    out.append("| **Totale** | " + " | ".join(cell((pat,)) for pat in patterns) + " |")
    out += ["", "## Successi per pattern (dettaglio modello + prompt)", "",
            "| Modello | Prompt | " + " | ".join(p.split(' - ')[0] for p in patterns) + " | Totale |",
            "|---|---|" + "---|" * (len(patterns) + 1)]
    for s in MODELS:
        for p in prompts:
            out.append(f"| {s} | {PROMPTS[p]} | " +
                       " | ".join(f"{grid[(s, p, pat)][0]}/{grid[(s, p, pat)][1]}" for pat in patterns) +
                       f" | {cell((s, p))} |")
    GRID_MD_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rows = collect_rows()
    patterns = sorted({pattern_label(r["case"]) for r in rows}, key=lambda s: int(s.split(" ")[0]))
    wb = Workbook()
    ws = wb.active
    ws.title = "Risultati"
    last = write_results_sheet(ws, rows)
    write_grid_sheet(wb.create_sheet("Griglia"), last, patterns)
    write_charts_sheet(wb.create_sheet("Grafici"), make_charts(rows))
    write_notes_sheet(wb.create_sheet("Note"))
    wb.calculation.fullCalcOnLoad = True  # Excel ricalcola le formule all'apertura
    wb.save(XLSX_PATH)
    grid = python_grid(rows, patterns)
    write_markdown(rows, patterns, grid)
    print(f"Scritti {XLSX_PATH} ({len(rows)} righe) e {GRID_MD_PATH}")


if __name__ == "__main__":
    main()
