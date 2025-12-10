"""Routes pour l'import de films depuis TMDb."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status, Header, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlmodel import Session, select

from ..database import get_session
from ..dependencies import require_user
from ..models import Film, Tag, User
from ..services.tmdb import (
    search_movies,
    get_movie_details,
    get_popular_movies,
    format_movie_for_display,
    extract_film_data,
)
from ..utils.flash import flash
from ..web import template_context, templates


router = APIRouter(prefix="/tmdb", tags=["tmdb"])


def _ensure_tags(session: Session, tag_names: list[str]) -> list[Tag]:
    """Crée ou récupère les tags nécessaires."""
    tags: list[Tag] = []
    for name in {t.strip() for t in tag_names if t}:
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


@router.get("/search")
def search_tmdb(
    request: Request,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de recherche de films sur TMDb."""
    results = []
    total_results = 0
    total_pages = 0
    
    if q:
        try:
            data = search_movies(q, page)
            results = [format_movie_for_display(m) for m in data.get("results", [])]
            total_results = data.get("total_results", 0)
            total_pages = min(data.get("total_pages", 0), 10)  # Limiter à 10 pages
            
            # Vérifier quels films sont déjà en base
            for movie in results:
                existing = session.exec(
                    select(Film).where(Film.title == movie["title"])
                ).first()
                movie["already_exists"] = existing is not None
                if existing:
                    movie["local_id"] = existing.id
        except Exception as e:
            flash(request, f"Erreur lors de la recherche: {e}", "error")
    
    return templates.TemplateResponse(
        "tmdb/search.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=[],
            query=q or "",
            results=results,
            total_results=total_results,
            current_page=page,
            total_pages=total_pages,
        ),
    )


@router.get("/popular")
def popular_tmdb(
    request: Request,
    page: int = Query(default=1, ge=1),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page des films populaires sur TMDb."""
    results = []
    total_pages = 0
    
    try:
        data = get_popular_movies(page)
        results = [format_movie_for_display(m) for m in data.get("results", [])]
        total_pages = min(data.get("total_pages", 0), 10)
        
        # Vérifier quels films sont déjà en base
        for movie in results:
            existing = session.exec(
                select(Film).where(Film.title == movie["title"])
            ).first()
            movie["already_exists"] = existing is not None
            if existing:
                movie["local_id"] = existing.id
    except Exception as e:
        flash(request, f"Erreur lors de la récupération: {e}", "error")
    
    return templates.TemplateResponse(
        "tmdb/search.html",
        template_context(
            request,
            current_user=current_user,
            watchlist=[],
            query="",
            results=results,
            total_results=len(results),
            current_page=page,
            total_pages=total_pages,
            is_popular=True,
        ),
    )


@router.post("/import/{tmdb_id}")
def import_from_tmdb(
    tmdb_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
    accept: str | None = Header(default=None),
) -> Response:
    """Importe un film depuis TMDb vers la base locale."""
    try:
        details = get_movie_details(tmdb_id)
        film_data = extract_film_data(details)
        
        # Vérifier si le film existe déjà
        existing = session.exec(
            select(Film).where(Film.title == film_data["title"])
        ).first()
        
        if existing:
            msg = f"« {film_data['title']} » existe déjà dans la base."
            if accept == "application/json":
                 return JSONResponse(
                     content={"success": True, "local_id": existing.id, "title": existing.title, "message": msg, "already_exists": True},
                     status_code=200
                 )
            
            flash(request, msg, "info")
            return RedirectResponse(
                url=f"/films/{existing.id}",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        
        # Créer les tags
        tags = _ensure_tags(session, film_data.pop("genres", []))
        
        # Créer le film
        film = Film(**film_data)
        film.tags = tags
        session.add(film)
        session.commit()
        session.refresh(film)
        
        flash(request, f"« {film.title} » a été ajouté avec succès !", "success")
        
        if accept == "application/json":
             return JSONResponse(
                 content={"success": True, "local_id": film.id, "title": film.title, "message": f"« {film.title} » ajouté !"},
                 status_code=200
             )

        return RedirectResponse(
            url=f"/films/{film.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    except Exception as e:
        if accept == "application/json":
             return JSONResponse(
                 content={"success": False, "message": str(e)},
                 status_code=400
             )
        flash(request, f"Erreur lors de l'import: {e}", "error")
        return RedirectResponse(
            url="/tmdb/search",
            status_code=status.HTTP_303_SEE_OTHER,
        )
