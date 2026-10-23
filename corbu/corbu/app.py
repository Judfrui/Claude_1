import json
import os
import sqlite3
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, exports, offres
from .formules import FormuleInvalide, evaluer

ICI = Path(__file__).parent
TAILLE_MAX_OFFRE = 20 * 1024 * 1024
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

templates = Jinja2Templates(directory=ICI / "templates")
templates.env.filters["eur"] = lambda v: "" if v is None else exports.nombre_fr(v)
templates.env.filters["qte"] = lambda v: "" if v is None else exports.nombre_fr(v, 3).rstrip("0").rstrip(",")
templates.env.filters["pct"] = lambda v: "" if v is None else f"{v:+.1%}".replace(".", ",")
templates.env.globals["MODES"] = db.MODES


def creer_app(chemin_db: str | None = None) -> FastAPI:
    chemin_db = chemin_db or os.environ.get("CORBU_DB", "corbu.db")
    conn = db.connecter(chemin_db)
    db.initialiser(conn)
    conn.close()

    app = FastAPI(title="Corbu")
    app.mount("/static", StaticFiles(directory=ICI / "static"), name="static")

    def connexion():
        conn = db.connecter(chemin_db)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    Conn = Annotated[object, Depends(connexion)]

    def projet_ou_404(conn, projet_id):
        projet = conn.execute("SELECT * FROM projet WHERE id = ?", (projet_id,)).fetchone()
        if projet is None:
            raise HTTPException(404, "Projet introuvable")
        return projet

    def poste_ou_404(conn, poste_id):
        poste = conn.execute(
            "SELECT p.*, l.projet_id, l.code AS lot_code, l.titre AS lot_titre FROM poste p "
            "JOIN projet_lot l ON l.id = p.lot_id WHERE p.id = ?", (poste_id,)).fetchone()
        if poste is None:
            raise HTTPException(404, "Poste introuvable")
        return poste

    def retour(url, message=None):
        if message:
            url += ("&" if "?" in url else "?") + "msg=" + quote(message)
        return RedirectResponse(url, status_code=303)

    def fichier(contenu, nom, type_mime):
        return Response(contenu, media_type=type_mime,
                        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nom)}"})

    def lot_du_projet(conn, projet_id, code, titre):
        conn.execute("INSERT INTO projet_lot (projet_id, code, titre) VALUES (?, ?, ?) "
                     "ON CONFLICT(projet_id, code) DO NOTHING", (projet_id, code, titre))
        return conn.execute("SELECT id FROM projet_lot WHERE projet_id = ? AND code = ?",
                            (projet_id, code)).fetchone()[0]

    def mode_valide(mode):
        if mode not in db.MODES:
            raise HTTPException(400, "Mode de métré inconnu")
        return mode

    # Projets

    @app.get("/")
    def accueil(request: Request, conn: Conn, msg: str = ""):
        projets = conn.execute("SELECT * FROM projet ORDER BY cree_le DESC, id DESC").fetchall()
        return templates.TemplateResponse(request, "index.html", {"projets": projets, "msg": msg})

    @app.post("/projets")
    def creer_projet(conn: Conn, nom: Annotated[str, Form()], reference: Annotated[str, Form()] = "",
                     maitre_ouvrage: Annotated[str, Form()] = "", adresse: Annotated[str, Form()] = ""):
        if not nom.strip():
            return retour("/", "Le nom du projet est obligatoire.")
        projet_id = conn.execute(
            "INSERT INTO projet (nom, reference, maitre_ouvrage, adresse) VALUES (?, ?, ?, ?)",
            (nom.strip(), reference.strip(), maitre_ouvrage.strip(), adresse.strip())).lastrowid
        return retour(f"/projets/{projet_id}")

    @app.get("/projets/{projet_id}")
    def voir_projet(request: Request, conn: Conn, projet_id: int, msg: str = ""):
        projet = projet_ou_404(conn, projet_id)
        lots = db.lots_du_projet(conn, projet_id)
        bibliotheque = conn.execute(
            "SELECT a.*, l.code AS lot_code, l.titre AS lot_titre FROM bib_article a "
            "JOIN bib_lot l ON l.id = a.lot_id ORDER BY a.code").fetchall()
        return templates.TemplateResponse(request, "projet.html", {
            "projet": projet, "lots": lots, "bibliotheque": bibliotheque,
            "total": sum(l["total"] for l in lots), "msg": msg})

    @app.post("/projets/{projet_id}/modifier")
    def modifier_projet(conn: Conn, projet_id: int, nom: Annotated[str, Form()],
                        reference: Annotated[str, Form()] = "", maitre_ouvrage: Annotated[str, Form()] = "",
                        adresse: Annotated[str, Form()] = ""):
        projet_ou_404(conn, projet_id)
        if not nom.strip():
            return retour(f"/projets/{projet_id}", "Le nom du projet est obligatoire.")
        conn.execute("UPDATE projet SET nom = ?, reference = ?, maitre_ouvrage = ?, adresse = ? WHERE id = ?",
                     (nom.strip(), reference.strip(), maitre_ouvrage.strip(), adresse.strip(), projet_id))
        return retour(f"/projets/{projet_id}", "Projet mis à jour.")

    @app.post("/projets/{projet_id}/supprimer")
    def supprimer_projet(conn: Conn, projet_id: int):
        conn.execute("DELETE FROM projet WHERE id = ?", (projet_id,))
        return retour("/", "Projet supprimé.")

    @app.post("/projets/{projet_id}/articles")
    def ajouter_articles(conn: Conn, projet_id: int, articles: Annotated[list[int], Form()] = []):
        projet_ou_404(conn, projet_id)
        ajoutes = 0
        for article_id in articles:
            art = conn.execute(
                "SELECT a.*, l.code AS lot_code, l.titre AS lot_titre FROM bib_article a "
                "JOIN bib_lot l ON l.id = a.lot_id WHERE a.id = ?", (article_id,)).fetchone()
            if art is None:
                continue
            lot_id = lot_du_projet(conn, projet_id, art["lot_code"], art["lot_titre"])
            if conn.execute("SELECT 1 FROM poste WHERE lot_id = ? AND code = ?", (lot_id, art["code"])).fetchone():
                continue
            conn.execute(
                "INSERT INTO poste (lot_id, code, titre, description, unite, mode, prix_unitaire) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (lot_id, art["code"], art["titre"], art["description"], art["unite"], art["mode"], art["prix_ref"]))
            ajoutes += 1
        return retour(f"/projets/{projet_id}", f"{ajoutes} poste(s) ajouté(s) depuis la bibliothèque.")

    @app.post("/projets/{projet_id}/postes")
    def creer_poste(conn: Conn, projet_id: int, lot_code: Annotated[str, Form()],
                    lot_titre: Annotated[str, Form()], code: Annotated[str, Form()],
                    titre: Annotated[str, Form()], unite: Annotated[str, Form()] = "",
                    mode: Annotated[str, Form()] = "QF"):
        projet_ou_404(conn, projet_id)
        if not (lot_code.strip() and code.strip() and titre.strip()):
            return retour(f"/projets/{projet_id}", "Lot, code et intitulé sont obligatoires.")
        existant = conn.execute(
            "SELECT 1 FROM poste p JOIN projet_lot l ON l.id = p.lot_id WHERE l.projet_id = ? AND p.code = ?",
            (projet_id, code.strip())).fetchone()
        if existant:
            return retour(f"/projets/{projet_id}", f"Le code {code.strip()} existe déjà dans ce projet.")
        lot_id = lot_du_projet(conn, projet_id, lot_code.strip(), lot_titre.strip() or lot_code.strip())
        poste_id = conn.execute(
            "INSERT INTO poste (lot_id, code, titre, unite, mode) VALUES (?, ?, ?, ?, ?)",
            (lot_id, code.strip(), titre.strip(), unite.strip(), mode_valide(mode))).lastrowid
        return retour(f"/postes/{poste_id}")

    @app.post("/lots/{lot_id}/supprimer")
    def supprimer_lot(conn: Conn, lot_id: int):
        lot = conn.execute("SELECT projet_id FROM projet_lot WHERE id = ?", (lot_id,)).fetchone()
        if lot is None:
            raise HTTPException(404, "Lot introuvable")
        conn.execute("DELETE FROM projet_lot WHERE id = ?", (lot_id,))
        return retour(f"/projets/{lot['projet_id']}", "Lot supprimé.")

    # Postes et métré

    @app.get("/postes/{poste_id}")
    def voir_poste(request: Request, conn: Conn, poste_id: int, msg: str = ""):
        poste = poste_ou_404(conn, poste_id)
        lignes = conn.execute("SELECT * FROM metre_ligne WHERE poste_id = ? ORDER BY id", (poste_id,)).fetchall()
        return templates.TemplateResponse(request, "poste.html", {
            "poste": poste, "lignes": lignes, "quantite": sum(l["valeur"] for l in lignes), "msg": msg})

    @app.post("/postes/{poste_id}")
    def modifier_poste(conn: Conn, poste_id: int, titre: Annotated[str, Form()],
                       description: Annotated[str, Form()] = "", unite: Annotated[str, Form()] = "",
                       mode: Annotated[str, Form()] = "QF", prix_unitaire: Annotated[str, Form()] = ""):
        poste_ou_404(conn, poste_id)
        pu = offres.lire_nombre(prix_unitaire)
        conn.execute("UPDATE poste SET titre = ?, description = ?, unite = ?, mode = ?, prix_unitaire = ? WHERE id = ?",
                     (titre.strip(), description.strip(), unite.strip(), mode_valide(mode), pu, poste_id))
        return retour(f"/postes/{poste_id}", "Poste enregistré.")

    @app.post("/postes/{poste_id}/supprimer")
    def supprimer_poste(conn: Conn, poste_id: int):
        poste = poste_ou_404(conn, poste_id)
        conn.execute("DELETE FROM poste WHERE id = ?", (poste_id,))
        return retour(f"/projets/{poste['projet_id']}", "Poste supprimé.")

    @app.post("/postes/{poste_id}/metre")
    def ajouter_ligne(conn: Conn, poste_id: int, formule: Annotated[str, Form()],
                      libelle: Annotated[str, Form()] = ""):
        poste_ou_404(conn, poste_id)
        try:
            valeur = evaluer(formule)
        except FormuleInvalide as exc:
            return retour(f"/postes/{poste_id}", str(exc))
        conn.execute("INSERT INTO metre_ligne (poste_id, libelle, formule, valeur) VALUES (?, ?, ?, ?)",
                     (poste_id, libelle.strip(), formule.strip(), valeur))
        return retour(f"/postes/{poste_id}")

    @app.post("/metre/{ligne_id}/supprimer")
    def supprimer_ligne(conn: Conn, ligne_id: int):
        ligne = conn.execute("SELECT poste_id FROM metre_ligne WHERE id = ?", (ligne_id,)).fetchone()
        if ligne is None:
            raise HTTPException(404, "Ligne introuvable")
        conn.execute("DELETE FROM metre_ligne WHERE id = ?", (ligne_id,))
        return retour(f"/postes/{ligne['poste_id']}")

    # Exports

    @app.get("/projets/{projet_id}/csc.docx")
    def export_csc(conn: Conn, projet_id: int):
        projet = projet_ou_404(conn, projet_id)
        return fichier(exports.csc_docx(conn, projet_id), f"CSC - {projet['nom']}.docx", DOCX)

    @app.get("/projets/{projet_id}/metre.xlsx")
    def export_metre(conn: Conn, projet_id: int, prix: bool = False):
        projet = projet_ou_404(conn, projet_id)
        nom = f"{'Estimation' if prix else 'Métré récapitulatif'} - {projet['nom']}.xlsx"
        return fichier(exports.metre_xlsx(conn, projet_id, avec_prix=prix), nom, XLSX)

    # Offres

    def page_offres(request, conn, projet_id, seuil, msg="", rapport=None):
        projet = projet_ou_404(conn, projet_id)
        return templates.TemplateResponse(request, "offres.html", {
            "projet": projet, "analyse": offres.analyser(conn, projet_id, seuil / 100),
            "seuil": seuil, "msg": msg, "rapport": rapport or []})

    @app.get("/projets/{projet_id}/offres")
    def voir_offres(request: Request, conn: Conn, projet_id: int, seuil: int = 25, msg: str = ""):
        return page_offres(request, conn, projet_id, seuil, msg)

    @app.post("/projets/{projet_id}/offres")
    async def importer_offres(request: Request, conn: Conn, projet_id: int,
                              fichiers: Annotated[list[UploadFile], File()]):
        projet_ou_404(conn, projet_id)
        postes = db.postes_du_projet(conn, projet_id)
        rapport = []
        for f in fichiers:
            contenu = await f.read(TAILLE_MAX_OFFRE + 1)
            nom = Path(f.filename or "offre.xlsx").name
            if len(contenu) > TAILLE_MAX_OFFRE:
                rapport.append({"fichier": nom, "erreur": "fichier trop volumineux (20 Mo max.)"})
                continue
            try:
                lue = offres.lire_offre(contenu, nom, postes)
            except offres.OffreIllisible as exc:
                rapport.append({"fichier": nom, "erreur": str(exc)})
                continue
            offres.enregistrer_offre(conn, projet_id, lue, nom)
            lots = sorted({p["lot_code"] for p in postes if p["id"] in lue["prix"]})
            rapport.append({"fichier": nom, "entreprise": lue["entreprise"], "lots": lots,
                            "postes": len(lue["prix"]), "inconnus": lue["inconnus"]})
        conn.commit()
        return page_offres(request, conn, projet_id, 25, rapport=rapport)

    @app.post("/offres/{offre_id}/supprimer")
    def supprimer_offre(conn: Conn, offre_id: int):
        offre = conn.execute("SELECT projet_id, entreprise FROM offre WHERE id = ?", (offre_id,)).fetchone()
        if offre is None:
            raise HTTPException(404, "Offre introuvable")
        conn.execute("DELETE FROM offre WHERE id = ?", (offre_id,))
        return retour(f"/projets/{offre['projet_id']}/offres", f"Offre de {offre['entreprise']} supprimée.")

    @app.get("/projets/{projet_id}/analyse.xlsx")
    def export_analyse(conn: Conn, projet_id: int, seuil: int = 25):
        projet = projet_ou_404(conn, projet_id)
        analyse = offres.analyser(conn, projet_id, seuil / 100)
        return fichier(exports.analyse_xlsx(conn, projet_id, analyse),
                       f"Analyse des offres - {projet['nom']}.xlsx", XLSX)

    # Bibliothèque

    @app.get("/bibliotheque")
    def voir_bibliotheque(request: Request, conn: Conn, msg: str = ""):
        lots = [dict(l) for l in conn.execute("SELECT * FROM bib_lot ORDER BY code")]
        for lot in lots:
            lot["articles"] = conn.execute(
                "SELECT * FROM bib_article WHERE lot_id = ? ORDER BY code", (lot["id"],)).fetchall()
        return templates.TemplateResponse(request, "bibliotheque.html", {"lots": lots, "msg": msg})

    @app.post("/bibliotheque/articles")
    def enregistrer_article(conn: Conn, lot_code: Annotated[str, Form()], lot_titre: Annotated[str, Form()],
                            code: Annotated[str, Form()], titre: Annotated[str, Form()],
                            description: Annotated[str, Form()] = "", unite: Annotated[str, Form()] = "",
                            mode: Annotated[str, Form()] = "QF", prix_ref: Annotated[str, Form()] = ""):
        if not (lot_code.strip() and code.strip() and titre.strip()):
            return retour("/bibliotheque", "Lot, code et intitulé sont obligatoires.")
        db.importer_bibliotheque(conn, {"lots": [{
            "code": lot_code.strip(), "titre": lot_titre.strip() or lot_code.strip(),
            "articles": [{"code": code.strip(), "titre": titre.strip(), "description": description.strip(),
                          "unite": unite.strip(), "mode": mode_valide(mode),
                          "prix_ref": offres.lire_nombre(prix_ref)}]}]})
        return retour("/bibliotheque", f"Article {code.strip()} enregistré.")

    @app.post("/bibliotheque/articles/{article_id}/supprimer")
    def supprimer_article(conn: Conn, article_id: int):
        conn.execute("DELETE FROM bib_article WHERE id = ?", (article_id,))
        return retour("/bibliotheque", "Article supprimé.")

    @app.get("/bibliotheque.json")
    def export_bibliotheque(conn: Conn):
        contenu = json.dumps(db.exporter_bibliotheque(conn), ensure_ascii=False, indent=2)
        return fichier(contenu.encode("utf-8"), "bibliotheque-corbu.json", "application/json")

    @app.post("/bibliotheque/import")
    async def importer_bibliotheque(conn: Conn, fichier_json: Annotated[UploadFile, File()]):
        try:
            donnees = json.loads(await fichier_json.read())
            db.importer_bibliotheque(conn, donnees)
        except (ValueError, KeyError, TypeError, sqlite3.Error):
            conn.rollback()
            return retour("/bibliotheque", "Fichier de bibliothèque invalide.")
        return retour("/bibliotheque", "Bibliothèque importée.")

    return app
