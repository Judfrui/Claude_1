import argparse

import uvicorn

from .app import creer_app


def main():
    parser = argparse.ArgumentParser(prog="corbu", description="Lance le serveur Corbu.")
    parser.add_argument("--db", default=None, help="fichier de base de données (défaut : corbu.db)")
    parser.add_argument("--hote", default="127.0.0.1",
                        help="adresse d'écoute ; 0.0.0.0 pour partager sur le réseau du bureau")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(creer_app(args.db), host=args.hote, port=args.port)


if __name__ == "__main__":
    main()
