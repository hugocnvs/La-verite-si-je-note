"""Configuration partagée pour les templates Jinja2."""

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .models import User
from .utils.flash import pop_flashed_messages


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.globals["settings"] = get_settings()


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

