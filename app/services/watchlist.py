"""Services liés à la watchlist utilisateur."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..models import Film, User, WatchlistItem


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

