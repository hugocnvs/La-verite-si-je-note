"""Routes pour le profil utilisateur."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..database import get_session
from ..dependencies import require_user
from ..models import Film, Review, Tag, User
from ..services.watchlist import fetch_watchlist
from ..web import template_context, templates


router = APIRouter(prefix="/profil", tags=["profil"])


def get_user_stats(session: Session, user: User) -> dict:
    """Calcule les statistiques de l'utilisateur."""
    # Récupérer tous les avis avec les films
    stmt = (
        select(Review)
        .where(Review.user_id == user.id)
        .options(selectinload(Review.film).selectinload(Film.tags))
    )
    reviews = session.exec(stmt).all()
    
    if not reviews:
        return {
            "total_films": 0,
            "total_minutes": 0,
            "total_hours": 0,
            "avg_rating": None,
            "favorite_genre": None,
            "genre_counts": [],
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }
    
    # Nombre de films vus
    total_films = len(reviews)
    
    # Minutes totales
    total_minutes = sum(r.film.runtime_minutes or 0 for r in reviews)
    total_hours = round(total_minutes / 60, 1)
    
    # Note moyenne donnée
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
    
    # Distribution des notes
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        rating_distribution[r.rating] += 1
    
    # Genre préféré (basé sur les films notés 4-5)
    genre_counter = Counter()
    for review in reviews:
        if review.film and review.film.tags:
            for tag in review.film.tags:
                genre_counter[tag.name] += 1
    
    genre_counts = genre_counter.most_common(5)
    favorite_genre = genre_counts[0][0] if genre_counts else None
    
    return {
        "total_films": total_films,
        "total_minutes": total_minutes,
        "total_hours": total_hours,
        "avg_rating": avg_rating,
        "favorite_genre": favorite_genre,
        "genre_counts": genre_counts,
        "rating_distribution": rating_distribution,
    }


def get_user_reviews(
    session: Session, 
    user: User, 
    search: Optional[str] = None,
    sort: str = "recent"
) -> list:
    """Récupère les avis de l'utilisateur avec recherche optionnelle."""
    stmt = (
        select(Review)
        .where(Review.user_id == user.id)
        .options(selectinload(Review.film).selectinload(Film.tags))
    )
    
    reviews = session.exec(stmt).all()
    
    # Filtrer par recherche
    if search:
        search_lower = search.lower()
        reviews = [
            r for r in reviews 
            if r.film and search_lower in r.film.title.lower()
        ]
    
    # Trier
    if sort == "rating_high":
        reviews = sorted(reviews, key=lambda r: r.rating, reverse=True)
    elif sort == "rating_low":
        reviews = sorted(reviews, key=lambda r: r.rating)
    elif sort == "title":
        reviews = sorted(reviews, key=lambda r: r.film.title if r.film else "")
    else:  # recent
        reviews = sorted(reviews, key=lambda r: r.created_at, reverse=True)
    
    return reviews


@router.get("")
def profile_page(
    request: Request,
    q: Optional[str] = None,
    sort: str = Query(default="recent"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de profil de l'utilisateur."""
    # Stats
    stats = get_user_stats(session, current_user)
    
    # Avis avec recherche et tri
    reviews = get_user_reviews(session, current_user, search=q, sort=sort)
    
    # Films les mieux notés (5 étoiles)
    top_rated = [r for r in reviews if r.rating == 5][:6]
    
    # Films les moins bien notés (1-2 étoiles)
    lowest_rated = [r for r in reviews if r.rating <= 2][:6]
    
    # Watchlist
    watchlist = fetch_watchlist(session, current_user)
    
    return templates.TemplateResponse(
        "profil/index.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=watchlist,
            watchlist_ids={f.id for f in watchlist},
            stats=stats,
            reviews=reviews,
            top_rated=top_rated,
            lowest_rated=lowest_rated,
            search_query=q or "",
            current_sort=sort,
        ),
    )
