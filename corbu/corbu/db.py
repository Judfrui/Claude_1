import json
import os
import sqlite3
from pathlib import Path

MODES = {
    "QF": "Quantité forfaitaire",
    "QP": "Quantité présumée",
    "FF": "Forfait",
    "PM": "Pour mémoire",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS bib_lot (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    titre TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bib_article (
    id INTEGER PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES bib_lot(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    titre TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    unite TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT 'QF',
    prix_ref REAL
);
CREATE TABLE IF NOT EXISTS projet (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    reference TEXT NOT NULL DEFAULT '',
    maitre_ouvrage TEXT NOT NULL DEFAULT '',
    adresse TEXT NOT NULL DEFAULT '',
    cree_le TEXT NOT NULL DEFAULT (date('now'))
);
CREATE TABLE IF NOT EXISTS projet_lot (
    id INTEGER PRIMARY KEY,
    projet_id INTEGER NOT NULL REFERENCES projet(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    titre TEXT NOT NULL,
    UNIQUE (projet_id, code)
);
CREATE TABLE IF NOT EXISTS poste (
    id INTEGER PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES projet_lot(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    titre TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    unite TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT 'QF',
    prix_unitaire REAL
);
CREATE TABLE IF NOT EXISTS metre_ligne (
    id INTEGER PRIMARY KEY,
    poste_id INTEGER NOT NULL REFERENCES poste(id) ON DELETE CASCADE,
    libelle TEXT NOT NULL DEFAULT '',
    formule TEXT NOT NULL,
    valeur REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS offre (
    id INTEGER PRIMARY KEY,
    projet_id INTEGER NOT NULL REFERENCES projet(id) ON DELETE CASCADE,
    entreprise TEXT NOT NULL,
    fichier TEXT NOT NULL DEFAULT '',
    importee_le TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (projet_id, entreprise)
);
CREATE TABLE IF NOT EXISTS offre_prix (
    offre_id INTEGER NOT NULL REFERENCES offre(id) ON DELETE CASCADE,
    poste_id INTEGER NOT NULL REFERENCES poste(id) ON DELETE CASCADE,
    quantite REAL,
    pu REAL,
    total REAL,
    PRIMARY KEY (offre_id, poste_id)
);
"""

BIBLIOTHEQUE_PAR_DEFAUT = Path(__file__).parent / "data" / "bibliotheque_belge.json"


def connecter(chemin: str | None = None) -> sqlite3.Connection:
    chemin = chemin or os.environ.get("CORBU_DB", "corbu.db")
    conn = sqlite3.connect(chemin, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialiser(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM bib_lot").fetchone()[0] == 0:
        importer_bibliotheque(conn, json.loads(BIBLIOTHEQUE_PAR_DEFAUT.read_text("utf-8")))
    conn.commit()


def importer_bibliotheque(conn: sqlite3.Connection, donnees: dict) -> None:
    for lot in donnees["lots"]:
        lot_id = conn.execute(
            "INSERT INTO bib_lot (code, titre) VALUES (?, ?) "
            "ON CONFLICT(code) DO UPDATE SET titre = excluded.titre RETURNING id",
            (lot["code"], lot["titre"]),
        ).fetchone()[0]
        for art in lot.get("articles", []):
            if art.get("mode", "QF") not in MODES:
                raise ValueError(f"Mode de métré inconnu : {art['mode']}")
            conn.execute(
                "INSERT INTO bib_article (lot_id, code, titre, description, unite, mode, prix_ref) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(code) DO UPDATE SET "
                "lot_id = excluded.lot_id, titre = excluded.titre, description = excluded.description, "
                "unite = excluded.unite, mode = excluded.mode, prix_ref = excluded.prix_ref",
                (lot_id, art["code"], art["titre"], art.get("description", ""),
                 art.get("unite", ""), art.get("mode", "QF"), art.get("prix_ref")),
            )


def exporter_bibliotheque(conn: sqlite3.Connection) -> dict:
    lots = []
    for lot in conn.execute("SELECT * FROM bib_lot ORDER BY code"):
        articles = conn.execute(
            "SELECT code, titre, description, unite, mode, prix_ref FROM bib_article "
            "WHERE lot_id = ? ORDER BY code", (lot["id"],)).fetchall()
        lots.append({"code": lot["code"], "titre": lot["titre"],
                     "articles": [dict(a) for a in articles]})
    return {"lots": lots}


def postes_du_projet(conn: sqlite3.Connection, projet_id: int) -> list[dict]:
    """Postes du projet avec leur lot et leur quantité, triés par lot puis code."""
    lignes = conn.execute(
        """
        SELECT p.*, l.code AS lot_code, l.titre AS lot_titre,
               COALESCE((SELECT SUM(valeur) FROM metre_ligne m WHERE m.poste_id = p.id), 0) AS quantite
        FROM poste p JOIN projet_lot l ON l.id = p.lot_id
        WHERE l.projet_id = ?
        ORDER BY l.code, p.code
        """,
        (projet_id,),
    ).fetchall()
    return [dict(r) for r in lignes]


def lots_du_projet(conn: sqlite3.Connection, projet_id: int) -> list[dict]:
    lots = [dict(r) for r in conn.execute(
        "SELECT * FROM projet_lot WHERE projet_id = ? ORDER BY code", (projet_id,))]
    postes = postes_du_projet(conn, projet_id)
    for lot in lots:
        lot["postes"] = [p for p in postes if p["lot_id"] == lot["id"]]
        lot["total"] = sum(montant(p) for p in lot["postes"])
    return lots


def montant(poste: dict) -> float:
    if poste["mode"] == "PM" or poste["prix_unitaire"] is None:
        return 0.0
    if poste["mode"] == "FF":
        return poste["prix_unitaire"]
    return poste["quantite"] * poste["prix_unitaire"]
