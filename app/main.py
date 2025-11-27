"""Point d'entrée FastAPI."""

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .database import engine, init_db
from .models import User
from .routers import auth, films, watchlist
from .services.watchlist import fetch_watchlist
from .web import template_context, templates


settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie,
    max_age=60 * 60 * 24 * 30,  # 30 jours
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(films.router)
app.include_router(watchlist.router)


def _error_context(request: Request) -> Dict[str, Any]:
    user = None
    watchlist = []
    watchlist_ids = set()
    user_id = request.session.get("user_id")
    if user_id:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                watchlist = fetch_watchlist(session, user)
                watchlist_ids = {film.id for film in watchlist}
    return template_context(
        request, current_user=user, watchlist=watchlist, watchlist_ids=watchlist_ids
    )


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    context = _error_context(request)
    context.update(
        {
            "error_code": 404,
            "error_title": "Perdu dans le générique ?",
            "error_message": "On dirait que cette scène n'a jamais été tournée. Revenons au plateau principal.",
        }
    )
    return templates.TemplateResponse("errors/404.html", context, status_code=404)


@app.exception_handler(403)
async def forbidden(request: Request, exc: Exception):
    context = _error_context(request)
    context.update(
        {
            "error_code": 403,
            "error_title": "Accès interdit",
            "error_message": "Même Rabbi Jacob ne passerait pas ce cordon de sécurité. Reprenez un ticket valide.",
        }
    )
    return templates.TemplateResponse("errors/403.html", context, status_code=403)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/films")


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}

