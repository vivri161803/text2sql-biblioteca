# Dataset Text2SQL – Biblioteca

Generato da `dataset.json`. Ogni domanda è adattata da un esercizio online (colonna Fonte) e la soluzione è verificata sul database di prova con `dataset/validate.py`.

## Pattern 0 – Proiezione

### P0-1

**Domanda:** Mostra il titolo, il genere e l'anno di pubblicazione dei libri pubblicati dopo il 2000, ordinati per anno di pubblicazione crescente.

**Fonte:** [W3RESOURCE](https://w3resource.com/projects/sql/sql-projects-on-library-management-system.php) – Query-7: libri pubblicati dopo un certo anno (WHERE published_year > 2000)

**Adattamento:** Tabella Books → LIBRO; aggiunti genere e ORDER BY.

Soluzione attesa:
```sql
SELECT titolo, genere, anno_pubblicazione
FROM LIBRO
WHERE anno_pubblicazione > 2000
ORDER BY anno_pubblicazione ASC;
```

### P0-2

**Domanda:** Mostra il codice del libro, il codice del lettore e la data di prestito dei prestiti non ancora restituiti, ordinati dal prestito meno recente al più recente.

**Fonte:** [W3RESOURCE](https://w3resource.com/projects/sql/sql-projects-on-library-management-system.php) – Query-15: libri prestati ma non ancora restituiti (return_date IS NULL)

**Adattamento:** Ridotta alla sola tabella PRESTITO_LIBRO (niente join) per restare nel pattern Proiezione; aggiunto ORDER BY.

Soluzione attesa:
```sql
SELECT id_libro, id_lettore, data_prestito
FROM PRESTITO_LIBRO
WHERE data_restituzione IS NULL
ORDER BY data_prestito ASC;
```

### P0-3

**Domanda:** Mostra nome, cognome e data di nascita degli autori di nazionalità “italiana” ancora in vita, ordinati dal più giovane al più anziano.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 1a: nome e data di nascita degli atleti italiani (selezione su Nazione)

**Adattamento:** ATLETA → AUTORE; la condizione sulle gare è sostituita da 'ancora in vita' (data_morte IS NULL); aggiunto ORDER BY.

Soluzione attesa:
```sql
SELECT nome, cognome, data_nascita
FROM AUTORE
WHERE nazionalità = 'italiana' AND data_morte IS NULL
ORDER BY data_nascita DESC;
```

## Pattern 1 – Join

### P1-1

**Domanda:** Mostra nome e cognome dei lettori che hanno preso in prestito il libro intitolato “Il nome della rosa”, insieme alla data di ciascun prestito.

**Fonte:** [W3RESOURCE](https://w3resource.com/projects/sql/sql-projects-on-library-management-system.php) – Query-9: membri che hanno preso in prestito un libro specifico (title = '1984')

**Adattamento:** Members/Borrowing/Books → LETTORE/PRESTITO_LIBRO/LIBRO.

Soluzione attesa:
```sql
SELECT LE.nome, LE.cognome, P.data_prestito
FROM PRESTITO_LIBRO P
JOIN LIBRO L ON P.id_libro = L.id_libro
JOIN LETTORE LE ON P.id_lettore = LE.id_lettore
WHERE L.titolo = 'Il nome della rosa';
```

### P1-2

**Domanda:** Mostra nome e cognome del lettore e titolo del libro per tutti i prestiti non ancora restituiti iniziati prima del 1° settembre 2026.

**Fonte:** [W3RESOURCE](https://w3resource.com/projects/sql/sql-projects-on-library-management-system.php) – Query-5: libri in ritardo (non restituiti e prestati da più di 14 giorni)

**Adattamento:** CURRENT_DATE - 14 giorni sostituito da una data fissa, così il risultato non dipende dal giorno di esecuzione.

Soluzione attesa:
```sql
SELECT LE.nome, LE.cognome, L.titolo
FROM PRESTITO_LIBRO P
JOIN LETTORE LE ON P.id_lettore = LE.id_lettore
JOIN LIBRO L ON P.id_libro = L.id_libro
WHERE P.data_restituzione IS NULL
  AND P.data_prestito < DATE '2026-09-01';
```

### P1-3

**Domanda:** Mostra il titolo dei libri scritti da Umberto Eco che sono stati presi in prestito nel 2025, insieme alla data di ciascun prestito.

**Fonte:** [UNIPR](https://www.ce.unipr.it/people/cagnoni/didattica/basidati/testi_esame/bd180209.pdf) – Punto E: volumi di Umberto Eco prestati nell'ultimo mese e numero di prestiti

**Adattamento:** 'Ultimo mese' → anno 2025; tolto il conteggio per restare nel pattern Join.

Soluzione attesa:
```sql
SELECT L.titolo, P.data_prestito
FROM AUTORE A
JOIN LIBRO L ON A.id_autore = L.id_autore
JOIN PRESTITO_LIBRO P ON P.id_libro = L.id_libro
WHERE A.nome = 'Umberto' AND A.cognome = 'Eco'
  AND P.data_prestito BETWEEN DATE '2025-01-01' AND DATE '2025-12-31';
```

## Pattern 2 – Raggruppamento con condizione e funzione aggregata

### P2-1

**Domanda:** Per ogni lettore che ha effettuato almeno 3 prestiti, mostra il codice, il nome e il cognome del lettore e il numero di prestiti effettuati.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Es. 1c (join, group by): per ogni studente con media > 28, matricola, nome e voti; cfr. anche W3RESOURCE Query-12

**Adattamento:** STUDENTE/ESAME → LETTORE/PRESTITO_LIBRO; condizione HAVING sul conteggio dei prestiti.

Soluzione attesa:
```sql
SELECT LE.id_lettore, LE.nome, LE.cognome, COUNT(*) AS num_prestiti
FROM LETTORE LE
JOIN PRESTITO_LIBRO P ON LE.id_lettore = P.id_lettore
GROUP BY LE.id_lettore, LE.nome, LE.cognome
HAVING COUNT(*) >= 3;
```

### P2-2

**Domanda:** Per ogni lettore iscritto alla biblioteca dal 1° gennaio 2024 in poi che ha effettuato almeno 2 prenotazioni di sale, mostra il codice e il cognome del lettore, il numero di prenotazioni effettuate e il numero di sale diverse prenotate.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Es. 2d (join, group by): persone nate dopo il 1970 con almeno 5 lezioni, numero lezioni e numero istruttori diversi

**Adattamento:** PERSONA/LEZIONE_PRIVATA/ISTRUTTORE → LETTORE/PRENOTAZIONE_SALA/SALA; data di nascita → data di iscrizione.

Soluzione attesa:
```sql
SELECT LE.id_lettore, LE.cognome, COUNT(*) AS num_prenotazioni, COUNT(DISTINCT PS.id_sala) AS num_sale
FROM LETTORE LE
JOIN PRENOTAZIONE_SALA PS ON LE.id_lettore = PS.id_lettore
WHERE LE.data_iscrizione >= DATE '2024-01-01'
GROUP BY LE.id_lettore, LE.cognome
HAVING COUNT(*) >= 2;
```

### P2-3

**Domanda:** Per ogni piano che ospita almeno 2 sale, mostra il piano, il numero di sale presenti, la capacità massima e la capacità media delle sale di quel piano.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Es. 4b (join, group by): per le città con almeno 100 contratti, costo massimo, costo medio e numero di contratti

**Adattamento:** Città/ALLOGGIO → piano/SALA; costo affitto → capacità.

Soluzione attesa:
```sql
SELECT piano, COUNT(*) AS num_sale, MAX(capacità) AS capacita_max, AVG(capacità) AS capacita_media
FROM SALA
GROUP BY piano
HAVING COUNT(*) >= 2;
```

## Pattern 3 – Soluzioni multiple Join/IN/INTERSECT

### P3-1

**Domanda:** Mostra il codice dei lettori che hanno preso in prestito sia almeno un libro di genere “fantasy” sia almeno un libro di genere “giallo”.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Query annidate es. 1a: orchestre che hanno tenuto concerti sia a Torino sia a Milano

**Adattamento:** Orchestre/città → lettori/generi dei libri presi in prestito.

Soluzione attesa – JOIN:
```sql
SELECT DISTINCT P1.id_lettore
FROM PRESTITO_LIBRO P1
JOIN LIBRO L1 ON P1.id_libro = L1.id_libro
JOIN PRESTITO_LIBRO P2 ON P1.id_lettore = P2.id_lettore
JOIN LIBRO L2 ON P2.id_libro = L2.id_libro
WHERE L1.genere = 'fantasy' AND L2.genere = 'giallo';
```

Soluzione attesa – IN:
```sql
SELECT id_lettore
FROM LETTORE
WHERE id_lettore IN (SELECT id_lettore FROM PRESTITO_LIBRO
                     WHERE id_libro IN (SELECT id_libro FROM LIBRO WHERE genere = 'fantasy'))
  AND id_lettore IN (SELECT id_lettore FROM PRESTITO_LIBRO
                     WHERE id_libro IN (SELECT id_libro FROM LIBRO WHERE genere = 'giallo'));
```

Soluzione attesa – INTERSECT:
```sql
SELECT P.id_lettore
FROM PRESTITO_LIBRO P JOIN LIBRO L ON P.id_libro = L.id_libro
WHERE L.genere = 'fantasy'
INTERSECT
SELECT P.id_lettore
FROM PRESTITO_LIBRO P JOIN LIBRO L ON P.id_libro = L.id_libro
WHERE L.genere = 'giallo';
```

### P3-2

**Domanda:** Mostra il codice e il nome delle sale che sono state prenotate sia nel mese di marzo 2026 sia nel mese di aprile 2026.

**Fonte:** [POLITO_SLIDE](https://dbdmg.polito.it/wordpress/wp-content/uploads/2016/04/02EserciziSQLIN-NOT-IN-GROUPBYx2.pdf) – Esercizio #1: orchestre che hanno tenuto concerti sia a Torino sia a Milano

**Adattamento:** Orchestre/città → sale/mesi di prenotazione.

Soluzione attesa – JOIN:
```sql
SELECT DISTINCT S.id_sala, S.nome
FROM SALA S
JOIN PRENOTAZIONE_SALA P1 ON S.id_sala = P1.id_sala
JOIN PRENOTAZIONE_SALA P2 ON S.id_sala = P2.id_sala
WHERE P1.data BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
  AND P2.data BETWEEN DATE '2026-04-01' AND DATE '2026-04-30';
```

Soluzione attesa – IN:
```sql
SELECT id_sala, nome
FROM SALA
WHERE id_sala IN (SELECT id_sala FROM PRENOTAZIONE_SALA
                  WHERE data BETWEEN DATE '2026-03-01' AND DATE '2026-03-31')
  AND id_sala IN (SELECT id_sala FROM PRENOTAZIONE_SALA
                  WHERE data BETWEEN DATE '2026-04-01' AND DATE '2026-04-30');
```

Soluzione attesa – INTERSECT:
```sql
SELECT S.id_sala, S.nome
FROM SALA S JOIN PRENOTAZIONE_SALA P ON S.id_sala = P.id_sala
WHERE P.data BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
INTERSECT
SELECT S.id_sala, S.nome
FROM SALA S JOIN PRENOTAZIONE_SALA P ON S.id_sala = P.id_sala
WHERE P.data BETWEEN DATE '2026-04-01' AND DATE '2026-04-30';
```

### P3-3

**Domanda:** Mostra il codice, il nome e il cognome degli autori che hanno scritto sia almeno un libro di genere “romanzo” sia almeno un libro di genere “saggio”.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Query annidate es. 1a: orchestre che hanno tenuto concerti sia a Torino sia a Milano

**Adattamento:** Orchestre/città → autori/generi dei libri scritti.

Soluzione attesa – JOIN:
```sql
SELECT DISTINCT A.id_autore, A.nome, A.cognome
FROM AUTORE A
JOIN LIBRO L1 ON A.id_autore = L1.id_autore
JOIN LIBRO L2 ON A.id_autore = L2.id_autore
WHERE L1.genere = 'romanzo' AND L2.genere = 'saggio';
```

Soluzione attesa – IN:
```sql
SELECT id_autore, nome, cognome
FROM AUTORE
WHERE id_autore IN (SELECT id_autore FROM LIBRO WHERE genere = 'romanzo')
  AND id_autore IN (SELECT id_autore FROM LIBRO WHERE genere = 'saggio');
```

Soluzione attesa – INTERSECT:
```sql
SELECT A.id_autore, A.nome, A.cognome
FROM AUTORE A JOIN LIBRO L ON A.id_autore = L.id_autore
WHERE L.genere = 'romanzo'
INTERSECT
SELECT A.id_autore, A.nome, A.cognome
FROM AUTORE A JOIN LIBRO L ON A.id_autore = L.id_autore
WHERE L.genere = 'saggio';
```

## Pattern 4 – Divisione

### P4-1

**Domanda:** Mostra il codice, il nome e il cognome dei lettori che hanno preso in prestito libri di tutti i generi presenti nella biblioteca.

**Fonte:** [UNIBG](https://cs.unibg.it/abbadini/bd_22-23/soluzioni_sql_exe_4.pdf) – Es. 1 punto D: utenti che hanno preso in prestito libri di tutti i generi

**Adattamento:** UTENTE/PRESTITO/COPIA/DATILIBRO → LETTORE/PRESTITO_LIBRO/LIBRO; le viste di supporto sono sostituite da una sottoquery.

Soluzione attesa:
```sql
SELECT LE.id_lettore, LE.nome, LE.cognome
FROM LETTORE LE
JOIN PRESTITO_LIBRO P ON LE.id_lettore = P.id_lettore
JOIN LIBRO L ON P.id_libro = L.id_libro
GROUP BY LE.id_lettore, LE.nome, LE.cognome
HAVING COUNT(DISTINCT L.genere) = (SELECT COUNT(DISTINCT genere) FROM LIBRO);
```

### P4-2

**Domanda:** Mostra il codice dei lettori che hanno preso in prestito tutti i libri scritti da Umberto Eco presenti nella biblioteca.

**Fonte:** [UNIBG](https://cs.unibg.it/abbadini/bd_22-23/soluzioni_sql_exe_4.pdf) – Es. 2 punto C: clienti che hanno noleggiato tutti i film

**Adattamento:** Clienti/film → lettori/libri di un autore specifico.

Soluzione attesa:
```sql
SELECT P.id_lettore
FROM PRESTITO_LIBRO P
JOIN LIBRO L ON P.id_libro = L.id_libro
JOIN AUTORE A ON L.id_autore = A.id_autore
WHERE A.nome = 'Umberto' AND A.cognome = 'Eco'
GROUP BY P.id_lettore
HAVING COUNT(DISTINCT P.id_libro) = (SELECT COUNT(*)
                                     FROM LIBRO L2 JOIN AUTORE A2 ON L2.id_autore = A2.id_autore
                                     WHERE A2.nome = 'Umberto' AND A2.cognome = 'Eco');
```

### P4-3

**Domanda:** Mostra il codice, il nome e il cognome degli autori i cui libri presenti nella biblioteca sono stati tutti presi in prestito almeno una volta.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 3b: studenti che hanno conseguito il punteggio massimo possibile nei quiz di matematica (HAVING confrontato con il totale)

**Adattamento:** Il confronto con il totale dei quiz diventa il confronto con il numero di libri dell'autore.

Soluzione attesa:
```sql
SELECT A.id_autore, A.nome, A.cognome
FROM AUTORE A
JOIN LIBRO L ON A.id_autore = L.id_autore
JOIN PRESTITO_LIBRO P ON L.id_libro = P.id_libro
GROUP BY A.id_autore, A.nome, A.cognome
HAVING COUNT(DISTINCT L.id_libro) = (SELECT COUNT(*) FROM LIBRO L2 WHERE L2.id_autore = A.id_autore);
```

## Pattern 5 – Soluzioni multiple NOT IN/EXCEPT

### P5-1

**Domanda:** Mostra il codice, il nome e il cognome dei lettori che non hanno mai preso in prestito libri di genere “horror”.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 1a: atleti italiani che non hanno partecipato a nessuna gara di discesa libera (NOT IN)

**Adattamento:** Atleti/gare/disciplina → lettori/prestiti/genere.

Soluzione attesa – NOT IN:
```sql
SELECT id_lettore, nome, cognome
FROM LETTORE
WHERE id_lettore NOT IN (SELECT P.id_lettore
                         FROM PRESTITO_LIBRO P JOIN LIBRO L ON P.id_libro = L.id_libro
                         WHERE L.genere = 'horror');
```

Soluzione attesa – EXCEPT:
```sql
SELECT id_lettore, nome, cognome
FROM LETTORE
EXCEPT
SELECT LE.id_lettore, LE.nome, LE.cognome
FROM LETTORE LE
JOIN PRESTITO_LIBRO P ON LE.id_lettore = P.id_lettore
JOIN LIBRO L ON P.id_libro = L.id_libro
WHERE L.genere = 'horror';
```

### P5-2

**Domanda:** Mostra il codice e il nome delle sale per cui non è mai stata effettuata una prenotazione con ora di inizio successiva alle 18:00.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Query annidate es. 2a: aule in cui non si tengono mai lezioni di corsi del primo anno

**Adattamento:** Aule/lezioni → sale/prenotazioni; la condizione sull'anno del corso diventa una condizione sull'orario.

Soluzione attesa – NOT IN:
```sql
SELECT id_sala, nome
FROM SALA
WHERE id_sala NOT IN (SELECT id_sala FROM PRENOTAZIONE_SALA WHERE ora_inizio > TIME '18:00');
```

Soluzione attesa – EXCEPT:
```sql
SELECT id_sala, nome
FROM SALA
EXCEPT
SELECT S.id_sala, S.nome
FROM SALA S JOIN PRENOTAZIONE_SALA P ON S.id_sala = P.id_sala
WHERE P.ora_inizio > TIME '18:00';
```

### P5-3

**Domanda:** Mostra il codice e il titolo dei libri che non sono mai stati presi in prestito da lettori iscritti alla biblioteca prima del 1° gennaio 2020.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 2a: librerie in cui non è stata venduta nessuna pubblicazione di editori con sede a Torino

**Adattamento:** Librerie/vendite/editori → libri/prestiti/lettori; la sede dell'editore diventa la data di iscrizione del lettore.

Soluzione attesa – NOT IN:
```sql
SELECT id_libro, titolo
FROM LIBRO
WHERE id_libro NOT IN (SELECT P.id_libro
                       FROM PRESTITO_LIBRO P JOIN LETTORE LE ON P.id_lettore = LE.id_lettore
                       WHERE LE.data_iscrizione < DATE '2020-01-01');
```

Soluzione attesa – EXCEPT:
```sql
SELECT id_libro, titolo
FROM LIBRO
EXCEPT
SELECT L.id_libro, L.titolo
FROM LIBRO L
JOIN PRESTITO_LIBRO P ON L.id_libro = P.id_libro
JOIN LETTORE LE ON P.id_lettore = LE.id_lettore
WHERE LE.data_iscrizione < DATE '2020-01-01';
```

## Pattern 6 – Soluzioni multiple CTE/Correlazione

### P6-1

**Domanda:** Per ogni sala, mostra il codice della sala, la capacità e il numero di prenotazioni effettuate nell'ultima data in cui la sala è stata prenotata.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 6b: per ogni sala, numero di prenotazioni considerando solo l'ultima data di prenotazione (soluzione correlata e soluzione alternativa)

**Adattamento:** SALA_RIUNIONI → SALA; la soluzione alternativa con tabella derivata è riscritta come CTE.

Soluzione attesa – CTE:
```sql
WITH ultima AS (
    SELECT id_sala, MAX(data) AS ultima_data
    FROM PRENOTAZIONE_SALA
    GROUP BY id_sala)
SELECT S.id_sala, S.capacità, COUNT(*) AS num_prenotazioni
FROM SALA S
JOIN PRENOTAZIONE_SALA P ON S.id_sala = P.id_sala
JOIN ultima U ON P.id_sala = U.id_sala AND P.data = U.ultima_data
GROUP BY S.id_sala, S.capacità;
```

Soluzione attesa – CORRELAZIONE:
```sql
SELECT S.id_sala, S.capacità, COUNT(*) AS num_prenotazioni
FROM SALA S
JOIN PRENOTAZIONE_SALA P1 ON S.id_sala = P1.id_sala
WHERE P1.data = (SELECT MAX(P2.data)
                 FROM PRENOTAZIONE_SALA P2
                 WHERE P2.id_sala = P1.id_sala)
GROUP BY S.id_sala, S.capacità;
```

### P6-2

**Domanda:** Mostra il codice, il nome e il cognome dei lettori che hanno effettuato un numero di prestiti superiore al numero medio di prestiti per lettore, calcolato considerando solo i lettori che hanno effettuato almeno un prestito.

**Fonte:** [POLITO_P2](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/05/EserciziSQL-parte2_sol.pdf) – Es. 8b: contribuenti il cui reddito massimo supera la media dei redditi di tutte le dichiarazioni

**Adattamento:** Il confronto con una media globale diventa il confronto tra il conteggio per lettore e la media dei conteggi.

Soluzione attesa – CTE:
```sql
WITH conteggi AS (
    SELECT id_lettore, COUNT(*) AS num_prestiti
    FROM PRESTITO_LIBRO
    GROUP BY id_lettore)
SELECT LE.id_lettore, LE.nome, LE.cognome
FROM LETTORE LE
JOIN conteggi C ON LE.id_lettore = C.id_lettore
WHERE C.num_prestiti > (SELECT AVG(num_prestiti) FROM conteggi);
```

Soluzione attesa – CORRELAZIONE:
```sql
SELECT LE.id_lettore, LE.nome, LE.cognome
FROM LETTORE LE
WHERE (SELECT COUNT(*) FROM PRESTITO_LIBRO P WHERE P.id_lettore = LE.id_lettore)
      > (SELECT COUNT(*) * 1.0 / COUNT(DISTINCT id_lettore) FROM PRESTITO_LIBRO);
```

### P6-3

**Domanda:** Mostra il nome, la capacità e il piano delle sale che hanno la capacità massima tra le sale dello stesso piano.

**Fonte:** [POLITO_P1](https://dbdmg.polito.it/dbdmg_web/wp-content/uploads/2024/04/EserciziSQL-parte1_sol.pdf) – Correlazione es. 1a: alloggi con superficie superiore alla superficie media degli alloggi della stessa città

**Adattamento:** Alloggi/città/superficie media → sale/piano/capacità massima.

Soluzione attesa – CTE:
```sql
WITH max_piano AS (
    SELECT piano, MAX(capacità) AS cap_max
    FROM SALA
    GROUP BY piano)
SELECT S.nome, S.capacità, S.piano
FROM SALA S
JOIN max_piano M ON S.piano = M.piano AND S.capacità = M.cap_max;
```

Soluzione attesa – CORRELAZIONE:
```sql
SELECT S1.nome, S1.capacità, S1.piano
FROM SALA S1
WHERE S1.capacità = (SELECT MAX(S2.capacità)
                     FROM SALA S2
                     WHERE S2.piano = S1.piano);
```
