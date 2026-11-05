"""Crea db/biblioteca.duckdb con lo schema Biblioteca e dati di prova.

I dati sono scritti a mano per far emergere errori tipici:
NULL (prestiti non restituiti, autori vivi), lettori senza prestiti,
sale con la stessa capacità sullo stesso piano, autori con solo alcuni libri prestati.
"""
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).with_name("biblioteca.duckdb")

SCHEMA = """
CREATE TABLE AUTORE (
    id_autore INTEGER PRIMARY KEY, nome VARCHAR, cognome VARCHAR,
    nazionalità VARCHAR, data_nascita DATE, data_morte DATE);
CREATE TABLE LIBRO (
    id_libro INTEGER PRIMARY KEY, id_autore INTEGER REFERENCES AUTORE(id_autore),
    titolo VARCHAR, anno_pubblicazione INTEGER, genere VARCHAR, numero_copie INTEGER);
CREATE TABLE LETTORE (
    id_lettore INTEGER PRIMARY KEY, nome VARCHAR, cognome VARCHAR, email VARCHAR,
    telefono VARCHAR, indirizzo VARCHAR, data_iscrizione DATE);
CREATE TABLE PRESTITO_LIBRO (
    id_libro INTEGER REFERENCES LIBRO(id_libro), id_lettore INTEGER REFERENCES LETTORE(id_lettore),
    data_prestito DATE, data_restituzione DATE, note VARCHAR,
    PRIMARY KEY (id_libro, id_lettore, data_prestito));
CREATE TABLE DIPENDENTE (
    id_dipendente INTEGER PRIMARY KEY, nome VARCHAR, cognome VARCHAR, ruolo VARCHAR,
    data_assunzione DATE, email VARCHAR, telefono VARCHAR);
CREATE TABLE SALA (
    id_sala INTEGER PRIMARY KEY, id_dipendente_responsabile INTEGER REFERENCES DIPENDENTE(id_dipendente),
    nome VARCHAR, capacità INTEGER, piano INTEGER, tipologia VARCHAR);
CREATE TABLE PRENOTAZIONE_SALA (
    id_lettore INTEGER REFERENCES LETTORE(id_lettore), data DATE, ora_inizio TIME, ora_fine TIME,
    id_sala INTEGER REFERENCES SALA(id_sala), note VARCHAR,
    PRIMARY KEY (id_lettore, data, ora_inizio));
"""

AUTORI = [
    (1, "Umberto", "Eco", "italiana", "1932-01-05", "2016-02-19"),
    (2, "Italo", "Calvino", "italiana", "1923-10-15", "1985-09-19"),
    (3, "Alessandro", "Baricco", "italiana", "1958-01-25", None),
    (4, "Paolo", "Giordano", "italiana", "1982-12-19", None),
    (5, "Donato", "Carrisi", "italiana", "1973-03-25", None),
    (6, "John Ronald Reuel", "Tolkien", "inglese", "1892-01-03", "1973-09-02"),
    (7, "Joanne", "Rowling", "inglese", "1965-07-31", None),
    (8, "Agatha", "Christie", "inglese", "1890-09-15", "1976-01-12"),
    (9, "Stephen", "King", "statunitense", "1947-09-21", None),
    (10, "Fëdor", "Dostoevskij", "russa", "1821-11-11", "1881-02-09"),
    (11, "Mary", "Shelley", "inglese", "1797-08-30", "1851-02-01"),
]

LIBRI = [
    (1, 1, "Il nome della rosa", 1980, "giallo", 4),
    (2, 1, "Il pendolo di Foucault", 1988, "romanzo", 2),
    (3, 1, "Come si fa una tesi di laurea", 1977, "saggio", 1),
    (4, 2, "Il barone rampante", 1957, "romanzo", 3),
    (5, 2, "Lezioni americane", 1988, "saggio", 2),
    (6, 2, "Le cosmicomiche", 1965, "fantascienza", 1),
    (7, 3, "Seta", 1996, "romanzo", 5),
    (8, 3, "The Game", 2018, "saggio", 2),
    (9, 4, "La solitudine dei numeri primi", 2008, "romanzo", 6),
    (10, 5, "Il suggeritore", 2009, "giallo", 3),
    (11, 5, "La ragazza nella nebbia", 2015, "giallo", 2),
    (12, 6, "Il Signore degli Anelli", 1954, "fantasy", 7),
    (13, 6, "Lo Hobbit", 1937, "fantasy", 4),
    (14, 7, "Harry Potter e la pietra filosofale", 1997, "fantasy", 8),
    (15, 7, "Il seggio vacante", 2012, "romanzo", 1),
    (16, 8, "Dieci piccoli indiani", 1939, "giallo", 3),
    (17, 9, "It", 1986, "horror", 2),
    (18, 9, "Shining", 1977, "horror", 3),
    (19, 9, "Misery", 1987, "horror", 1),
    (20, 10, "Delitto e castigo", 1866, "romanzo", 2),
    (21, 11, "Frankenstein", 1818, "horror", 2),
    (22, 9, "Fairy Tale", 2022, "fantasy", 2),
]

LETTORI = [
    (1, "Marco", "Rossi", "2016-03-10"),
    (2, "Giulia", "Bianchi", "2018-09-01"),
    (3, "Luca", "Verdi", "2019-11-20"),
    (4, "Sara", "Neri", "2021-02-14"),
    (5, "Andrea", "Russo", "2022-06-30"),
    (6, "Chiara", "Ferrari", "2023-01-09"),
    (7, "Matteo", "Esposito", "2024-02-01"),
    (8, "Francesca", "Romano", "2024-05-15"),
    (9, "Davide", "Colombo", "2024-10-03"),
    (10, "Elena", "Ricci", "2025-01-20"),
    (11, "Simone", "Marino", "2025-03-11"),
    (12, "Laura", "Greco", "2025-09-05"),  # nessun prestito, nessuna prenotazione
]

PRESTITI = [  # (id_libro, id_lettore, data_prestito, data_restituzione, note)
    (1, 1, "2025-02-10", "2025-03-01", None),
    (2, 1, "2024-03-05", "2024-03-25", None),
    (3, 1, "2025-05-12", "2025-05-30", None),
    (6, 1, "2024-07-01", "2024-07-20", None),
    (12, 1, "2026-01-08", "2026-02-01", None),
    (17, 1, "2026-03-03", "2026-03-20", None),
    (1, 2, "2024-11-05", "2024-11-28", None),
    (3, 2, "2025-09-12", "2025-10-01", None),
    (14, 2, "2025-12-01", "2025-12-20", None),
    (10, 2, "2026-02-14", "2026-03-01", None),
    (1, 3, "2025-06-01", "2025-06-21", None),
    (1, 3, "2026-01-15", None, "Sollecito inviato"),
    (2, 3, "2025-07-10", "2025-08-01", None),
    (3, 3, "2024-10-02", "2024-10-30", None),
    (18, 3, "2026-04-04", "2026-04-25", None),
    (12, 4, "2025-04-18", "2025-05-10", None),
    (9, 4, "2026-05-02", "2026-05-20", None),
    (11, 5, "2025-01-22", "2025-02-12", None),
    (16, 5, "2025-08-08", "2025-08-30", "Copertina danneggiata"),
    (19, 5, "2026-06-11", "2026-07-01", None),
    (14, 6, "2025-03-03", "2025-03-24", None),
    (1, 6, "2026-02-20", "2026-03-10", None),
    (7, 7, "2024-09-09", "2024-09-30", None),
    (9, 7, "2025-11-11", "2025-12-02", None),
    (8, 7, "2026-08-01", "2026-08-21", None),
    (9, 8, "2025-05-05", "2025-05-25", None),
    (20, 8, "2026-03-15", "2026-04-05", None),
    (14, 8, "2026-10-02", None, None),
    (21, 9, "2026-07-20", None, None),
    (4, 10, "2025-10-10", "2025-10-31", None),
    (7, 10, "2026-10-20", None, None),
]

DIPENDENTI = [
    (1, "Paolo", "Gallo", "bibliotecario", "2010-04-01"),
    (2, "Anna", "Conti", "responsabile sale", "2015-09-15"),
    (3, "Roberto", "Costa", "archivista", "2018-01-10"),
    (4, "Marta", "De Luca", "bibliotecaria", "2020-06-01"),
    (5, "Giorgio", "Mancini", "direttore", "2008-02-01"),
]

SALE = [  # (id_sala, id_dipendente_responsabile, nome, capacità, piano, tipologia)
    (1, 2, "Sala Studio A", 20, 0, "studio"),
    (2, 2, "Sala Studio B", 12, 0, "studio"),
    (3, 4, "Sala Lettura Calvino", 30, 1, "lettura"),
    (4, 4, "Sala Conferenze", 80, 1, "conferenza"),
    (5, 1, "Sala Gruppi", 8, 2, "studio"),
    (6, 1, "Sala Multimediale", 15, 2, "multimediale"),
    (7, 3, "Sala Archivio", 15, 2, "lettura"),
    (8, 5, "Sala Riunioni", 10, 3, "conferenza"),
]

PRENOTAZIONI = [  # (id_lettore, data, ora_inizio, ora_fine, id_sala, note)
    (1, "2026-02-10", "09:00", "11:00", 2, None),
    (1, "2026-03-05", "10:00", "12:00", 1, None),
    (1, "2026-04-20", "14:00", "16:00", 1, None),
    (2, "2026-04-20", "10:00", "12:00", 1, None),
    (11, "2026-03-12", "09:00", "10:30", 1, None),
    (11, "2026-04-02", "15:00", "17:00", 2, None),
    (11, "2026-04-15", "16:00", "18:00", 5, None),
    (7, "2026-03-18", "11:00", "13:00", 1, None),
    (7, "2026-05-06", "09:00", "11:00", 2, None),
    (8, "2026-03-25", "15:00", "17:00", 3, None),
    (8, "2026-04-08", "15:00", "17:00", 3, None),
    (9, "2026-04-28", "10:00", "12:00", 3, None),
    (3, "2026-03-30", "20:00", "22:00", 4, "Presentazione libro"),
    (4, "2026-04-11", "09:00", "12:00", 5, None),
    (5, "2026-05-14", "10:00", "12:00", 6, None),
    (6, "2026-01-22", "08:30", "10:00", 7, None),
    (2, "2026-06-03", "19:00", "21:00", 8, "Riunione gruppo di lettura"),
]


def build(path: Path = DB_PATH) -> Path:
    path.unlink(missing_ok=True)
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    con.executemany("INSERT INTO AUTORE VALUES (?, ?, ?, ?, ?, ?)", AUTORI)
    con.executemany("INSERT INTO LIBRO VALUES (?, ?, ?, ?, ?, ?)", LIBRI)
    con.executemany(
        "INSERT INTO LETTORE VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(i, n, c, f"{n.lower()}.{c.lower()}@mail.it", f"33{i:08d}", f"Via Roma {i}, Torino", d)
         for i, n, c, d in LETTORI],
    )
    con.executemany("INSERT INTO PRESTITO_LIBRO VALUES (?, ?, ?, ?, ?)", PRESTITI)
    con.executemany(
        "INSERT INTO DIPENDENTE VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(i, n, c, r, d, f"{n.lower()}.{c.lower().replace(' ', '')}@biblioteca.it", f"011{i:07d}")
         for i, n, c, r, d in DIPENDENTI],
    )
    con.executemany("INSERT INTO SALA VALUES (?, ?, ?, ?, ?, ?)", SALE)
    con.executemany("INSERT INTO PRENOTAZIONE_SALA VALUES (?, ?, ?, ?, ?, ?)", PRENOTAZIONI)
    con.close()
    return path


if __name__ == "__main__":
    print("Creato", build())
