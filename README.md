# 🎬 La Vérité Si Je Note

![Header](img/header.jpg)

Plateforme FastAPI complète pour explorer des films, filtrer par tags, laisser des commentaires notés sur 5 et gérer l'authentification. L'interface propose un thème néon apaisant, responsive et dynamique.

## Fonctionnalités

- **Authentification sécurisée** : inscription, connexion, déconnexion via sessions signées.
- **Grille interactive** : recherche plein texte + filtres multi-tags et rendu en cartes animées.
- **Page de détail** : fiche film, moyenne des notes, commentaires triés, formulaire d'avis.
- **Avis éditables** : chaque utilisateur connecté peut créer ou modifier son retour (note sur 5 + texte).
- **Visiteurs** : consultation libre des films/avis sans possibilité de poster.
- **Import auto** : script `scripts/fetch_movies.py` pour remplir la base depuis SampleAPIs.

## Stack

- **Backend** : FastAPI, SQLModel, SQLite
- **Frontend** : Jinja2, CSS custom, JS léger
- **Sécurité** : passlib[bcrypt], SessionMiddleware
- **Outillage** : pydantic-settings, requests, uvicorn

## Arborescence

```
app/
 ├─ main.py              # FastAPI + middleware + routage
 ├─ models.py            # User, Film, Tag, Review
 ├─ routers/             # auth.py, films.py
 ├─ templates/           # base + pages auth & films
 ├─ static/              # styles & scripts
 └─ utils/               # flash messages, sécurité...
scripts/
 └─ fetch_movies.py      # Import automatique de films
data/                    # Base SQLite (créée au démarrage)
```

## Installation & lancement

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optionnel : importer des films (15 par catégorie)
python scripts/fetch_movies.py --limit 15

# Lancer le serveur
uvicorn app.main:app --reload
```

Ensuite, rendez-vous sur `http://127.0.0.1:8000/` (redirection vers `/films`).

## Variables d'environnement optionnelles

Déposez un fichier `.env` à la racine pour surcharger les valeurs par défaut :

```
SECRET_KEY="change-me"
DATABASE_URL="sqlite:///./data/app.db"
SESSION_COOKIE="lvn_session"
API_TIMEOUT_SECONDS=10
```

## Vérifications manuelles suggérées

- créer un compte puis se connecter/déconnecter ;
- tester la recherche + sélection de plusieurs tags ;
- ajouter un avis, puis le modifier (le formulaire se pré-remplit) ;
- consulter la fiche en navigation privée : le formulaire d'avis disparaît.

## Pistes d'évolution

- Dockeriser API + job d'import + base
- Ajouter pagination et tri avancé
- Support OAuth (Google/GitHub)
- Historiser les révisions de commentaires
