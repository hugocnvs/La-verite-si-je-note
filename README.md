# La Vérité Si Je Note

![Header](img/header.jpg)

Plateforme FastAPI complète pour explorer des films, filtrer par tags, laisser des commentaires notés sur 5 et gérer une watchlist personnelle. L'interface propose un thème clair/sombre moderne, responsive et dynamique.

## Fonctionnalités

- **Authentification sécurisée** : inscription, connexion, déconnexion via sessions signées.
- **Grille interactive** : recherche plein texte + filtres multi-tags avec dropdown et rendu en cartes animées.
- **Page de détail** : fiche film, moyenne des notes, commentaires triés, formulaire d'avis.
- **Avis éditables** : chaque utilisateur connecté peut créer ou modifier son retour (note sur 5 + texte).
- **Watchlist** : liste de films à voir, ajout/suppression en un clic.
- **Profil utilisateur** : statistiques personnelles (films vus, temps de visionnage, note moyenne, genres préférés), coups de cœur, déceptions et historique complet.
- **Intégration TMDb** : recherche et import de films depuis The Movie Database.
- **Mode clair/sombre** : bascule entre thème jour et nuit, persisté en local.
- **Visiteurs** : consultation libre des films/avis sans possibilité de poster.
- **Import auto** : scripts pour remplir la base depuis SampleAPIs ou TMDb.

## Stack

- **Backend** : FastAPI, SQLModel, SQLite
- **Frontend** : Jinja2, CSS custom (variables CSS), JS vanilla
- **APIs externes** : TMDb (The Movie Database), SampleAPIs
- **Sécurité** : passlib[bcrypt], SessionMiddleware
- **Outillage** : pydantic-settings, requests, uvicorn

## Arborescence

```
app/
 ├─ main.py              # FastAPI + middleware + routage
 ├─ models.py            # User, Film, Tag, Review, WatchlistItem
 ├─ routers/             # auth, films, watchlist, tmdb, profil
 ├─ services/            # tmdb.py (intégration API)
 ├─ templates/           # base + pages (auth, films, watchlist, profil, tmdb)
 ├─ static/              # styles (mode clair/sombre) & scripts
 └─ utils/               # flash messages, sécurité...
scripts/
 ├─ fetch_movies.py      # Import depuis SampleAPIs (avec limite)
 ├─ fetch_all_movies.py  # Import complet (11 catégories)
 └─ fetch_from_tmdb.py   # Import depuis TMDb (CLI)
data/                    # Base SQLite (créée au démarrage)
```

## Installation & lancement

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optionnel : importer des films depuis SampleAPIs
python scripts/fetch_movies.py --limit 15      # 15 films par catégorie
python scripts/fetch_all_movies.py             # Tous les films disponibles

# Optionnel : importer depuis TMDb (nécessite une clé API)
export TMDB_API_KEY=votre_clé
python scripts/fetch_from_tmdb.py --popular --limit 20

# Lancer le serveur
uvicorn app.main:app --reload
```

Ensuite, rendez-vous sur `http://127.0.0.1:8000/` (redirection vers `/films`).

## Configuration TMDb

Pour utiliser l'import depuis TMDb, créez un fichier `.env` :

```
TMDB_API_KEY=votre_clé_api
```

Obtenez une clé gratuite sur [themoviedb.org](https://www.themoviedb.org/settings/api).
