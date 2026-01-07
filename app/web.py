"""Configuration partagée pour les templates Jinja2."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .models import User
from .utils.flash import pop_flashed_messages


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.globals["settings"] = get_settings()


def static_url(request: Request, path: str) -> str:
    """Construit l'URL des assets static.

    Quand l'app est accédée via `kubectl proxy`, le navigateur est sur une URL
    du type `/api/v1/.../proxy/` mais l'app, elle, ne voit que `/...`.
    Résultat: `url_for('static', ...)` génère `/static/...` (sans préfixe proxy)
    et le navigateur demande `http://127.0.0.1:8001/static/...` -> 404.

    On corrige en préfixant avec `KUBE_PROXY_BASE_PATH` quand on détecte le
    cas `kubectl proxy`.
    """

    clean_path = path.lstrip("/")
    proxy_base = os.getenv("KUBE_PROXY_BASE_PATH")

    if proxy_base:
        return f"{proxy_base.rstrip('/')}/static/{clean_path}"

    return str(request.url_for("static", path=clean_path))


templates.env.globals["static_url"] = static_url


def template_context(
    request: Request,
    *,
    current_user: Optional[User] = None,
    watchlist: Optional[list] = None,
    watchlist_ids: Optional[set[int]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Aide pour éviter de répéter les mêmes clés dans chaque rendu."""
    watchlist_list = watchlist or []
    context = {
        "request": request,
        "current_user": current_user,
        "watchlist": watchlist_list,
        "watchlist_ids": watchlist_ids or {getattr(film, "id", None) for film in watchlist_list if getattr(film, "id", None)},
        "messages": pop_flashed_messages(request),
    }
    context.update(extra)
    return context

