from __future__ import annotations

"""Routes dédiées à la watchlist."""

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from ..database import get_session
from ..dependencies import require_user
from ..models import User
from ..services.watchlist import fetch_watchlist
from ..web import template_context, templates
from .films import _cards_payload


router = APIRouter(tags=["watchlist"])


@router.get("/watchlist")
def watchlist_page(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Affiche la watchlist complète de l'utilisateur."""
    watchlist_films = fetch_watchlist(session, current_user)
    watchlist_ids = {film.id for film in watchlist_films}
    cards = _cards_payload(watchlist_films, watchlist_ids)
    return templates.TemplateResponse(
        "films/watchlist.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=watchlist_films,
            watchlist_ids=watchlist_ids,
            films=cards,
        ),
    )

