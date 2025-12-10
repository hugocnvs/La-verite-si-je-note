"""Services liés à la watchlist utilisateur."""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..models import Film, Tag, User, WatchlistItem


def fetch_watchlist(session: Session, user: Optional[User]) -> List[Film]:
    """Retourne la liste des films ajoutés par l'utilisateur."""
    if not user:
        return []
    stmt = (
        select(Film)
        .join(WatchlistItem)
        .where(WatchlistItem.user_id == user.id)
        .options(selectinload(Film.tags))
        .order_by(WatchlistItem.created_at.desc())
    )
    return session.exec(stmt).all()


def fetch_watchlist_with_dates(
    session: Session, user: Optional[User], sort_by: str = "date"
) -> List[Tuple[Film, WatchlistItem]]:
    """Retourne les films de la watchlist avec leurs métadonnées (date d'ajout, etc.)."""
    if not user:
        return []
    stmt = (
        select(WatchlistItem, Film)
        .join(Film)
        .where(WatchlistItem.user_id == user.id)
        .options(selectinload(Film.tags), selectinload(Film.reviews))
    )
    
    # Apply sorting
    if sort_by == "title":
        stmt = stmt.order_by(Film.title.asc())
    elif sort_by == "year":
        stmt = stmt.order_by(Film.release_year.desc().nullslast())
    elif sort_by == "genre":
        # Sort by first tag name alphabetically
        stmt = stmt.outerjoin(Tag, Film.tags).order_by(Tag.name.asc().nullslast(), Film.title.asc())
    else:  # default: date (most recent first)
        stmt = stmt.order_by(WatchlistItem.created_at.desc())
    
    results = session.exec(stmt).all()
    # Return as list of (film, watchlist_item) tuples
    return [(film, item) for item, film in results]

