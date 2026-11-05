# Prompt

Ogni prompt aggiunge qualcosa al precedente, così si misura l'effetto di ogni aggiunta.

| File | Metodo | Contenuto |
|---|---|---|
| `p1_schema.txt` | Schema | Prompt d'esempio del PDF: ruolo, schema logico con chiavi primarie, domanda |
| `p2_schema_descrizioni.txt` | + Descrizioni | p1 + descrizione di ogni tabella (testo di pagina 2 del PDF) |
| `p3_cot.txt` | + CoT | p2 + ragionamento passo per passo in 6 punti; la query finale va in un blocco ```sql |
| `p4_fewshot.txt` | + Few-shot | p3 + 7 esempi risolti, uno per pattern (l'esempio del pattern 0 è quello del PDF) |

Segnaposto sostituiti dalla harness:
- `{{DOMANDA}}`: la domanda in italiano (x).
- `{{STRATEGIA}}`: solo per i pattern 3, 5 e 6, la riga presa da `strategie.json` (es. "Risolvi la query utilizzando l'operatore EXCEPT."); vuoto negli altri casi.

Le domande del dataset devono essere diverse dagli esempi few-shot.
