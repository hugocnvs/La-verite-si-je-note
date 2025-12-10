from __future__ import annotations

"""Routes liées aux films et aux notations."""

from datetime import datetime
from typing import List, Optional, Sequence

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..database import get_session
from ..dependencies import get_current_user, require_user
from ..models import Film, Review, Tag, User, WatchlistItem
from ..services.watchlist import fetch_watchlist
from ..utils.flash import flash
from ..web import template_context, templates


router = APIRouter(prefix="/films", tags=["films"])


def _apply_filters(statement, q: Optional[str], tags: List[str]):
    if q:
        like = f"%{q.lower()}%"
        statement = statement.where(
            (Film.title.ilike(like)) | (Film.overview.ilike(like))
        )
    if tags:
        statement = statement.join(Film.tags).where(Tag.name.in_(tags)).group_by(Film.id)
    return statement


def _cards_payload(films: Sequence[Film], watchlist_ids: Optional[set[int]] = None):
    watchlist_ids = watchlist_ids or set()
    data = []
    for film in films:
        reviews = film.reviews or []
        review_count = len(reviews)
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else None
        data.append(
            {
                "film": film,
                "avg_rating": avg_rating,
                "review_count": review_count,
                "in_watchlist": film.id in watchlist_ids,
            }
        )
    return data


def _film_query(session: Session, q: Optional[str], tags: List[str]):
    stmt = (
        select(Film)
        .options(selectinload(Film.tags), selectinload(Film.reviews))
        .order_by(Film.title)
    )
    stmt = _apply_filters(stmt, q, tags)
    return session.exec(stmt).all()


@router.get("")
def list_films(
    request: Request,
    q: str | None = None,
    tags: List[str] = Query(default_factory=list),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user),
):
    """Page d'index : liste des films avec filtres."""
    films = _film_query(session, q, tags)
    watchlist_films = fetch_watchlist(session, current_user)
    watchlist_ids = {film.id for film in watchlist_films}
    data = _cards_payload(films, watchlist_ids)
    all_tags = session.exec(select(Tag).order_by(Tag.name)).all()

    return templates.TemplateResponse(
        "films/index.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=watchlist_films,
            watchlist_ids=watchlist_ids,
            films=data,
            selected_query=q or "",
            selected_tags=tags,
            tags=all_tags,
        ),
    )


@router.get("/partial")
def list_films_partial(
    request: Request,
    q: str | None = None,
    tags: List[str] = Query(default_factory=list),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user),
):
    """Rendu partiel utilisé pour la recherche dynamique."""
    films = _film_query(session, q, tags)
    watchlist_films = fetch_watchlist(session, current_user)
    watchlist_ids = {film.id for film in watchlist_films}
    data = _cards_payload(films, watchlist_ids)
    return templates.TemplateResponse(
        "films/_cards.html",
        {"request": request, "films": data, "watchlist_ids": watchlist_ids},
    )


@router.get("/{film_id}")
def film_detail(
    film_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user),
):
    """Page de détail d'un film."""
    stmt = (
        select(Film)
        .where(Film.id == film_id)
        .options(
            selectinload(Film.tags),
            selectinload(Film.reviews).selectinload(Review.user),
        )
    )
    film = session.exec(stmt).first()
    if not film:
        raise HTTPException(status_code=404, detail="Film introuvable.")

    reviews = film.reviews or []
    review_count = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else None
    user_review = None
    film_in_watchlist = None
    watchlist_films = []
    if current_user:
        user_review = next((r for r in reviews if r.user_id == current_user.id), None)
        watchlist_films = fetch_watchlist(session, current_user)
        film_in_watchlist = any(f.id == film.id for f in watchlist_films)

    return templates.TemplateResponse(
        "films/detail.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=watchlist_films,
            watchlist_ids={f.id for f in watchlist_films},
            film=film,
            reviews=sorted(reviews, key=lambda r: r.created_at, reverse=True),
            avg_rating=avg_rating,
            review_count=review_count,
            user_review=user_review,
            film_in_watchlist=film_in_watchlist,
        ),
    )


@router.post("/{film_id}/reviews")
def submit_review(
    film_id: int,
    request: Request,
    rating: int = Form(..., ge=1, le=5),
    comment: str = Form(""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
) -> RedirectResponse:
    """Crée ou met à jour l'avis de l'utilisateur."""
    film = session.get(Film, film_id)
    if not film:
        raise HTTPException(status_code=404, detail="Film introuvable.")

    review = session.exec(
        select(Review).where(
            (Review.user_id == current_user.id) & (Review.film_id == film_id)
        )
    ).first()

    if review:
        review.rating = rating
        review.comment = comment.strip() or None
        review.updated_at = datetime.utcnow()
        flash(request, "Votre avis a été mis à jour.", "success")
    else:
        review = Review(
            rating=rating,
            comment=comment.strip() or None,
            user_id=current_user.id,
            film_id=film_id,
        )
        session.add(review)
        flash(request, "Merci pour votre avis !", "success")

    # Auto-remove from watchlist if present
    watchlist_item = session.exec(
        select(WatchlistItem).where(
            (WatchlistItem.user_id == current_user.id) & (WatchlistItem.film_id == film_id)
        )
    ).first()
    if watchlist_item:
        session.delete(watchlist_item)
        flash(request, f"{film.title} a été retiré de votre watchlist.", "info")

    session.commit()
    return RedirectResponse(
        url=f"/films/{film_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/{film_id}/watchlist")
def toggle_watchlist(
    film_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
) -> RedirectResponse:
    """Ajoute ou retire un film de la watchlist."""
    film = session.get(Film, film_id)
    if not film:
        raise HTTPException(status_code=404, detail="Film introuvable.")

    item = session.exec(
        select(WatchlistItem).where(
            (WatchlistItem.user_id == current_user.id) & (WatchlistItem.film_id == film_id)
        )
    ).first()

    if item:
        session.delete(item)
        flash(request, f"{film.title} a été retiré de votre watchlist.", "info")
    else:
        item = WatchlistItem(user_id=current_user.id, film_id=film_id)
        session.add(item)
        flash(request, f"{film.title} a été ajouté à votre watchlist.", "success")

    session.commit()
    return RedirectResponse(url=f"/films/{film_id}", status_code=status.HTTP_303_SEE_OTHER)

