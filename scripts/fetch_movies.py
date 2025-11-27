"""Script d'insertion automatique de films depuis l'API SampleAPIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

import requests
from sqlmodel import Session, select

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.config import get_settings
from app.database import engine, init_db
from app.models import Film, Tag


SOURCES = {
    "Action": "https://api.sampleapis.com/movies/action-adventure",
    "Comédie": "https://api.sampleapis.com/movies/comedy",
    "Drame": "https://api.sampleapis.com/movies/drama",
    "Fantasy": "https://api.sampleapis.com/movies/fantasy",
}

settings = get_settings()


def ensure_tags(session: Session, tag_names: Iterable[str]) -> List[Tag]:
    tags: List[Tag] = []
    for name in {t.strip() for t in tag_names if t}:
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def import_movies(limit: int) -> int:
    init_db()
    inserted = 0
    with Session(engine) as session:
        for label, url in SOURCES.items():
            try:
                resp = requests.get(url, timeout=settings.api_timeout_seconds)
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"Impossible de récupérer {url}: {exc}")
                continue
            payload = resp.json()
            if isinstance(payload, list):
                data = payload[:limit]
            elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
                data = payload["results"][:limit]
            else:
                print(f"Réponse inattendue pour {url}: {type(payload)!r}")
                continue

            for film_data in data:
                title = film_data.get("title")
                if not title:
                    continue
                exists = session.exec(select(Film).where(Film.title == title)).first()
                if exists:
                    continue
                tag_names = film_data.get("genres", []) or []
                tag_names.append(label)
                tags = ensure_tags(session, tag_names)
                director_field = film_data.get("director")
                if isinstance(director_field, list):
                    director = ", ".join(director_field)
                else:
                    director = director_field
                runtime = film_data.get("runtime")
                if isinstance(runtime, str):
                    digits = "".join(ch for ch in runtime if ch.isdigit())
                    runtime_minutes = int(digits) if digits else None
                elif isinstance(runtime, (int, float)):
                    runtime_minutes = int(runtime)
                else:
                    runtime_minutes = None

                film = Film(
                    title=title,
                    overview=film_data.get("description"),
                    release_year=film_data.get("year"),
                    poster_url=film_data.get("posterURL"),
                    director=director,
                    country=film_data.get("country"),
                    runtime_minutes=runtime_minutes,
                )
                film.tags = tags
                session.add(film)
                inserted += 1
        session.commit()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Import automatique de films.")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de films par catégorie (défaut: 10)")
    args = parser.parse_args()
    count = import_movies(limit=args.limit)
    print(f"{count} films importés avec succès.")


if __name__ == "__main__":
    main()

