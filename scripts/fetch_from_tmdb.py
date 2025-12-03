"""Script d'import de films depuis TMDb (The Movie Database)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List

import requests
from sqlmodel import Session, select

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.database import engine, init_db
from app.models import Film, Tag


# Clé API TMDb (à définir en variable d'environnement ou directement ici)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def ensure_tags(session: Session, tag_names: Iterable[str]) -> List[Tag]:
    """Crée ou récupère les tags nécessaires."""
    tags: List[Tag] = []
    for name in {t.strip() for t in tag_names if t}:
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def get_genres_map(api_key: str) -> dict:
    """Récupère la correspondance ID -> nom de genre."""
    resp = requests.get(
        f"{BASE_URL}/genre/movie/list",
        params={"api_key": api_key, "language": "fr-FR"},
        timeout=10
    )
    resp.raise_for_status()
    return {g["id"]: g["name"] for g in resp.json().get("genres", [])}


def search_movie(api_key: str, query: str) -> list:
    """Recherche des films par titre."""
    resp = requests.get(
        f"{BASE_URL}/search/movie",
        params={"api_key": api_key, "query": query, "language": "fr-FR"},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_movie_details(api_key: str, movie_id: int) -> dict:
    """Récupère les détails complets d'un film."""
    resp = requests.get(
        f"{BASE_URL}/movie/{movie_id}",
        params={"api_key": api_key, "language": "fr-FR", "append_to_response": "credits"},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()


def get_popular_movies(api_key: str, pages: int = 1) -> list:
    """Récupère les films populaires."""
    movies = []
    for page in range(1, pages + 1):
        resp = requests.get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": api_key, "language": "fr-FR", "page": page},
            timeout=10
        )
        resp.raise_for_status()
        movies.extend(resp.json().get("results", []))
    return movies


def get_top_rated_movies(api_key: str, pages: int = 1) -> list:
    """Récupère les films les mieux notés."""
    movies = []
    for page in range(1, pages + 1):
        resp = requests.get(
            f"{BASE_URL}/movie/top_rated",
            params={"api_key": api_key, "language": "fr-FR", "page": page},
            timeout=10
        )
        resp.raise_for_status()
        movies.extend(resp.json().get("results", []))
    return movies


def import_movie(session: Session, movie_data: dict, genres_map: dict, api_key: str) -> bool:
    """Importe un film dans la base de données."""
    title = movie_data.get("title")
    if not title:
        return False
    
    # Vérifier si le film existe déjà
    exists = session.exec(select(Film).where(Film.title == title)).first()
    if exists:
        return False
    
    # Récupérer les détails complets
    details = get_movie_details(api_key, movie_data["id"])
    
    # Extraire les genres
    genre_names = [g["name"] for g in details.get("genres", [])]
    tags = ensure_tags(session, genre_names)
    
    # Extraire le réalisateur depuis les crédits
    director = None
    credits = details.get("credits", {})
    for crew_member in credits.get("crew", []):
        if crew_member.get("job") == "Director":
            director = crew_member.get("name")
            break
    
    # Extraire l'année de sortie
    release_date = details.get("release_date", "")
    release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    
    # Construire l'URL du poster
    poster_path = details.get("poster_path")
    poster_url = f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None
    
    # Extraire le pays de production
    countries = details.get("production_countries", [])
    country = countries[0]["name"] if countries else None
    
    film = Film(
        title=title,
        overview=details.get("overview"),
        release_year=release_year,
        poster_url=poster_url,
        director=director,
        country=country,
        runtime_minutes=details.get("runtime"),
    )
    film.tags = tags
    session.add(film)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Import de films depuis TMDb.")
    parser.add_argument("--api-key", type=str, default=TMDB_API_KEY, help="Clé API TMDb")
    parser.add_argument("--search", type=str, help="Rechercher et importer un film par titre")
    parser.add_argument("--popular", type=int, metavar="PAGES", help="Importer les films populaires (nombre de pages, 20 films/page)")
    parser.add_argument("--top-rated", type=int, metavar="PAGES", help="Importer les films les mieux notés (nombre de pages)")
    args = parser.parse_args()
    
    api_key = args.api_key
    if not api_key:
        print("❌ Clé API TMDb requise!")
        print("   Définissez TMDB_API_KEY ou utilisez --api-key")
        print("   Obtenez une clé gratuite sur: https://www.themoviedb.org/settings/api")
        sys.exit(1)
    
    init_db()
    genres_map = get_genres_map(api_key)
    inserted = 0
    skipped = 0
    
    with Session(engine) as session:
        movies_to_import = []
        
        if args.search:
            print(f"🔍 Recherche de: {args.search}")
            results = search_movie(api_key, args.search)
            if not results:
                print("   Aucun film trouvé.")
                return
            print(f"   {len(results)} résultat(s) trouvé(s)")
            movies_to_import = results
        
        elif args.popular:
            print(f"📥 Récupération des films populaires ({args.popular} page(s))...")
            movies_to_import = get_popular_movies(api_key, args.popular)
        
        elif args.top_rated:
            print(f"📥 Récupération des films les mieux notés ({args.top_rated} page(s))...")
            movies_to_import = get_top_rated_movies(api_key, args.top_rated)
        
        else:
            # Par défaut: 1 page de films populaires
            print("📥 Récupération des films populaires (1 page)...")
            movies_to_import = get_popular_movies(api_key, 1)
        
        for movie_data in movies_to_import:
            title = movie_data.get("title", "?")
            try:
                if import_movie(session, movie_data, genres_map, api_key):
                    print(f"   ✅ {title}")
                    inserted += 1
                else:
                    print(f"   ⏭️  {title} (déjà présent)")
                    skipped += 1
            except Exception as e:
                print(f"   ❌ {title}: {e}")
        
        session.commit()
    
    print(f"\n{'='*40}")
    print(f"✅ {inserted} films importés")
    print(f"⏭️  {skipped} films ignorés")


if __name__ == "__main__":
    main()
