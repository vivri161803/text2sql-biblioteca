"""Grafici dei risultati (PNG in deliverables/grafici/), usati dal README e dall'Excel.

Uso: python -m harness.charts   (viene chiamato anche da harness.report)
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .config import MODELS, PROMPTS, ROOT  # noqa: E402

OUT = ROOT / "deliverables" / "grafici"

# Palette di riferimento (validata: CVD e contrasto) e inchiostri.
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # ordine fisso
MODEL_COLOR = dict(zip(MODELS, SERIES))
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
MODEL_LABEL = {"piccolo": "piccolo · Nemotron 3.5 Lightning",
               "medio": "medio · Gemma 4 31B",
               "grande": "grande · Nemotron 3 Ultra"}
PROMPT_SHORT = {"p1_schema": "1. Schema", "p2_schema_descrizioni": "2. + Descrizioni",
                "p3_cot": "3. + CoT", "p4_fewshot": "4. + Few-shot"}
PATTERN_SHORT = {0: "0 · Proiezione", 1: "1 · Join", 2: "2 · Group by + Having",
                 3: "3 · Join / IN / INTERSECT", 4: "4 · Divisione",
                 5: "5 · NOT IN / EXCEPT", 6: "6 · CTE / Correlazione"}

plt.rcParams.update({
    "font.family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "axes.edgecolor": AXIS, "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def _title(fig, title, subtitle):
    fig.text(0.02, 0.97, title, fontsize=14, fontweight="bold", va="top", color=INK)
    fig.text(0.02, 0.905, subtitle, fontsize=10, va="top", color=INK2)


def _clean(ax, grid_axis="y"):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def error_cause(row) -> str:
    sql, j = row["gen"]["sql_generato"], row["jud"]
    if re.search(r"\bLETTER[EI]\b|\bLETTORI\b", sql):
        return "Nome di tabella inventato (LETTERE)"
    if "`" in sql:
        return "Backtick MySQL (falso negativo del giudice)"
    if "Ambiguous" in (j.get("esecuzione_errore") or ""):
        return "Colonna ambigua senza alias"
    return "Duplicati (DISTINCT mancante)"


CAUSES = ["Nome di tabella inventato (LETTERE)", "Colonna ambigua senza alias",
          "Duplicati (DISTINCT mancante)", "Backtick MySQL (falso negativo del giudice)"]


def chart_prompt_effect(rows):
    acc = defaultdict(lambda: [0, 0])
    for r in rows:
        acc[(r["size"], r["prompt"])][0] += r["jud"]["esito"]
        acc[(r["size"], r["prompt"])][1] += 1
    prompts = list(PROMPTS)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(left=0.08, right=0.74, top=0.78, bottom=0.11)
    _title(fig, "Effetto del metodo di prompt sull'accuratezza",
           "Casi superati su 33 per configurazione; i prompt sono cumulativi (ognuno aggiunge qualcosa al precedente)")
    end_offsets = {"grande": 0.6, "medio": 0.9, "piccolo": -1.6}  # evita sovrapposizioni delle etichette finali
    for size in MODELS:
        ys = [100 * acc[(size, p)][0] / acc[(size, p)][1] for p in prompts]
        ax.plot(range(4), ys, color=MODEL_COLOR[size], linewidth=2, marker="o", markersize=9,
                markeredgecolor=SURFACE, markeredgewidth=2, label=MODEL_LABEL[size], zorder=3)
        ax.annotate("●", (3, ys[-1]), xytext=(14, end_offsets[size] * 6), textcoords="offset points",
                    va="center", fontsize=11, color=MODEL_COLOR[size])
        ax.annotate(f"{size}  {ys[-1]:.0f}%", (3, ys[-1]), xytext=(27, end_offsets[size] * 6),
                    textcoords="offset points", va="center", fontsize=10, color=INK, fontweight="bold")
    p_cot = 100 * acc[("piccolo", "p3_cot")][0] / 33
    ax.annotate(f"{p_cot:.0f}% – il CoT peggiora\nil modello piccolo", (2, p_cot), xytext=(-12, -4),
                textcoords="offset points", ha="right", va="center", fontsize=9, color=INK2)
    ax.set_xticks(range(4), [PROMPT_SHORT[p] for p in prompts], color=INK2)
    ax.set_ylim(74, 102)
    ax.set_yticks(range(75, 101, 5), [f"{v}%" for v in range(75, 101, 5)])
    ax.set_xlim(-0.25, 3.25)
    _clean(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 0.45), frameon=False, fontsize=9, labelcolor=INK2)
    fig.savefig(OUT / "1_effetto_prompt.png", dpi=200)
    plt.close(fig)


def chart_pattern_heatmap(rows):
    acc = defaultdict(lambda: [0, 0])
    for r in rows:
        for k in ((r["case"]["pattern"], r["size"]), (r["case"]["pattern"], "totale")):
            acc[k][0] += r["jud"]["esito"]
            acc[k][1] += 1
    cols = list(MODELS) + ["totale"]
    pats = sorted({r["case"]["pattern"] for r in rows})
    data = [[acc[(p, c)][0] / acc[(p, c)][1] for c in cols] for p in pats]
    cmap = LinearSegmentedColormap.from_list("blu", BLUE_RAMP)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    fig.subplots_adjust(left=0.25, right=0.97, top=0.8, bottom=0.04)
    _title(fig, "Accuratezza per pattern di difficoltà e modello",
           "Tutti i prompt insieme · più scuro = più casi superati · nelle celle: percentuale e casi superati / casi")
    ax.pcolormesh(data, cmap=cmap, vmin=0.7, vmax=1.0, edgecolors=SURFACE, linewidth=3)
    for i, p in enumerate(pats):
        for j, c in enumerate(cols):
            v, (s, n) = data[i][j], acc[(p, c)]
            color = "#ffffff" if v >= 0.9 else INK
            ax.text(j + 0.5, i + 0.5, f"{100 * v:.0f}%", ha="center", va="center", fontsize=11,
                    fontweight="bold", color=color)
            ax.text(j + 0.5, i + 0.22, f"{s}/{n}", ha="center", va="center", fontsize=8, color=color)
    ax.set_xticks([j + 0.5 for j in range(len(cols))], ["piccolo", "medio", "grande", "tutti"], color=INK2)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(pats))], [PATTERN_SHORT[p] for p in pats], color=INK2)
    ax.invert_yaxis()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.savefig(OUT / "2_accuratezza_per_pattern.png", dpi=200)
    plt.close(fig)


def chart_error_causes(rows):
    counts = Counter((r["size"], error_cause(r)) for r in rows if r["jud"]["esito"] == 0)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.66, bottom=0.12)
    _title(fig, "Perché le query sono state bocciate",
           "Casi bocciati dal giudice per modello (su 132 casi ciascuno), classificati per causa")
    sizes = list(MODELS)[::-1]
    for y, size in enumerate(sizes):
        left = 0
        for c, cause in enumerate(CAUSES):
            n = counts[(size, cause)]
            if not n:
                continue
            ax.barh(y, n, left=left, height=0.5, color=SERIES[c], edgecolor=SURFACE, linewidth=2,
                    hatch="//" if "falso negativo" in cause else None)
            label_ink = INK if SERIES[c] == "#eda100" else "#ffffff"  # testo scuro sul giallo
            ax.text(left + n / 2, y, str(n), ha="center", va="center", fontsize=10, fontweight="bold",
                    color=label_ink, bbox=dict(boxstyle="round,pad=0.15", fc=SERIES[c], ec="none")
                    if "falso negativo" in cause else None)
            left += n
        ax.text(left + 0.3, y, f"{left} bocciati", va="center", fontsize=10, color=INK, fontweight="bold")
    ax.set_yticks(range(len(sizes)), sizes, color=INK2)
    ax.set_xlim(0, 17)
    ax.set_xlabel("numero di casi bocciati", color=MUTED)
    _clean(ax, "x")
    handles = [plt.Rectangle((0, 0), 1, 1, color=SERIES[i], hatch="//" if "falso" in c else None,
                             edgecolor=SURFACE) for i, c in enumerate(CAUSES)]
    fig.legend(handles, CAUSES, loc="upper left", bbox_to_anchor=(0.02, 0.84), ncol=2, frameon=False,
               fontsize=9, labelcolor=INK2)
    fig.savefig(OUT / "3_cause_errori.png", dpi=200)
    plt.close(fig)
    return counts


def make_charts(rows) -> list:
    OUT.mkdir(parents=True, exist_ok=True)
    chart_prompt_effect(rows)
    chart_pattern_heatmap(rows)
    counts = chart_error_causes(rows)
    print("Cause degli errori:", dict(counts))
    return sorted(OUT.glob("*.png"))


if __name__ == "__main__":
    from .report import collect_rows
    print(make_charts(collect_rows()))
