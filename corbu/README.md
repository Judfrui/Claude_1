# Corbu

Logiciel libre de pièces écrites et d'analyse d'offres pour bureaux
d'architectes et bureaux d'études en Belgique. Son nom rend hommage à
Le Corbusier.

Corbu s'inspire des logiciels de rédaction de CCTP/DPGF du marché, mais il est
pensé pour la pratique belge et il change l'analyse des offres sur un point
précis : **toutes les offres, y compris celles qui couvrent plusieurs lots,
s'importent en une seule fois.**

## Fonctionnalités

- **Bibliothèque** de lots et d'articles (description technique, unité, mode
  de métré, prix de référence). Une bibliothèque de départ structurée par corps
  de métier est fournie. Elle s'exporte et s'importe en JSON, pour être
  partagée entre bureaux.
- **Projets** : on ajoute des articles de la bibliothèque, ou des postes libres.
  Chaque poste copié reste indépendant de la bibliothèque.
- **Métré détaillé** par poste, avec formules en notation de chantier
  (`12,40 x 2,80 - 2 x 1,20 x 2,10`). Les déductions s'écrivent en négatif.
- **Modes de métré belges** : QF (quantité forfaitaire), QP (quantité
  présumée), FF (forfait), PM (pour mémoire).
- **Exports** :
  - le cahier spécial des charges, clauses techniques (Word `.docx`) ;
  - le métré récapitulatif vierge à remettre aux soumissionnaires (Excel
    `.xlsx`), en un seul classeur : un onglet par lot, un récapitulatif et
    la TVA ;
  - l'estimation chiffrée (même classeur, avec les prix estimés).
- **Analyse des offres** :
  - import groupé : on sélectionne d'un coup tous les fichiers reçus ;
  - chaque fichier peut couvrir un ou plusieurs lots. Les prix sont rattachés
    aux postes par leur code, quel que soit l'onglet. Corbu lit aussi les
    tableaux personnels des entrepreneurs, tant qu'ils ont une colonne
    « Code » (ou « N° ») et une colonne « Prix unitaire » (ou « P.U. ») ;
  - le soumissionnaire est lu dans la cellule « Soumissionnaire », à défaut
    dans le nom du fichier. Une nouvelle remise de la même entreprise
    remplace l'ancienne ;
  - les montants sont recalculés sur les quantités du métré (montant corrigé)
    et comparés au montant déclaré ;
  - alertes : prix manquant, erreur de calcul, quantité modifiée, prix
    anormalement haut ou bas. Le seuil est réglable. La référence est la
    médiane des offres à partir de trois offres, sinon l'estimation ;
  - classement par lot, moins-disant par poste, attribution lot par lot, et
    comparaison des offres complètes ;
  - rapport d'analyse exportable (Excel).

Corbu n'a pas de protection matérielle (clé USB) ni de licence à activer.

## Installation

Il faut Python 3.10 ou plus récent.

```bash
cd corbu
python -m venv .venv
.venv/bin/pip install -e .          # Windows : .venv\Scripts\pip install -e .
.venv/bin/corbu                     # puis ouvrir http://127.0.0.1:8000
```

Pour le travail en réseau au bureau, un poste sert de serveur et les autres
utilisent leur navigateur :

```bash
corbu --hote 0.0.0.0 --port 8000 --db D:/Corbu/corbu.db
```

Les collègues ouvrent `http://<nom-du-poste>:8000`. Corbu n'a pas encore
d'authentification : il ne faut l'exposer que sur le réseau interne.

## Tests

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## Structure

```
corbu/
├── corbu/
│   ├── app.py          # routes web (FastAPI)
│   ├── db.py           # schéma SQLite, bibliothèque, calculs de montants
│   ├── formules.py     # évaluation sûre des formules de métré
│   ├── offres.py       # import des offres et analyse comparative
│   ├── exports.py      # CSC .docx, métré et rapport .xlsx
│   ├── data/           # bibliothèque de départ
│   ├── templates/      # pages HTML (Jinja2)
│   └── static/
└── tests/
```

## Licence

MIT. Voir [LICENSE](LICENSE).
