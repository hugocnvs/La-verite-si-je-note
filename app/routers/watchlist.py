from __future__ import annotations

"""Routes dédiées à la watchlist."""

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, delete

from ..database import get_session
from ..dependencies import require_user
from ..models import Film, User, WatchlistItem
from ..services.watchlist import fetch_watchlist, fetch_watchlist_with_dates
from ..utils.flash import flash
from ..web import template_context, templates


router = APIRouter(tags=["watchlist"])


def _watchlist_cards_payload(watchlist_data: list, watchlist_ids: set[int]):
    """Build card data for watchlist view, including added_at date."""
    data = []
    for film, watchlist_item in watchlist_data:
        reviews = film.reviews or []
        review_count = len(reviews)
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else None
        data.append(
            {
                "film": film,
                "avg_rating": avg_rating,
                "review_count": review_count,
                "in_watchlist": film.id in watchlist_ids,
                "added_at": watchlist_item.created_at,
            }
        )
    return data


@router.get("/watchlist")
def watchlist_page(
    request: Request,
    sort: str = Query(default="date", regex="^(date|title|year|genre)$"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Affiche la watchlist complète de l'utilisateur."""
    watchlist_data = fetch_watchlist_with_dates(session, current_user, sort_by=sort)
    watchlist_films = [film for film, _ in watchlist_data]
    watchlist_ids = {film.id for film in watchlist_films}
    cards = _watchlist_cards_payload(watchlist_data, watchlist_ids)
    return templates.TemplateResponse(
        "films/watchlist.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=watchlist_films,
            watchlist_ids=watchlist_ids,
            films=cards,
            current_sort=sort,
        ),
    )


@router.post("/watchlist/{film_id}/remove")
def remove_from_watchlist(
    film_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
) -> RedirectResponse:
    """Retire un film de la watchlist (depuis la vue watchlist)."""
    film = session.get(Film, film_id)
    if not film:
        flash(request, "Film introuvable.", "error")
        return RedirectResponse(url="/watchlist", status_code=status.HTTP_303_SEE_OTHER)

    item = session.exec(
        select(WatchlistItem).where(
            (WatchlistItem.user_id == current_user.id) & (WatchlistItem.film_id == film_id)
        )
    ).first()

    if item:
        session.delete(item)
        session.commit()
        flash(request, f"{film.title} a été retiré de votre watchlist.", "info")
    
    return RedirectResponse(url="/watchlist", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/watchlist/clear")
def clear_watchlist(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
) -> RedirectResponse:
    """Vide entièrement la watchlist de l'utilisateur."""
    statement = delete(WatchlistItem).where(WatchlistItem.user_id == current_user.id)
    session.exec(statement)
    session.commit()
    
    flash(request, "Votre watchlist a été entièrement vidée.", "info")
    return RedirectResponse(url="/watchlist", status_code=status.HTTP_303_SEE_OTHER)

