"""Dépendances FastAPI partagées."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from .database import get_session
from .models import User


def get_current_user(
    request: Request, session: Session = Depends(get_session)
) -> Optional[User]:
    """Retourne l'utilisateur courant si connecté."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return session.get(User, user_id)


def require_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Force la présence d'un utilisateur connecté."""
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")
    return current_user

