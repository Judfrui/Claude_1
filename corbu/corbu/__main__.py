import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn

from .app import creer_app

EXECUTABLE = getattr(sys, "frozen", False)


def _db_par_defaut():
    """Version installée : la base vit dans le profil utilisateur, pas dans Program Files."""
    if not EXECUTABLE:
        return None
    dossier = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Corbu"
    dossier.mkdir(parents=True, exist_ok=True)
    return str(dossier / "corbu.db")


def main():
    parser = argparse.ArgumentParser(prog="corbu", description="Lance le serveur Corbu.")
    parser.add_argument("--db", default=_db_par_defaut(), help="fichier de base de données (défaut : corbu.db)")
    parser.add_argument("--hote", default="127.0.0.1",
                        help="adresse d'écoute ; 0.0.0.0 pour partager sur le réseau du bureau")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--navigateur", action="store_true", default=EXECUTABLE,
                        help="ouvre Corbu dans le navigateur au démarrage")
    args = parser.parse_args()
    app = creer_app(args.db)
    if args.navigateur:
        threading.Timer(1.5, webbrowser.open, [f"http://127.0.0.1:{args.port}"]).start()
    print(f"Corbu est lancé : http://127.0.0.1:{args.port} — fermez cette fenêtre pour l'arrêter.")
    uvicorn.run(app, host=args.hote, port=args.port)


if __name__ == "__main__":
    main()
