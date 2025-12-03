"""Service pour interagir avec l'API TMDb."""

from __future__ import annotations

import os
from typing import List, Optional

import requests

from ..config import get_settings


TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "11c76c77d46467911ba085973c464050")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


settings = get_settings()


def search_movies(query: str, page: int = 1) -> dict:
    """Recherche des films par titre sur TMDb."""
    resp = requests.get(
        f"{BASE_URL}/search/movie",
        params={
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "fr-FR",
            "page": page,
        },
        timeout=settings.api_timeout_seconds,
    )
    resp.raise_for_status()
    return resp.json()


def get_movie_details(tmdb_id: int) -> dict:
    """Récupère les détails complets d'un film depuis TMDb."""
    resp = requests.get(
        f"{BASE_URL}/movie/{tmdb_id}",
        params={
            "api_key": TMDB_API_KEY,
            "language": "fr-FR",
            "append_to_response": "credits",
        },
        timeout=settings.api_timeout_seconds,
    )
    resp.raise_for_status()
    return resp.json()


def get_popular_movies(page: int = 1) -> dict:
    """Récupère les films populaires."""
    resp = requests.get(
        f"{BASE_URL}/movie/popular",
        params={
            "api_key": TMDB_API_KEY,
            "language": "fr-FR",
            "page": page,
        },
        timeout=settings.api_timeout_seconds,
    )
    resp.raise_for_status()
    return resp.json()


def format_movie_for_display(movie: dict) -> dict:
    """Formate un film TMDb pour l'affichage."""
    poster_path = movie.get("poster_path")
    release_date = movie.get("release_date", "")
    
    return {
        "tmdb_id": movie.get("id"),
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "poster_url": f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None,
        "release_year": int(release_date[:4]) if release_date and len(release_date) >= 4 else None,
        "vote_average": movie.get("vote_average"),
    }


def extract_film_data(details: dict) -> dict:
    """Extrait les données d'un film depuis les détails TMDb."""
    # Extraire le réalisateur
    director = None
    credits = details.get("credits", {})
    for crew_member in credits.get("crew", []):
        if crew_member.get("job") == "Director":
            director = crew_member.get("name")
            break
    
    # Extraire l'année
    release_date = details.get("release_date", "")
    release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    
    # Poster URL
    poster_path = details.get("poster_path")
    poster_url = f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None
    
    # Pays
    countries = details.get("production_countries", [])
    country = countries[0]["name"] if countries else None
    
    # Genres
    genres = [g["name"] for g in details.get("genres", [])]
    
    return {
        "title": details.get("title"),
        "overview": details.get("overview"),
        "release_year": release_year,
        "poster_url": poster_url,
        "director": director,
        "country": country,
        "runtime_minutes": details.get("runtime"),
        "genres": genres,
    }
