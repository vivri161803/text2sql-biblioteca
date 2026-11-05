# Griglia di valutazione

Modelli: piccolo = `nvidia/nemotron-3.5-lightning:free`, medio = `google/gemma-4-31b-it`, grande = `nvidia/nemotron-3-ultra-550b-a55b:free`. Giudice: `google/gemini-3.1-flash-lite`.

## Successi totali (modello × metodo di prompt)

| Modello | 1 - Schema | 2 - Schema + descrizioni | 3 - + CoT | 4 - + Few-shot | Totale |
|---|---|---|---|---|---|
| piccolo | 29/33 (88%) | 30/33 (91%) | 26/33 (79%) | 32/33 (97%) | 117/132 (89%) |
| medio | 30/33 (91%) | 30/33 (91%) | 33/33 (100%) | 32/33 (97%) | 125/132 (95%) |
| grande | 32/33 (97%) | 32/33 (97%) | 33/33 (100%) | 33/33 (100%) | 130/132 (98%) |
| **Totale** | 91/99 (92%) | 92/99 (93%) | 92/99 (93%) | 97/99 (98%) | **372/396 (94%)** |

## Successi per pattern (modello × pattern, tutti i prompt)

| Modello | 0 - Proiezione | 1 - Join | 2 - Raggruppamento con condizione e funzione aggregata | 3 - Soluzioni multiple Join/IN/INTERSECT | 4 - Divisione | 5 - Soluzioni multiple NOT IN/EXCEPT | 6 - Soluzioni multiple CTE/Correlazione |
|---|---|---|---|---|---|---|---|
| piccolo | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 33/36 (92%) | 11/12 (92%) | 21/24 (88%) | 18/24 (75%) |
| medio | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 30/36 (83%) | 11/12 (92%) | 24/24 (100%) | 24/24 (100%) |
| grande | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 36/36 (100%) | 12/12 (100%) | 24/24 (100%) | 23/24 (96%) |
| **Totale** | 36/36 (100%) | 35/36 (97%) | 34/36 (94%) | 99/108 (92%) | 34/36 (94%) | 69/72 (96%) | 65/72 (90%) |

## Successi per pattern (dettaglio modello + prompt)

| Modello | Prompt | 0 | 1 | 2 | 3 | 4 | 5 | 6 | Totale |
|---|---|---|---|---|---|---|---|---|---|
| piccolo | 1 - Schema | 3/3 | 3/3 | 2/3 | 8/9 | 3/3 | 5/6 | 5/6 | 29/33 (88%) |
| piccolo | 2 - Schema + descrizioni | 3/3 | 3/3 | 3/3 | 9/9 | 2/3 | 6/6 | 4/6 | 30/33 (91%) |
| piccolo | 3 - + CoT | 3/3 | 2/3 | 3/3 | 7/9 | 3/3 | 4/6 | 4/6 | 26/33 (79%) |
| piccolo | 4 - + Few-shot | 3/3 | 3/3 | 3/3 | 9/9 | 3/3 | 6/6 | 5/6 | 32/33 (97%) |
| medio | 1 - Schema | 3/3 | 3/3 | 3/3 | 6/9 | 3/3 | 6/6 | 6/6 | 30/33 (91%) |
| medio | 2 - Schema + descrizioni | 3/3 | 3/3 | 3/3 | 6/9 | 3/3 | 6/6 | 6/6 | 30/33 (91%) |
| medio | 3 - + CoT | 3/3 | 3/3 | 3/3 | 9/9 | 3/3 | 6/6 | 6/6 | 33/33 (100%) |
| medio | 4 - + Few-shot | 3/3 | 3/3 | 3/3 | 9/9 | 2/3 | 6/6 | 6/6 | 32/33 (97%) |
| grande | 1 - Schema | 3/3 | 3/3 | 3/3 | 9/9 | 3/3 | 6/6 | 5/6 | 32/33 (97%) |
| grande | 2 - Schema + descrizioni | 3/3 | 3/3 | 2/3 | 9/9 | 3/3 | 6/6 | 6/6 | 32/33 (97%) |
| grande | 3 - + CoT | 3/3 | 3/3 | 3/3 | 9/9 | 3/3 | 6/6 | 6/6 | 33/33 (100%) |
| grande | 4 - + Few-shot | 3/3 | 3/3 | 3/3 | 9/9 | 3/3 | 6/6 | 6/6 | 33/33 (100%) |
